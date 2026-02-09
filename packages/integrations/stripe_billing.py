"""
Stripe Integration for DealFlow
================================
Generate payment links and invoices from SOWs.

Setup:
1. Create Stripe account: dashboard.stripe.com
2. Get API keys from Developers → API Keys
3. Set STRIPE_SECRET_KEY environment variable
"""

import os
from typing import Any

import stripe

# Initialize Stripe
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")


async def create_payment_link(
    sow: dict,
    client_email: str,
    client_name: str,
) -> dict:
    """
    Create a Stripe payment link for a SOW.
    
    For milestone-based payments, creates multiple links.
    
    Returns:
        {"payment_link": "https://...", "amount": 15000, ...}
    """
    
    pricing = sow.get("pricing", {})
    total = pricing.get("total", 0)
    title = sow.get("title", "Project")
    
    # Create a product for this SOW
    product = stripe.Product.create(
        name=f"SOW: {title}",
        description=sow.get("executive_summary", "")[:500],
        metadata={
            "sow_title": title,
            "client_email": client_email,
            "client_name": client_name,
        },
    )
    
    # Create price (in cents)
    price = stripe.Price.create(
        product=product.id,
        unit_amount=int(total * 100),
        currency="usd",
    )
    
    # Create payment link
    payment_link = stripe.PaymentLink.create(
        line_items=[{"price": price.id, "quantity": 1}],
        metadata={
            "sow_title": title,
            "client_email": client_email,
        },
        after_completion={
            "type": "redirect",
            "redirect": {"url": "https://prodway.ai/thank-you"},
        },
    )
    
    return {
        "payment_link": payment_link.url,
        "amount": total,
        "product_id": product.id,
        "price_id": price.id,
    }


async def create_invoice(
    sow: dict,
    client_email: str,
    client_name: str,
    due_days: int = 14,
) -> dict:
    """
    Create a Stripe invoice for a SOW.
    
    Returns:
        {"invoice_id": "in_xxx", "invoice_url": "https://...", ...}
    """
    
    pricing = sow.get("pricing", {})
    total = pricing.get("total", 0)
    title = sow.get("title", "Project")
    
    # Create or get customer
    customers = stripe.Customer.list(email=client_email, limit=1)
    if customers.data:
        customer = customers.data[0]
    else:
        customer = stripe.Customer.create(
            email=client_email,
            name=client_name,
            metadata={"source": "dealflow"},
        )
    
    # Create invoice
    invoice = stripe.Invoice.create(
        customer=customer.id,
        collection_method="send_invoice",
        days_until_due=due_days,
        metadata={
            "sow_title": title,
        },
    )
    
    # Add line item
    stripe.InvoiceItem.create(
        customer=customer.id,
        invoice=invoice.id,
        amount=int(total * 100),
        currency="usd",
        description=f"Statement of Work: {title}",
    )
    
    # Finalize and send
    invoice = stripe.Invoice.finalize_invoice(invoice.id)
    stripe.Invoice.send_invoice(invoice.id)
    
    return {
        "invoice_id": invoice.id,
        "invoice_url": invoice.hosted_invoice_url,
        "invoice_pdf": invoice.invoice_pdf,
        "amount": total,
        "status": invoice.status,
    }


async def create_milestone_invoices(
    sow: dict,
    client_email: str,
    client_name: str,
) -> list[dict]:
    """
    Create multiple invoices for milestone-based payments.
    
    Returns list of invoice details.
    """
    
    pricing = sow.get("pricing", {})
    payment_schedule = pricing.get("payment_schedule", [])
    title = sow.get("title", "Project")
    
    if not payment_schedule:
        # Fall back to single invoice
        return [await create_invoice(sow, client_email, client_name)]
    
    # Create or get customer
    customers = stripe.Customer.list(email=client_email, limit=1)
    if customers.data:
        customer = customers.data[0]
    else:
        customer = stripe.Customer.create(
            email=client_email,
            name=client_name,
            metadata={"source": "dealflow"},
        )
    
    invoices = []
    
    for i, milestone in enumerate(payment_schedule):
        amount = milestone.get("amount", 0)
        milestone_name = milestone.get("milestone", f"Milestone {i+1}")
        
        # Only create/send first invoice immediately
        # Others are created as drafts
        send_now = (i == 0) or milestone.get("due") == "Upon signing"
        
        invoice = stripe.Invoice.create(
            customer=customer.id,
            collection_method="send_invoice",
            days_until_due=14,
            metadata={
                "sow_title": title,
                "milestone": milestone_name,
                "milestone_index": str(i),
            },
        )
        
        stripe.InvoiceItem.create(
            customer=customer.id,
            invoice=invoice.id,
            amount=int(amount * 100),
            currency="usd",
            description=f"{title} - {milestone_name}",
        )
        
        if send_now:
            invoice = stripe.Invoice.finalize_invoice(invoice.id)
            stripe.Invoice.send_invoice(invoice.id)
            status = "sent"
        else:
            status = "draft"
        
        invoices.append({
            "invoice_id": invoice.id,
            "invoice_url": invoice.hosted_invoice_url if send_now else None,
            "amount": amount,
            "milestone": milestone_name,
            "status": status,
        })
    
    return invoices


# Quick functions for common operations

async def quick_payment_link(
    amount: int,
    description: str,
    client_email: str = None,
) -> str:
    """Create a quick payment link for a given amount."""
    
    product = stripe.Product.create(name=description)
    price = stripe.Price.create(
        product=product.id,
        unit_amount=amount * 100,
        currency="usd",
    )
    
    link = stripe.PaymentLink.create(
        line_items=[{"price": price.id, "quantity": 1}],
    )
    
    return link.url
