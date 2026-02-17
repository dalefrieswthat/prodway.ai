"""
Mercury Integration for SowFlow
================================
Generate invoices with ACH payment option via Mercury's API.

Benefits over Stripe for larger invoices:
- ACH payments have lower fees (~$5 flat vs 2.9% + $0.30)
- Direct bank-to-bank transfers
- Professional invoicing with your Mercury branding

Setup:
1. Mercury Plus or Pro plan required for API access
2. Generate API token: Mercury Dashboard -> Settings -> Developers -> API Tokens
3. Set MERCURY_API_TOKEN environment variable
4. Set MERCURY_ACCOUNT_ID (your Mercury account ID for receiving payments)

API Docs: https://docs.mercury.com/reference
"""

import os
import httpx
from typing import Optional
from datetime import datetime, timedelta

# Mercury API configuration
MERCURY_API_TOKEN = os.environ.get("MERCURY_API_TOKEN", "")
MERCURY_ACCOUNT_ID = os.environ.get("MERCURY_ACCOUNT_ID", "")
MERCURY_BASE_URL = "https://api.mercury.com/api/v1"


def _get_headers() -> dict:
    """Get authorization headers for Mercury API."""
    return {
        "Authorization": f"Bearer {MERCURY_API_TOKEN}",
        "Content-Type": "application/json",
    }


async def create_customer(
    email: str,
    name: str,
    address: Optional[dict] = None,
) -> dict:
    """
    Create or get a customer in Mercury.

    Args:
        email: Customer email
        name: Customer/company name
        address: Optional address dict with address1, city, region, postalCode, country

    Returns:
        {"customer_id": "...", "email": "...", "name": "..."}
    """
    async with httpx.AsyncClient() as client:
        # Check if customer exists
        response = await client.get(
            f"{MERCURY_BASE_URL}/invoicing/customers",
            headers=_get_headers(),
            params={"limit": 100},
        )
        response.raise_for_status()
        data = response.json()

        # Look for existing customer by email
        for customer in data.get("customers", []):
            if customer.get("email", "").lower() == email.lower():
                return {
                    "customer_id": customer["id"],
                    "email": customer["email"],
                    "name": customer["name"],
                    "existing": True,
                }

        # Create new customer
        payload = {
            "email": email,
            "name": name,
        }

        if address:
            payload["address"] = {
                "name": name,
                "address1": address.get("address1", ""),
                "city": address.get("city", ""),
                "region": address.get("region", ""),
                "postalCode": address.get("postalCode", ""),
                "country": address.get("country", "US"),
            }

        response = await client.post(
            f"{MERCURY_BASE_URL}/invoicing/customers",
            headers=_get_headers(),
            json=payload,
        )
        response.raise_for_status()
        customer = response.json()

        return {
            "customer_id": customer["id"],
            "email": customer["email"],
            "name": customer["name"],
            "existing": False,
        }


