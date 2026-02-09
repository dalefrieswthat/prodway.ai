"""
DocuSign Integration for SowFlow
=================================
Send SOWs for e-signature via DocuSign API.

Setup:
1. Create DocuSign developer account: developers.docusign.com
2. Create an app with "Authorization Code Grant"
3. Get Integration Key, Secret Key, and configure redirect URI
4. Run OAuth flow to get access token
"""

import os
import base64
from datetime import datetime
from typing import Any

import httpx

# DocuSign API endpoints
DOCUSIGN_AUTH_SERVER = "account-d.docusign.com"  # Use account.docusign.com for production
DOCUSIGN_API_BASE = "https://demo.docusign.net/restapi"  # Use docusign.net for production


class DocuSignClient:
    """Client for DocuSign e-signature API."""

    def __init__(
        self,
        access_token: str | None = None,
        account_id: str | None = None,
    ):
        self.access_token = access_token or os.environ.get("DOCUSIGN_ACCESS_TOKEN")
        self.account_id = account_id or os.environ.get("DOCUSIGN_ACCOUNT_ID")
        self.base_url = f"{DOCUSIGN_API_BASE}/v2.1/accounts/{self.account_id}"

    @property
    def headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    async def create_envelope_from_sow(
        self,
        sow: dict,
        client_email: str,
        client_name: str,
        sender_email: str,
        sender_name: str,
    ) -> dict:
        """
        Create a DocuSign envelope from a SOW.

        Returns envelope ID and status.
        """

        # Generate SOW document content
        document_content = self._generate_sow_document(sow, client_name)
        document_base64 = base64.b64encode(document_content.encode()).decode()

        # Build envelope definition
        envelope_definition = {
            "emailSubject": f"Statement of Work: {sow.get('title', 'Project Proposal')}",
            "emailBlurb": f"Please review and sign the attached Statement of Work for {sow.get('title')}.",
            "status": "sent",  # "created" for draft, "sent" to send immediately
            "documents": [
                {
                    "documentId": "1",
                    "name": f"SOW - {sow.get('title', 'Project')}.html",
                    "fileExtension": "html",
                    "documentBase64": document_base64,
                }
            ],
            "recipients": {
                "signers": [
                    {
                        "email": client_email,
                        "name": client_name,
                        "recipientId": "1",
                        "routingOrder": "1",
                        "tabs": {
                            "signHereTabs": [
                                {
                                    "documentId": "1",
                                    "pageNumber": "1",
                                    "anchorString": "[CLIENT_SIGNATURE]",
                                    "anchorUnits": "pixels",
                                    "anchorXOffset": "0",
                                    "anchorYOffset": "0",
                                }
                            ],
                            "dateSignedTabs": [
                                {
                                    "documentId": "1",
                                    "pageNumber": "1",
                                    "anchorString": "[CLIENT_DATE]",
                                    "anchorUnits": "pixels",
                                    "anchorXOffset": "0",
                                    "anchorYOffset": "0",
                                }
                            ],
                        },
                    },
                    {
                        "email": sender_email,
                        "name": sender_name,
                        "recipientId": "2",
                        "routingOrder": "2",
                        "tabs": {
                            "signHereTabs": [
                                {
                                    "documentId": "1",
                                    "pageNumber": "1",
                                    "anchorString": "[PROVIDER_SIGNATURE]",
                                    "anchorUnits": "pixels",
                                    "anchorXOffset": "0",
                                    "anchorYOffset": "0",
                                }
                            ],
                        },
                    },
                ],
            },
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/envelopes",
                headers=self.headers,
                json=envelope_definition,
            )
            response.raise_for_status()
            return response.json()

    async def get_envelope_status(self, envelope_id: str) -> dict:
        """Get the status of an envelope."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/envelopes/{envelope_id}",
                headers=self.headers,
            )
            response.raise_for_status()
            return response.json()

    def _generate_sow_document(self, sow: dict, client_name: str) -> str:
        """Generate HTML document from SOW data."""

        pricing = sow.get("pricing", {})
        total = pricing.get("total", 0)

        # Build scope list
        scope_html = "\n".join(
            f"<li>{item}</li>" for item in sow.get("scope", [])
        )

        # Build deliverables list
        deliverables_html = "\n".join(
            f"<li>{item}</li>" for item in sow.get("deliverables", [])
        )

        # Build timeline
        timeline_html = "\n".join(
            f"<tr><td>{p.get('phase')}</td><td>{p.get('duration')}</td><td>{p.get('description', '')}</td></tr>"
            for p in sow.get("timeline", [])
        )

        # Build payment schedule
        payment_html = "\n".join(
            f"<tr><td>{p.get('milestone')}</td><td>${p.get('amount'):,.0f}</td><td>{p.get('due')}</td></tr>"
            for p in pricing.get("payment_schedule", [])
        )

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 40px auto; padding: 20px; }}
        h1 {{ color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px; }}
        h2 {{ color: #555; margin-top: 30px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 10px; text-align: left; }}
        th {{ background-color: #f5f5f5; }}
        .signature-block {{ margin-top: 50px; display: flex; justify-content: space-between; }}
        .signature-box {{ width: 45%; }}
        .signature-line {{ border-top: 1px solid #333; margin-top: 50px; padding-top: 5px; }}
        .total {{ font-size: 24px; font-weight: bold; color: #007bff; }}
    </style>
</head>
<body>
    <h1>Statement of Work</h1>
    <h2>{sow.get('title', 'Project Proposal')}</h2>

    <p><strong>Date:</strong> {datetime.now().strftime('%B %d, %Y')}</p>
    <p><strong>Client:</strong> {client_name}</p>

    <h2>Executive Summary</h2>
    <p>{sow.get('executive_summary', '')}</p>

    <h2>Scope of Work</h2>
    <ul>
        {scope_html}
    </ul>

    <h2>Deliverables</h2>
    <ul>
        {deliverables_html}
    </ul>

    <h2>Timeline</h2>
    <table>
        <tr><th>Phase</th><th>Duration</th><th>Description</th></tr>
        {timeline_html}
    </table>

    <h2>Pricing</h2>
    <p class="total">Total: ${total:,.0f} USD</p>
    <p>{pricing.get('structure', '')}</p>

    <table>
        <tr><th>Milestone</th><th>Amount</th><th>Due</th></tr>
        {payment_html}
    </table>

    <h2>Terms & Conditions</h2>
    <ul>
        <li>This SOW is valid for 30 days from the date above.</li>
        <li>Work begins upon receipt of signed agreement and initial payment.</li>
        <li>Two (2) rounds of revisions are included in the scope.</li>
        <li>Additional work beyond scope will be quoted separately.</li>
        <li>Either party may terminate with 14 days written notice.</li>
    </ul>

    <div class="signature-block">
        <div class="signature-box">
            <p><strong>Client</strong></p>
            <p>[CLIENT_SIGNATURE]</p>
            <p class="signature-line">Signature</p>
            <p>[CLIENT_DATE]</p>
            <p class="signature-line">Date</p>
        </div>
        <div class="signature-box">
            <p><strong>Provider</strong></p>
            <p>[PROVIDER_SIGNATURE]</p>
            <p class="signature-line">Signature</p>
        </div>
    </div>
</body>
</html>
"""
        return html


# Convenience function for quick sends
async def send_sow_for_signature(
    sow: dict,
    client_email: str,
    client_name: str,
    sender_email: str = "dale@prodway.ai",
    sender_name: str = "Dale Yarborough",
) -> dict:
    """
    Quick function to send a SOW for signature.

    Returns:
        {"envelope_id": "xxx", "status": "sent", "uri": "..."}
    """
    client = DocuSignClient()
    return await client.create_envelope_from_sow(
        sow=sow,
        client_email=client_email,
        client_name=client_name,
        sender_email=sender_email,
        sender_name=sender_name,
    )