async def create_invoice(
    sow: dict,
    client_email: str,
    client_name: str,
    due_days: int = 14,
    send_email: bool = True,
    enable_ach: bool = True,
    enable_credit_card: bool = False,
) -> dict:
    """
    Create a Mercury invoice for a SOW with ACH payment option.

    Args:
        sow: SOW dict with pricing, title, etc.
        client_email: Client's email address
        client_name: Client/company name
        due_days: Days until invoice is due (default 14)
        send_email: Whether to send invoice email immediately
        enable_ach: Enable ACH debit payment (recommended for lower fees)
        enable_credit_card: Enable credit card payment (requires Stripe connected)

    Returns:
        {
            "invoice_id": "...",
            "invoice_url": "https://...",
            "amount": 15000,
            "status": "sent",
            "payment_methods": ["ach"]
        }
    """
    # Get or create customer
    customer = await create_customer(client_email, client_name)

    pricing = sow.get("pricing", {})
    total = pricing.get("total", 0)
    title = sow.get("title", "Project")
    summary = sow.get("executive_summary", "")

    # Calculate due date
    due_date = (datetime.now() + timedelta(days=due_days)).strftime("%Y-%m-%d")

    # Build line items
    line_items = []

    # Check if SOW has itemized deliverables
    deliverables = sow.get("deliverables", [])
    if deliverables and len(deliverables) > 1:
        # Itemized invoice
        for i, deliverable in enumerate(deliverables):
            # Estimate cost per deliverable (equal split if not specified)
            item_amount = deliverable.get("estimated_cost", total / len(deliverables))
            line_items.append({
                "description": deliverable.get("title", f"Deliverable {i+1}"),
                "quantity": 1,
                "unitPrice": item_amount,
            })
    else:
        # Single line item
        line_items.append({
            "description": f"Statement of Work: {title}",
            "quantity": 1,
            "unitPrice": total,
        })

    # Create invoice
    payload = {
        "customerId": customer["customer_id"],
        "destinationAccountId": MERCURY_ACCOUNT_ID,
        "dueDate": due_date,
        "lineItems": line_items,
        "achDebitEnabled": enable_ach,
        "creditCardEnabled": enable_credit_card,
        "sendEmail": "SendNow" if send_email else "DontSend",
    }

    # Add memo/note if we have a summary
    if summary:
        payload["note"] = summary[:500]  # Mercury has a limit

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{MERCURY_BASE_URL}/invoicing/invoices",
            headers=_get_headers(),
            json=payload,
        )
        response.raise_for_status()
        invoice = response.json()

        payment_methods = []
        if enable_ach:
            payment_methods.append("ach")
        if enable_credit_card:
            payment_methods.append("credit_card")

        return {
            "invoice_id": invoice["id"],
            "invoice_url": invoice.get("invoiceUrl", ""),
            "invoice_number": invoice.get("invoiceNumber", ""),
            "amount": total,
            "due_date": due_date,
            "status": "sent" if send_email else "draft",
            "payment_methods": payment_methods,
            "customer_id": customer["customer_id"],
        }


async def create_milestone_invoices(
    sow: dict,
    client_email: str,
    client_name: str,
    enable_ach: bool = True,
) -> list[dict]:
    """
    Create multiple invoices for milestone-based payments.

    First milestone invoice is sent immediately, others are created as drafts.

    Returns list of invoice details.
    """
    pricing = sow.get("pricing", {})
    payment_schedule = pricing.get("payment_schedule", [])
    title = sow.get("title", "Project")

    if not payment_schedule:
        # Fall back to single invoice
        return [await create_invoice(sow, client_email, client_name, enable_ach=enable_ach)]

    # Get or create customer
    customer = await create_customer(client_email, client_name)

    invoices = []

    for i, milestone in enumerate(payment_schedule):
        amount = milestone.get("amount", 0)
        milestone_name = milestone.get("milestone", f"Milestone {i+1}")

        # Only send first invoice immediately
        send_now = (i == 0) or milestone.get("due") == "Upon signing"

        due_date = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")

        payload = {
            "customerId": customer["customer_id"],
            "destinationAccountId": MERCURY_ACCOUNT_ID,
            "dueDate": due_date,
            "lineItems": [{
                "description": f"{title} - {milestone_name}",
                "quantity": 1,
                "unitPrice": amount,
            }],
            "achDebitEnabled": enable_ach,
            "creditCardEnabled": False,
            "sendEmail": "SendNow" if send_now else "DontSend",
            "internalNote": f"Milestone {i+1} of {len(payment_schedule)}",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{MERCURY_BASE_URL}/invoicing/invoices",
                headers=_get_headers(),
                json=payload,
            )
            response.raise_for_status()
            invoice = response.json()

            invoices.append({
                "invoice_id": invoice["id"],
                "invoice_url": invoice.get("invoiceUrl", "") if send_now else None,
                "invoice_number": invoice.get("invoiceNumber", ""),
                "amount": amount,
                "milestone": milestone_name,
                "status": "sent" if send_now else "draft",
            })

    return invoices


async def get_invoice(invoice_id: str) -> dict:
    """
    Get invoice details and payment status.

    Returns:
        {
            "invoice_id": "...",
            "status": "paid" | "sent" | "viewed" | "overdue" | "canceled",
            "amount": 15000,
            "paid_at": "2026-02-17T...",
            ...
        }
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{MERCURY_BASE_URL}/invoicing/invoices/{invoice_id}",
            headers=_get_headers(),
        )
        response.raise_for_status()
        invoice = response.json()

        return {
            "invoice_id": invoice["id"],
            "invoice_number": invoice.get("invoiceNumber", ""),
            "invoice_url": invoice.get("invoiceUrl", ""),
            "status": invoice.get("status", "unknown"),
            "amount": invoice.get("totalAmount", 0),
            "due_date": invoice.get("dueDate", ""),
            "paid_at": invoice.get("paidAt"),
            "customer_email": invoice.get("customerEmail", ""),
        }


async def send_invoice(invoice_id: str) -> dict:
    """
    Send a draft invoice to the customer.

    Returns updated invoice details.
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{MERCURY_BASE_URL}/invoicing/invoices/{invoice_id}/send",
            headers=_get_headers(),
        )
        response.raise_for_status()
        return await get_invoice(invoice_id)


async def cancel_invoice(invoice_id: str) -> dict:
    """
    Cancel an unpaid invoice.

    Returns:
        {"invoice_id": "...", "status": "canceled"}
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{MERCURY_BASE_URL}/invoicing/invoices/{invoice_id}/cancel",
            headers=_get_headers(),
        )
        response.raise_for_status()

        return {
            "invoice_id": invoice_id,
            "status": "canceled",
        }


async def list_invoices(
    status: Optional[str] = None,
    limit: int = 50,
) -> list[dict]:
    """
    List invoices with optional status filter.

    Args:
        status: Filter by status (paid, sent, viewed, overdue, canceled)
        limit: Max invoices to return

    Returns list of invoice summaries.
    """
    params = {"limit": limit}
    if status:
        params["status"] = status

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{MERCURY_BASE_URL}/invoicing/invoices",
            headers=_get_headers(),
            params=params,
        )
        response.raise_for_status()
        data = response.json()

        return [
            {
                "invoice_id": inv["id"],
                "invoice_number": inv.get("invoiceNumber", ""),
                "status": inv.get("status", "unknown"),
                "amount": inv.get("totalAmount", 0),
                "due_date": inv.get("dueDate", ""),
                "customer_email": inv.get("customerEmail", ""),
            }
            for inv in data.get("invoices", [])
        ]


# ============================================================================
# Quick functions for common operations
# ============================================================================

async def quick_ach_invoice(
    amount: float,
    description: str,
    client_email: str,
    client_name: str,
    due_days: int = 14,
) -> str:
    """
    Create a quick ACH invoice and return the payment URL.

    Args:
        amount: Invoice amount in dollars
        description: What the invoice is for
        client_email: Client's email
        client_name: Client's name
        due_days: Days until due

    Returns:
        Invoice URL (e.g., "https://mercury.com/pay/...")
    """
    customer = await create_customer(client_email, client_name)

    due_date = (datetime.now() + timedelta(days=due_days)).strftime("%Y-%m-%d")

    payload = {
        "customerId": customer["customer_id"],
        "destinationAccountId": MERCURY_ACCOUNT_ID,
        "dueDate": due_date,
        "lineItems": [{
            "description": description,
            "quantity": 1,
            "unitPrice": amount,
        }],
        "achDebitEnabled": True,
        "creditCardEnabled": False,
        "sendEmail": "SendNow",
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{MERCURY_BASE_URL}/invoicing/invoices",
            headers=_get_headers(),
            json=payload,
        )
        response.raise_for_status()
        invoice = response.json()

        return invoice.get("invoiceUrl", "")


def is_configured() -> bool:
    """Check if Mercury integration is configured."""
    return bool(MERCURY_API_TOKEN and MERCURY_ACCOUNT_ID)
