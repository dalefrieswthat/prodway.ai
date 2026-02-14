"""
SowFlow - AI-Powered SOW Generation (Marketplace Edition)
==========================================================
Slack Marketplace-ready app with OAuth multi-tenant install,
DocuSign e-signatures, and Stripe invoicing.

Deploy as a FastAPI service. Any Slack workspace can install via OAuth.

Usage:
  /sow Need K8s migration for startup, 50k users, 6 weeks
  /sow list
"""

import os
import json
import re
import uuid
import base64
import logging
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()  # Load .env file from current directory or parent

import stripe
import httpx
from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse
from anthropic import Anthropic
from slack_bolt import App
from slack_bolt.oauth.oauth_settings import OAuthSettings
from slack_bolt.adapter.fastapi import SlackRequestHandler
from slack_sdk.oauth.installation_store import FileInstallationStore
from slack_sdk.oauth.state_store import FileOAuthStateStore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sowflow")

# ============================================================================
# CONFIGURATION
# ============================================================================

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
SLACK_CLIENT_ID = os.environ.get("SLACK_CLIENT_ID", "")
SLACK_CLIENT_SECRET = os.environ.get("SLACK_CLIENT_SECRET", "")
SLACK_SIGNING_SECRET = os.environ.get("SLACK_SIGNING_SECRET", "")

# Platform keys (YOUR Stripe platform account for Stripe Connect)
STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
STRIPE_CLIENT_ID = os.environ.get("STRIPE_CLIENT_ID", "")  # From Connect settings
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")

# Platform DocuSign app (YOUR integration key — customers OAuth through it)
DOCUSIGN_INTEGRATION_KEY = os.environ.get("DOCUSIGN_INTEGRATION_KEY", "")
DOCUSIGN_SECRET_KEY = os.environ.get("DOCUSIGN_SECRET_KEY", "")
DOCUSIGN_AUTH_SERVER = os.environ.get(
    "DOCUSIGN_AUTH_SERVER", "account-d.docusign.com"  # account.docusign.com for prod
)
DOCUSIGN_BASE_URL = os.environ.get(
    "DOCUSIGN_BASE_URL", "https://demo.docusign.net/restapi"
)

APP_URL = os.environ.get("APP_URL", "https://api.prodway.ai")

# Data directories (file-based storage for MVP — upgrade to Postgres later)
DATA_DIR = Path(os.environ.get("DATA_DIR", "./data"))
for _dir in [
    DATA_DIR / "installations",
    DATA_DIR / "states",
    DATA_DIR / "sows",
    DATA_DIR / "integrations",
]:
    _dir.mkdir(parents=True, exist_ok=True)

# Initialize services
claude = Anthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else None
if STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY


# ============================================================================
# SLACK APP (OAuth Multi-Tenant)
# ============================================================================
# This replaces Socket Mode. Any workspace can now install via /slack/install.
# Slack sends all events to /slack/events via HTTP POST.
# Each workspace gets its own bot token, stored in FileInstallationStore.

bolt_app = App(
    signing_secret=SLACK_SIGNING_SECRET,
    oauth_settings=OAuthSettings(
        client_id=SLACK_CLIENT_ID,
        client_secret=SLACK_CLIENT_SECRET,
        scopes=[
            "chat:write",
            "commands",
            "users:read",
        ],
        install_path="/slack/install",
        redirect_uri_path="/slack/oauth_redirect",
        installation_store=FileInstallationStore(
            base_dir=str(DATA_DIR / "installations")
        ),
        state_store=FileOAuthStateStore(
            expiration_seconds=600,
            base_dir=str(DATA_DIR / "states"),
        ),
    ),
)


# ============================================================================
# SOW STORAGE (file-based for speed — swap to Postgres when ready)
# ============================================================================


def save_sow(sow_id: str, sow_data: dict) -> None:
    """Persist a SOW to the file store."""
    path = DATA_DIR / "sows" / f"{sow_id}.json"
    sow_data["id"] = sow_id
    sow_data["updated_at"] = datetime.now().isoformat()
    path.write_text(json.dumps(sow_data, indent=2, default=str))


def load_sow(sow_id: str) -> dict | None:
    """Load a SOW by ID."""
    path = DATA_DIR / "sows" / f"{sow_id}.json"
    if path.exists():
        return json.loads(path.read_text())
    return None


def list_sows(team_id: str | None = None) -> list[dict]:
    """List SOWs, optionally filtered by Slack team."""
    sows = []
    for f in (DATA_DIR / "sows").glob("*.json"):
        try:
            sow = json.loads(f.read_text())
            if team_id is None or sow.get("_team_id") == team_id:
                sows.append(sow)
        except json.JSONDecodeError:
            continue
    return sorted(sows, key=lambda s: s.get("created_at", ""), reverse=True)


# ============================================================================
# DATA MOAT: Edit tracking + AI generation metrics
# ============================================================================
# These functions capture the data that makes Prodway defensible.
# File-based for now — same pattern as SOW storage, swap to Postgres later.

EDITS_DIR = DATA_DIR / "edits"
GENERATIONS_DIR = DATA_DIR / "generations"
OUTCOMES_DIR = DATA_DIR / "outcomes"
INTEGRATIONS_DIR = DATA_DIR / "integrations"
for _mdir in [EDITS_DIR, GENERATIONS_DIR, OUTCOMES_DIR, INTEGRATIONS_DIR]:
    _mdir.mkdir(parents=True, exist_ok=True)


# ============================================================================
# PER-CUSTOMER INTEGRATION STORAGE
# ============================================================================
# Each Slack workspace stores their own DocuSign + Stripe credentials.
# Customers connect their OWN accounts — Prodway is the platform, not in the money flow.


def save_team_integrations(team_id: str, data: dict) -> None:
    """Save a team's integration credentials."""
    path = INTEGRATIONS_DIR / f"{team_id}.json"
    existing = load_team_integrations(team_id)
    existing.update(data)
    existing["updated_at"] = datetime.now().isoformat()
    path.write_text(json.dumps(existing, indent=2, default=str))


def load_team_integrations(team_id: str) -> dict:
    """Load a team's integration credentials."""
    path = INTEGRATIONS_DIR / f"{team_id}.json"
    if path.exists():
        return json.loads(path.read_text())
    return {}


def get_team_docusign(team_id: str) -> dict | None:
    """Get a team's DocuSign credentials, or None if not connected."""
    integrations = load_team_integrations(team_id)
    if integrations.get("docusign_access_token"):
        return {
            "access_token": integrations["docusign_access_token"],
            "refresh_token": integrations.get("docusign_refresh_token", ""),
            "account_id": integrations.get("docusign_account_id", ""),
            "base_uri": integrations.get("docusign_base_uri", DOCUSIGN_BASE_URL),
        }
    return None


def get_team_stripe(team_id: str) -> str | None:
    """Get a team's Stripe Connect account ID, or None if not connected."""
    integrations = load_team_integrations(team_id)
    return integrations.get("stripe_account_id")


def save_edit(sow_id: str, team_id: str, edited_by: str,
              field_name: str, old_value: str, new_value: str) -> None:
    """Record an edit — every edit is a training signal for improving AI output."""
    edit = {
        "id": str(uuid.uuid4())[:8],
        "sow_id": sow_id,
        "team_id": team_id,
        "edited_by": edited_by,
        "field_name": field_name,
        "old_value": old_value,
        "new_value": new_value,
        "created_at": datetime.now().isoformat(),
    }
    path = EDITS_DIR / f"{sow_id}_{edit['id']}.json"
    path.write_text(json.dumps(edit, indent=2, default=str))


def save_generation_metadata(sow_id: str, team_id: str,
                             response_obj: object, generation_time_ms: int) -> None:
    """Track AI generation performance — cost, speed, quality metrics."""
    usage = getattr(response_obj, "usage", None)
    gen = {
        "id": str(uuid.uuid4())[:8],
        "sow_id": sow_id,
        "team_id": team_id,
        "model": getattr(response_obj, "model", "unknown"),
        "prompt_tokens": getattr(usage, "input_tokens", 0) if usage else 0,
        "completion_tokens": getattr(usage, "output_tokens", 0) if usage else 0,
        "generation_time_ms": generation_time_ms,
        "was_edited": False,
        "edit_count": 0,
        "fields_edited": [],
        # Estimate cost: ~$3/M input, ~$15/M output for Sonnet
        "estimated_cost_usd": round(
            (getattr(usage, "input_tokens", 0) * 3 / 1_000_000 +
             getattr(usage, "output_tokens", 0) * 15 / 1_000_000)
            if usage else 0, 4
        ),
        "created_at": datetime.now().isoformat(),
    }
    path = GENERATIONS_DIR / f"{sow_id}.json"
    path.write_text(json.dumps(gen, indent=2, default=str))


def mark_generation_edited(sow_id: str, fields: list[str]) -> None:
    """Update generation record when user edits the SOW."""
    path = GENERATIONS_DIR / f"{sow_id}.json"
    if path.exists():
        gen = json.loads(path.read_text())
        gen["was_edited"] = True
        gen["edit_count"] = gen.get("edit_count", 0) + len(fields)
        existing = gen.get("fields_edited", [])
        gen["fields_edited"] = list(set(existing + fields))
        path.write_text(json.dumps(gen, indent=2, default=str))


def save_outcome(sow_id: str, team_id: str, outcome: str,
                 **kwargs) -> None:
    """Record deal outcome — the core of pricing intelligence."""
    record = {
        "id": str(uuid.uuid4())[:8],
        "sow_id": sow_id,
        "team_id": team_id,
        "outcome": outcome,
        "created_at": datetime.now().isoformat(),
        **kwargs,
    }
    path = OUTCOMES_DIR / f"{sow_id}.json"
    path.write_text(json.dumps(record, indent=2, default=str))


# ============================================================================
# SOW GENERATION (Claude AI)
# ============================================================================

SOW_SYSTEM_PROMPT = """You are an expert technical consultant helping generate Statements of Work.

Given a project description, generate a structured SOW with:
1. Executive Summary (2-3 sentences)
2. Scope of Work (bullet points of what's included)
3. Deliverables (specific outputs)
4. Timeline (phases with durations)
5. Pricing (based on complexity)

Pricing guidelines:
- Simple (1-2 weeks): $5,000 - $15,000
- Medium (3-4 weeks): $15,000 - $35,000
- Complex (5-8 weeks): $35,000 - $75,000
- Enterprise (8+ weeks): $75,000+

Always include:
- 50% upfront, 50% on completion (or milestone-based for larger projects)
- 2 revision rounds included
- Timeline starts upon signed agreement and deposit

Return ONLY valid JSON with this structure:
{
  "title": "Project Title",
  "executive_summary": "...",
  "scope": ["item1", "item2"],
  "deliverables": ["item1", "item2"],
  "timeline": [
    {"phase": "Phase 1: ...", "duration": "X weeks", "description": "..."}
  ],
  "pricing": {
    "total": 30000,
    "currency": "USD",
    "structure": "50% upfront, 50% on completion",
    "payment_schedule": [
      {"milestone": "Signed Agreement", "amount": 15000, "due": "Upon signing"},
      {"milestone": "Project Completion", "amount": 15000, "due": "On delivery"}
    ]
  },
  "assumptions": ["assumption1", "assumption2"],
  "exclusions": ["not included 1", "not included 2"]
}"""


def generate_sow(description: str, team_id: str = "") -> tuple[dict, object, int]:
    """
    Generate a SOW from a natural language project description using Claude.

    Returns: (sow_dict, raw_response, generation_time_ms)
    The raw response and timing are used for data moat tracking.
    """
    import time

    if not claude:
        raise ValueError("Anthropic API key not configured")

    start = time.monotonic()
    response = claude.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        system=SOW_SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"Generate a SOW for this project:\n\n{description}",
            }
        ],
    )
    generation_time_ms = int((time.monotonic() - start) * 1000)

    content = response.content[0].text

    # Extract JSON from potential markdown code blocks
    json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", content)
    if json_match:
        content = json_match.group(1)

    try:
        sow = json.loads(content)
    except json.JSONDecodeError:
        sow = {
            "title": "Project Proposal",
            "executive_summary": content[:500],
            "scope": ["See details above"],
            "deliverables": ["TBD"],
            "timeline": [
                {"phase": "TBD", "duration": "TBD", "description": "TBD"}
            ],
            "pricing": {"total": 0, "currency": "USD", "structure": "TBD"},
        }

    return sow, response, generation_time_ms


# ============================================================================
# SLACK MESSAGE FORMATTING (Block Kit)
# ============================================================================


def format_sow_for_slack(sow: dict, sow_id: str) -> list:
    """Format SOW as Slack Block Kit blocks with action buttons."""
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"📋 {sow.get('title', 'Statement of Work')}",
                "emoji": True,
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Executive Summary*\n{sow.get('executive_summary', 'N/A')}",
            },
        },
        {"type": "divider"},
    ]

    # Scope
    scope_items = sow.get("scope", [])
    if scope_items:
        scope_text = "*Scope of Work*\n" + "\n".join(
            f"• {item}" for item in scope_items[:8]
        )
        blocks.append(
            {"type": "section", "text": {"type": "mrkdwn", "text": scope_text}}
        )

    # Deliverables
    deliverables = sow.get("deliverables", [])
    if deliverables:
        del_text = "*Deliverables*\n" + "\n".join(
            f"✓ {item}" for item in deliverables[:6]
        )
        blocks.append(
            {"type": "section", "text": {"type": "mrkdwn", "text": del_text}}
        )

    # Timeline
    timeline = sow.get("timeline", [])
    if timeline:
        timeline_text = "*Timeline*\n"
        for phase in timeline[:5]:
            timeline_text += (
                f"• *{phase.get('phase', 'Phase')}* "
                f"({phase.get('duration', 'TBD')})\n"
            )
        blocks.append(
            {"type": "section", "text": {"type": "mrkdwn", "text": timeline_text}}
        )

    blocks.append({"type": "divider"})

    # Pricing
    pricing = sow.get("pricing", {})
    total = pricing.get("total", 0)
    structure = pricing.get("structure", "TBD")
    blocks.append(
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"💰 *Pricing*\n\n*Total: ${total:,.0f} USD*\n{structure}",
            },
        }
    )

    # Payment schedule
    schedule = pricing.get("payment_schedule", [])
    if schedule:
        schedule_text = "\n".join(
            f"• {p.get('milestone')}: ${p.get('amount'):,.0f} ({p.get('due')})"
            for p in schedule
        )
        blocks.append(
            {
                "type": "context",
                "elements": [{"type": "mrkdwn", "text": schedule_text}],
            }
        )

    blocks.append({"type": "divider"})

    # Action buttons — value is sow_id (persisted), not the full SOW JSON
    blocks.append(
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "✅ Send to Client",
                        "emoji": True,
                    },
                    "style": "primary",
                    "action_id": "send_sow",
                    "value": sow_id,
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "✏️ Edit",
                        "emoji": True,
                    },
                    "action_id": "edit_sow",
                    "value": sow_id,
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "🗑️ Dismiss",
                        "emoji": True,
                    },
                    "style": "danger",
                    "action_id": "dismiss_sow",
                    "value": sow_id,
                },
            ],
        }
    )

    return blocks


# ============================================================================
# DOCUSIGN: E-SIGNATURE INTEGRATION
# ============================================================================


def generate_sow_html(sow: dict, client_name: str, company_name: str) -> str:
    """Generate a professional HTML SOW document for DocuSign."""
    pricing = sow.get("pricing", {})
    total = pricing.get("total", 0)

    scope_html = "\n".join(f"<li>{item}</li>" for item in sow.get("scope", []))
    deliverables_html = "\n".join(
        f"<li>{item}</li>" for item in sow.get("deliverables", [])
    )
    timeline_html = "\n".join(
        f"<tr><td>{p.get('phase')}</td><td>{p.get('duration')}</td>"
        f"<td>{p.get('description', '')}</td></tr>"
        for p in sow.get("timeline", [])
    )
    payment_html = "\n".join(
        f"<tr><td>{p.get('milestone')}</td><td>${p.get('amount'):,.0f}</td>"
        f"<td>{p.get('due')}</td></tr>"
        for p in pricing.get("payment_schedule", [])
    )
    assumptions_html = "\n".join(
        f"<li>{item}</li>" for item in sow.get("assumptions", [])
    )
    exclusions_html = "\n".join(
        f"<li>{item}</li>" for item in sow.get("exclusions", [])
    )

    return f"""<!DOCTYPE html>
<html>
<head>
<style>
  body {{ font-family: 'Helvetica Neue', Arial, sans-serif; max-width: 800px;
         margin: 40px auto; padding: 20px; color: #333; line-height: 1.6; }}
  h1 {{ color: #1a1a2e; border-bottom: 3px solid #0066ff; padding-bottom: 10px; }}
  h2 {{ color: #16213e; margin-top: 30px; }}
  table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
  th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
  th {{ background-color: #f8f9fa; font-weight: 600; }}
  .total {{ font-size: 28px; font-weight: bold; color: #0066ff; }}
  .signature-block {{ margin-top: 60px; display: flex; justify-content: space-between; }}
  .signature-box {{ width: 45%; }}
  .signature-line {{ border-top: 1px solid #333; margin-top: 60px; padding-top: 5px; }}
  .meta {{ color: #666; font-size: 14px; }}
</style>
</head>
<body>
  <h1>Statement of Work</h1>
  <h2>{sow.get('title', 'Project Proposal')}</h2>

  <p class="meta"><strong>Date:</strong> {datetime.now().strftime('%B %d, %Y')}</p>
  <p class="meta"><strong>Prepared for:</strong> {client_name}, {company_name}</p>

  <h2>Executive Summary</h2>
  <p>{sow.get('executive_summary', '')}</p>

  <h2>Scope of Work</h2>
  <ul>{scope_html}</ul>

  <h2>Deliverables</h2>
  <ul>{deliverables_html}</ul>

  <h2>Timeline</h2>
  <table>
    <tr><th>Phase</th><th>Duration</th><th>Description</th></tr>
    {timeline_html}
  </table>

  <h2>Investment</h2>
  <p class="total">Total: ${total:,.0f} USD</p>
  <p>{pricing.get('structure', '')}</p>
  <table>
    <tr><th>Milestone</th><th>Amount</th><th>Due</th></tr>
    {payment_html}
  </table>

  {"<h2>Assumptions</h2><ul>" + assumptions_html + "</ul>" if assumptions_html else ""}
  {"<h2>Exclusions</h2><ul>" + exclusions_html + "</ul>" if exclusions_html else ""}

  <h2>Terms &amp; Conditions</h2>
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
</html>"""


def send_docusign_envelope(
    sow: dict, client_email: str, client_name: str, company_name: str,
    team_id: str = "",
) -> dict | None:
    """
    Send SOW via the CUSTOMER's DocuSign account for e-signature.
    Each team connects their own DocuSign via OAuth.
    """
    ds_creds = get_team_docusign(team_id) if team_id else None
    if not ds_creds:
        return None

    html_content = generate_sow_html(sow, client_name, company_name)
    doc_base64 = base64.b64encode(html_content.encode()).decode()

    envelope = {
        "emailSubject": f"Statement of Work: {sow.get('title', 'Project Proposal')}",
        "emailBlurb": (
            f"Please review and sign the attached Statement of Work "
            f"for {sow.get('title')}."
        ),
        "status": "sent",
        "documents": [
            {
                "documentId": "1",
                "name": f"SOW - {sow.get('title', 'Project')}.html",
                "fileExtension": "html",
                "documentBase64": doc_base64,
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
                }
            ]
        },
    }

    base_uri = ds_creds["base_uri"].rstrip("/")
    account_id = ds_creds["account_id"]
    access_token = ds_creds["access_token"]
    # DocuSign userinfo returns base_uri like "https://demo.docusign.net"
    # but the API needs "/restapi" appended
    if not base_uri.endswith("/restapi"):
        base_uri = f"{base_uri}/restapi"
    api_url = f"{base_uri}/v2.1/accounts/{account_id}"

    try:
        with httpx.Client(timeout=30) as client:
            resp = client.post(
                f"{api_url}/envelopes",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                },
                json=envelope,
            )
            if resp.status_code in (200, 201):
                return resp.json()
            else:
                logger.error(f"DocuSign error: {resp.status_code} {resp.text}")
                return None
    except Exception as e:
        logger.error(f"DocuSign request failed: {e}")
        return None


# ============================================================================
# STRIPE: PAYMENT & INVOICING INTEGRATION
# ============================================================================


def create_stripe_payment_link(
    sow: dict, client_email: str, client_name: str, team_id: str = ""
) -> dict | None:
    """Create a Stripe payment link on the CUSTOMER's connected Stripe account."""
    stripe_account_id = get_team_stripe(team_id) if team_id else None
    if not stripe_account_id or not STRIPE_SECRET_KEY:
        return None

    pricing = sow.get("pricing", {})
    total = pricing.get("total", 0)
    title = sow.get("title", "Project")

    try:
        # Create on the connected account (customer's Stripe)
        product = stripe.Product.create(
            name=f"SOW: {title}",
            description=sow.get("executive_summary", "")[:500],
            metadata={"client_email": client_email, "client_name": client_name},
            stripe_account=stripe_account_id,
        )
        price = stripe.Price.create(
            product=product.id,
            unit_amount=int(total * 100),
            currency="usd",
            stripe_account=stripe_account_id,
        )
        link = stripe.PaymentLink.create(
            line_items=[{"price": price.id, "quantity": 1}],
            metadata={"sow_title": title, "client_email": client_email},
            after_completion={
                "type": "redirect",
                "redirect": {"url": f"{APP_URL}/thank-you"},
            },
            stripe_account=stripe_account_id,
        )
        return {"url": link.url, "amount": total, "product_id": product.id}
    except Exception as e:
        logger.error(f"Stripe payment link error: {e}")
        return None


def create_stripe_invoice(
    sow: dict, client_email: str, client_name: str, team_id: str = ""
) -> dict | None:
    """Create and send a Stripe invoice on the CUSTOMER's connected Stripe account."""
    stripe_account_id = get_team_stripe(team_id) if team_id else None
    if not stripe_account_id or not STRIPE_SECRET_KEY:
        return None

    pricing = sow.get("pricing", {})
    total = pricing.get("total", 0)
    title = sow.get("title", "Project")

    try:
        # Get or create customer on the connected account
        customers = stripe.Customer.list(
            email=client_email, limit=1,
            stripe_account=stripe_account_id,
        )
        if customers.data:
            customer = customers.data[0]
        else:
            customer = stripe.Customer.create(
                email=client_email,
                name=client_name,
                metadata={"source": "sowflow"},
                stripe_account=stripe_account_id,
            )

        invoice = stripe.Invoice.create(
            customer=customer.id,
            collection_method="send_invoice",
            days_until_due=14,
            metadata={"sow_title": title},
            stripe_account=stripe_account_id,
        )
        stripe.InvoiceItem.create(
            customer=customer.id,
            invoice=invoice.id,
            amount=int(total * 100),
            currency="usd",
            description=f"Statement of Work: {title}",
            stripe_account=stripe_account_id,
        )
        invoice = stripe.Invoice.finalize_invoice(
            invoice.id, stripe_account=stripe_account_id
        )
        stripe.Invoice.send_invoice(
            invoice.id, stripe_account=stripe_account_id
        )

        return {
            "invoice_id": invoice.id,
            "invoice_url": invoice.hosted_invoice_url,
            "amount": total,
        }
    except Exception as e:
        logger.error(f"Stripe invoice error: {e}")
        return None


# ============================================================================
# SLACK COMMAND & ACTION HANDLERS
# ============================================================================


@bolt_app.command("/sow")
def handle_sow_command(ack, command, respond, context):
    """Handle /sow slash command — generates AI-powered SOW."""
    ack()

    description = command.get("text", "").strip()
    team_id = context.get("team_id", command.get("team_id", "unknown"))

    if not description:
        respond(
            {
                "response_type": "ephemeral",
                "text": (
                    "Please provide a project description.\n\n"
                    "Example: `/sow K8s migration for startup, 50k users, "
                    "need to scale to 500k, 6 week timeline`\n\n"
                    "Or try `/sow list` to see your SOWs."
                ),
            }
        )
        return

    # /sow list — show existing SOWs
    if description.lower() == "list":
        sows = list_sows(team_id)
        if not sows:
            respond(
                {
                    "response_type": "ephemeral",
                    "text": "No SOWs yet. Use `/sow [description]` to create one.",
                }
            )
            return
        text = "*Your SOWs:*\n\n"
        status_icons = {
            "draft": "📝",
            "sent": "📤",
            "signed": "✅",
            "paid": "💰",
            "dismissed": "🗑️",
        }
        for s in sows[:10]:
            icon = status_icons.get(s.get("status", "draft"), "📝")
            total = s.get("pricing", {}).get("total", 0)
            text += (
                f"{icon} *{s.get('title', 'Untitled')}* — "
                f"${total:,.0f} — _{s.get('status', 'draft')}_\n"
            )
        respond({"response_type": "ephemeral", "text": text})
        return

    # Generate SOW
    respond(
        {
            "response_type": "ephemeral",
            "text": "🔄 Generating SOW... (takes ~5 seconds)",
        }
    )

    try:
        sow, ai_response, gen_time_ms = generate_sow(description, team_id)

        # Persist with metadata
        sow_id = str(uuid.uuid4())[:8]
        sow["_original_request"] = description
        sow["_team_id"] = team_id
        sow["_generated_by"] = command.get("user_id")
        sow["_channel_id"] = command.get("channel_id")
        sow["created_at"] = datetime.now().isoformat()
        sow["status"] = "draft"
        save_sow(sow_id, sow)

        # DATA MOAT: Track AI generation performance
        try:
            save_generation_metadata(sow_id, team_id, ai_response, gen_time_ms)
        except Exception:
            pass  # Don't fail SOW generation if tracking fails

        blocks = format_sow_for_slack(sow, sow_id)
        respond(
            {
                "response_type": "in_channel",
                "blocks": blocks,
                "text": f"SOW Generated: {sow.get('title', 'Project Proposal')}",
            }
        )

    except Exception as e:
        logger.error(f"SOW generation failed: {e}")
        respond(
            {
                "response_type": "ephemeral",
                "text": f"❌ Error generating SOW: {str(e)}",
            }
        )


@bolt_app.action("send_sow")
def handle_send_sow(ack, body, client, context):
    """Open modal to collect client details before sending."""
    ack()
    sow_id = body["actions"][0]["value"]
    team_id = context.get("team_id", body.get("team", {}).get("id", ""))

    # Check what THIS TEAM has connected (per-customer integrations)
    team_docusign = get_team_docusign(team_id)
    team_stripe = get_team_stripe(team_id)

    send_options = []
    if team_docusign:
        send_options.append(
            {
                "text": {
                    "type": "plain_text",
                    "text": "📝 Send via DocuSign for e-signature",
                },
                "value": "docusign",
            }
        )
    if team_stripe:
        send_options.append(
            {
                "text": {
                    "type": "plain_text",
                    "text": "💳 Include Stripe payment link",
                },
                "value": "stripe_link",
            }
        )
        send_options.append(
            {
                "text": {"type": "plain_text", "text": "🧾 Send Stripe invoice"},
                "value": "stripe_invoice",
            }
        )

    modal_blocks = [
        {
            "type": "input",
            "block_id": "client_email",
            "element": {
                "type": "email_text_input",
                "action_id": "email_input",
                "placeholder": {
                    "type": "plain_text",
                    "text": "client@company.com",
                },
            },
            "label": {"type": "plain_text", "text": "Client Email"},
        },
        {
            "type": "input",
            "block_id": "client_name",
            "element": {
                "type": "plain_text_input",
                "action_id": "name_input",
                "placeholder": {"type": "plain_text", "text": "John Smith"},
            },
            "label": {"type": "plain_text", "text": "Client Name"},
        },
        {
            "type": "input",
            "block_id": "company_name",
            "element": {
                "type": "plain_text_input",
                "action_id": "company_input",
                "placeholder": {"type": "plain_text", "text": "Acme Corp"},
            },
            "label": {"type": "plain_text", "text": "Company Name"},
        },
    ]

    # Only show integration options if at least one is configured
    if send_options:
        modal_blocks.append(
            {
                "type": "input",
                "block_id": "send_options",
                "element": {
                    "type": "checkboxes",
                    "action_id": "options_input",
                    "options": send_options,
                    # Pre-select all configured options
                    "initial_options": send_options,
                },
                "label": {"type": "plain_text", "text": "Send Options"},
                "optional": True,
            }
        )
    else:
        modal_blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        "_💡 Connect your DocuSign and Stripe accounts to enable "
                        "e-signatures and invoicing._\n"
                        f"<{APP_URL}/connect/docusign?team_id={team_id}|Connect DocuSign> · "
                        f"<{APP_URL}/connect/stripe?team_id={team_id}|Connect Stripe>"
                    ),
                },
            }
        )

    client.views_open(
        trigger_id=body["trigger_id"],
        view={
            "type": "modal",
            "callback_id": "send_sow_modal",
            "private_metadata": sow_id,
            "title": {"type": "plain_text", "text": "Send SOW to Client"},
            "submit": {"type": "plain_text", "text": "Send"},
            "blocks": modal_blocks,
        },
    )


@bolt_app.view("send_sow_modal")
def handle_send_sow_submit(ack, body, client, view):
    """Process the send modal — triggers DocuSign + Stripe."""
    ack()

    sow_id = view["private_metadata"]
    sow = load_sow(sow_id)
    if not sow:
        return

    values = view["state"]["values"]
    client_email = values["client_email"]["email_input"]["value"]
    client_name = values["client_name"]["name_input"]["value"]
    company_name = values["company_name"]["company_input"]["value"]

    # Parse selected options
    selected = []
    opts_block = values.get("send_options", {}).get("options_input", {})
    if opts_block and opts_block.get("selected_options"):
        selected = [o["value"] for o in opts_block["selected_options"]]

    user_id = body["user"]["id"]

    # Update SOW record
    sow["client_email"] = client_email
    sow["client_name"] = client_name
    sow["company_name"] = company_name
    sow["status"] = "sent"
    now = datetime.now()
    sow["sent_at"] = now.isoformat()

    # DATA MOAT: Calculate time-to-send (how fast from generation to send)
    try:
        created = datetime.fromisoformat(sow.get("created_at", now.isoformat()))
        time_to_send_ms = int((now - created).total_seconds() * 1000)
        sow["_time_to_send_ms"] = time_to_send_ms
    except Exception:
        time_to_send_ms = 0

    # Build result message
    lines = [
        "✅ *SOW Sent Successfully*",
        "",
        f"*To:* {client_name} ({client_email})",
        f"*Company:* {company_name}",
        f"*Project:* {sow.get('title')}",
        f"*Amount:* ${sow.get('pricing', {}).get('total', 0):,.0f}",
        "",
    ]

    team_id = sow.get("_team_id", "")

    # --- DocuSign (customer's own account) ---
    if "docusign" in selected:
        envelope = send_docusign_envelope(
            sow, client_email, client_name, company_name, team_id=team_id
        )
        if envelope:
            sow["docusign_envelope_id"] = envelope.get("envelopeId")
            lines.append(
                f"📝 *DocuSign:* Sent for signature "
                f"(Envelope: `{envelope.get('envelopeId', 'N/A')}`)"
            )
        else:
            lines.append("⚠️ *DocuSign:* Failed to send — check configuration")

    # --- Stripe Payment Link (customer's own account) ---
    if "stripe_link" in selected:
        link = create_stripe_payment_link(sow, client_email, client_name, team_id=team_id)
        if link:
            sow["stripe_payment_url"] = link["url"]
            lines.append(f"💳 *Payment Link:* {link['url']}")
        else:
            lines.append("⚠️ *Stripe Payment Link:* Failed — check configuration")

    # --- Stripe Invoice (customer's own account) ---
    if "stripe_invoice" in selected:
        inv = create_stripe_invoice(sow, client_email, client_name, team_id=team_id)
        if inv:
            sow["stripe_invoice_id"] = inv["invoice_id"]
            lines.append(f"🧾 *Invoice:* Sent — {inv['invoice_url']}")
        else:
            lines.append("⚠️ *Stripe Invoice:* Failed — check configuration")

    # No integrations selected
    if not selected:
        lines.append(
            f"_SOW saved. Connect your accounts to enable e-signatures and invoicing:_\n"
            f"<{APP_URL}/connect/docusign?team_id={team_id}|Connect DocuSign> · "
            f"<{APP_URL}/connect/stripe?team_id={team_id}|Connect Stripe>"
        )

    save_sow(sow_id, sow)

    # Post confirmation to the channel where /sow was run, fallback to DM
    channel = sow.get("_channel_id", user_id)
    try:
        client.chat_postMessage(channel=channel, text="\n".join(lines))
    except Exception:
        # If channel post fails, try DM as ephemeral
        try:
            client.chat_postMessage(channel=user_id, text="\n".join(lines))
        except Exception as e:
            logger.error(f"Failed to send confirmation: {e}")


@bolt_app.action("edit_sow")
def handle_edit_sow(ack, body, client):
    """Open edit modal for the SOW."""
    ack()
    sow_id = body["actions"][0]["value"]
    sow = load_sow(sow_id)
    if not sow:
        return

    client.views_open(
        trigger_id=body["trigger_id"],
        view={
            "type": "modal",
            "callback_id": "edit_sow_modal",
            "private_metadata": sow_id,
            "title": {"type": "plain_text", "text": "Edit SOW"},
            "submit": {"type": "plain_text", "text": "Save"},
            "blocks": [
                {
                    "type": "input",
                    "block_id": "title",
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "title_input",
                        "initial_value": sow.get("title", ""),
                    },
                    "label": {"type": "plain_text", "text": "Title"},
                },
                {
                    "type": "input",
                    "block_id": "pricing",
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "pricing_input",
                        "initial_value": str(
                            sow.get("pricing", {}).get("total", 0)
                        ),
                    },
                    "label": {"type": "plain_text", "text": "Total Price (USD)"},
                },
                {
                    "type": "input",
                    "block_id": "summary",
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "summary_input",
                        "multiline": True,
                        "initial_value": sow.get("executive_summary", ""),
                    },
                    "label": {"type": "plain_text", "text": "Executive Summary"},
                },
            ],
        },
    )


@bolt_app.view("edit_sow_modal")
def handle_edit_sow_submit(ack, body, client, view):
    """Save edits to a SOW — and track what changed (data moat)."""
    ack()

    sow_id = view["private_metadata"]
    sow = load_sow(sow_id)
    if not sow:
        return

    values = view["state"]["values"]
    user_id = body["user"]["id"]
    team_id = sow.get("_team_id", "")
    edited_fields = []

    # Track title edit
    new_title = values["title"]["title_input"]["value"]
    if new_title != sow.get("title", ""):
        save_edit(sow_id, team_id, user_id, "title",
                  sow.get("title", ""), new_title)
        edited_fields.append("title")
    sow["title"] = new_title

    # Track summary edit
    new_summary = values["summary"]["summary_input"]["value"]
    if new_summary != sow.get("executive_summary", ""):
        save_edit(sow_id, team_id, user_id, "executive_summary",
                  sow.get("executive_summary", ""), new_summary)
        edited_fields.append("executive_summary")
    sow["executive_summary"] = new_summary

    # Track pricing edit
    try:
        new_price = float(values["pricing"]["pricing_input"]["value"])
        old_price = sow.get("pricing", {}).get("total", 0)
        if new_price != old_price:
            save_edit(sow_id, team_id, user_id, "pricing.total",
                      str(old_price), str(new_price))
            edited_fields.append("pricing.total")
        sow.setdefault("pricing", {})["total"] = new_price
    except (ValueError, KeyError):
        pass

    save_sow(sow_id, sow)

    # DATA MOAT: Update generation record with edit info
    if edited_fields:
        try:
            mark_generation_edited(sow_id, edited_fields)
        except Exception:
            pass

    total = sow.get("pricing", {}).get("total", 0)
    client.chat_postMessage(
        channel=user_id,
        text=f"✅ SOW updated: *{sow['title']}* — ${total:,.0f}",
    )


@bolt_app.action("dismiss_sow")
def handle_dismiss_sow(ack, body, respond):
    """Dismiss a SOW."""
    ack()
    sow_id = body["actions"][0]["value"]
    sow = load_sow(sow_id)
    if sow:
        sow["status"] = "dismissed"
        save_sow(sow_id, sow)
    respond(
        {"response_type": "ephemeral", "text": "SOW dismissed.", "replace_original": True}
    )


@bolt_app.event("app_home_opened")
def handle_app_home(client, event, context):
    """Render the App Home tab with connection status, commands, and recent SOWs."""
    user_id = event["user"]
    team_id = context.get("team_id", "")

    # Check integration status
    team_docusign = get_team_docusign(team_id)
    team_stripe = get_team_stripe(team_id)

    ds_status = "✅ Connected" if team_docusign else f"<{APP_URL}/connect/docusign?team_id={team_id}|Connect DocuSign>"
    stripe_status = "✅ Connected" if team_stripe else f"<{APP_URL}/connect/stripe?team_id={team_id}|Connect Stripe>"

    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "🚀 SowFlow", "emoji": True},
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    "*AI-powered Statements of Work in seconds.*\n\n"
                    "Type `/sow [project description]` in any channel to generate "
                    "a professional SOW with pricing, timeline, and deliverables."
                ),
            },
        },
        {"type": "divider"},
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    "*🔌 Integrations*\n"
                    f"• 📝 DocuSign: {ds_status}\n"
                    f"• 💳 Stripe: {stripe_status}\n\n"
                    "_Connect your accounts to send SOWs for e-signature "
                    "and automatically invoice clients._"
                ),
            },
        },
        {"type": "divider"},
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    "*Commands:*\n"
                    "• `/sow Need K8s migration, 50k users, 6 weeks` — Generate SOW\n"
                    "• `/sow list` — View your SOWs\n\n"
                    "*How it works:*\n"
                    "1️⃣ `/sow` → AI generates a complete SOW\n"
                    "2️⃣ Review, edit, and click Send\n"
                    "3️⃣ Client receives SOW via DocuSign to approve or deny\n"
                    "4️⃣ On signature → Stripe invoice sent automatically"
                ),
            },
        },
    ]

    # Show recent SOWs for this team
    recent = list_sows(team_id)[:5]
    if recent:
        blocks.append({"type": "divider"})
        sow_text = "*Recent SOWs:*\n"
        status_icons = {
            "draft": "📝", "sent": "📤", "signed": "✅",
            "invoiced": "🧾", "paid": "💰", "dismissed": "🗑️",
        }
        for s in recent:
            icon = status_icons.get(s.get("status", "draft"), "📝")
            total = s.get("pricing", {}).get("total", 0)
            sow_text += (
                f"{icon} *{s.get('title', 'Untitled')}* — "
                f"${total:,.0f} — _{s.get('status', 'draft')}_\n"
            )
        blocks.append(
            {"type": "section", "text": {"type": "mrkdwn", "text": sow_text}}
        )

    client.views_publish(
        user_id=user_id, view={"type": "home", "blocks": blocks}
    )


# ============================================================================
# FASTAPI APPLICATION
# ============================================================================

api = FastAPI(
    title="SowFlow",
    description="AI-Powered SOW Generation for Slack",
    version="1.0.0",
)
slack_handler = SlackRequestHandler(bolt_app)


@api.get("/")
async def root():
    """Root — shows app info and install link."""
    return {
        "app": "SowFlow",
        "version": "1.0.0",
        "status": "running",
        "install_url": f"{APP_URL}/slack/install",
    }


@api.get("/health")
async def health():
    """Health check for load balancers / k8s probes."""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


# --- Slack OAuth & Events ---


@api.get("/slack/install")
async def slack_install(req: Request):
    """Slack OAuth install page — 'Add to Slack' button."""
    return await slack_handler.handle(req)


@api.get("/slack/oauth_redirect")
async def slack_oauth_redirect(req: Request):
    """Slack OAuth callback — stores installation tokens."""
    return await slack_handler.handle(req)


@api.post("/slack/events")
async def slack_events(req: Request):
    """Handles all Slack events: slash commands, interactions, events."""
    return await slack_handler.handle(req)


# --- Per-Customer OAuth: DocuSign Connect ---


@api.get("/connect/docusign")
async def connect_docusign(team_id: str = ""):
    """Start DocuSign OAuth flow — customer connects their own account."""
    if not DOCUSIGN_INTEGRATION_KEY:
        return HTMLResponse(content="<h1>DocuSign not configured</h1>", status_code=500)

    # Store team_id in state so we know who's connecting on callback
    state = f"{team_id}:{uuid.uuid4().hex[:8]}"
    auth_url = (
        f"https://{DOCUSIGN_AUTH_SERVER}/oauth/auth"
        f"?response_type=code"
        f"&scope=signature"
        f"&client_id={DOCUSIGN_INTEGRATION_KEY}"
        f"&redirect_uri={APP_URL}/connect/docusign/callback"
        f"&state={state}"
    )
    from fastapi.responses import RedirectResponse

    return RedirectResponse(url=auth_url)


@api.get("/connect/docusign/callback")
async def connect_docusign_callback(code: str = "", state: str = ""):
    """DocuSign OAuth callback — exchange code for customer's tokens."""
    team_id = state.split(":")[0] if ":" in state else state

    if not code:
        return HTMLResponse(content="<h1>Authorization failed</h1>", status_code=400)

    # Exchange code for access token
    token_url = f"https://{DOCUSIGN_AUTH_SERVER}/oauth/token"
    auth_header = base64.b64encode(
        f"{DOCUSIGN_INTEGRATION_KEY}:{DOCUSIGN_SECRET_KEY}".encode()
    ).decode()

    try:
        with httpx.Client(timeout=30) as client:
            resp = client.post(
                token_url,
                headers={
                    "Authorization": f"Basic {auth_header}",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": f"{APP_URL}/connect/docusign/callback",
                },
            )
            resp.raise_for_status()
            token_data = resp.json()

            # Get user info to find their account ID and base URI
            userinfo_resp = client.get(
                f"https://{DOCUSIGN_AUTH_SERVER}/oauth/userinfo",
                headers={"Authorization": f"Bearer {token_data['access_token']}"},
            )
            userinfo_resp.raise_for_status()
            userinfo = userinfo_resp.json()

            # Get the default account
            accounts = userinfo.get("accounts", [])
            default_account = next(
                (a for a in accounts if a.get("is_default")),
                accounts[0] if accounts else {},
            )

            # Save to team integrations
            save_team_integrations(team_id, {
                "docusign_access_token": token_data["access_token"],
                "docusign_refresh_token": token_data.get("refresh_token", ""),
                "docusign_account_id": default_account.get("account_id", ""),
                "docusign_base_uri": default_account.get("base_uri", DOCUSIGN_BASE_URL),
                "docusign_user_name": userinfo.get("name", ""),
                "docusign_connected_at": datetime.now().isoformat(),
            })

            return HTMLResponse(content=(
                "<html><body style='font-family:system-ui;text-align:center;padding:80px;"
                "background:#f8f9fa'>"
                "<div style='max-width:500px;margin:0 auto;background:white;padding:40px;"
                "border-radius:12px;box-shadow:0 2px 8px rgba(0,0,0,0.1)'>"
                "<h1 style='color:#22c55e'>✅ DocuSign Connected</h1>"
                f"<p>Account: {default_account.get('account_name', 'Connected')}</p>"
                "<p style='color:#666'>You can close this window and return to Slack.</p>"
                "</div></body></html>"
            ))

    except Exception as e:
        logger.error(f"DocuSign OAuth failed: {e}")
        return HTMLResponse(
            content=f"<h1>Connection failed</h1><p>{str(e)}</p>",
            status_code=500,
        )


# --- Per-Customer OAuth: Stripe Connect ---


@api.get("/connect/stripe")
async def connect_stripe(team_id: str = ""):
    """Start Stripe Connect OAuth — customer connects their own Stripe account."""
    if not STRIPE_CLIENT_ID:
        return HTMLResponse(content="<h1>Stripe Connect not configured</h1>", status_code=500)

    state = f"{team_id}:{uuid.uuid4().hex[:8]}"
    connect_url = (
        f"https://connect.stripe.com/oauth/authorize"
        f"?response_type=code"
        f"&client_id={STRIPE_CLIENT_ID}"
        f"&scope=read_write"
        f"&redirect_uri={APP_URL}/connect/stripe/callback"
        f"&state={state}"
    )
    from fastapi.responses import RedirectResponse

    return RedirectResponse(url=connect_url)


@api.get("/connect/stripe/callback")
async def connect_stripe_callback(code: str = "", state: str = ""):
    """Stripe Connect OAuth callback — exchange code for connected account ID."""
    team_id = state.split(":")[0] if ":" in state else state

    if not code:
        return HTMLResponse(content="<h1>Authorization failed</h1>", status_code=400)

    try:
        # Exchange authorization code for connected account
        resp = stripe.OAuth.token(grant_type="authorization_code", code=code)

        save_team_integrations(team_id, {
            "stripe_account_id": resp["stripe_user_id"],
            "stripe_access_token": resp.get("access_token", ""),
            "stripe_refresh_token": resp.get("refresh_token", ""),
            "stripe_connected_at": datetime.now().isoformat(),
        })

        return HTMLResponse(content=(
            "<html><body style='font-family:system-ui;text-align:center;padding:80px;"
            "background:#f8f9fa'>"
            "<div style='max-width:500px;margin:0 auto;background:white;padding:40px;"
            "border-radius:12px;box-shadow:0 2px 8px rgba(0,0,0,0.1)'>"
            "<h1 style='color:#22c55e'>✅ Stripe Connected</h1>"
            f"<p>Account ID: {resp['stripe_user_id']}</p>"
            "<p style='color:#666'>You can close this window and return to Slack.</p>"
            "</div></body></html>"
        ))

    except Exception as e:
        logger.error(f"Stripe Connect OAuth failed: {e}")
        return HTMLResponse(
            content=f"<h1>Connection failed</h1><p>{str(e)}</p>",
            status_code=500,
        )


# --- DocuSign Webhook: Auto-invoice on signature ---


@api.post("/webhooks/docusign")
async def docusign_webhook(req: Request):
    """
    DocuSign Connect webhook — when a SOW is signed, automatically
    create a Stripe invoice on the customer's connected account.
    """
    body = await req.json()

    # DocuSign sends envelope status changes
    status = body.get("status", "")
    envelope_id = body.get("envelopeId", "")

    if status != "completed":
        return {"status": "ignored", "reason": f"status={status}"}

    logger.info(f"DocuSign envelope completed: {envelope_id}")

    # Find the SOW with this envelope ID
    for f in (DATA_DIR / "sows").glob("*.json"):
        try:
            sow = json.loads(f.read_text())
            if sow.get("docusign_envelope_id") == envelope_id:
                team_id = sow.get("_team_id", "")

                # Update SOW status
                sow["status"] = "signed"
                sow["signed_at"] = datetime.now().isoformat()
                save_sow(sow["id"], sow)

                # AUTO-INVOICE: Create Stripe invoice on customer's account
                if get_team_stripe(team_id) and sow.get("client_email"):
                    inv = create_stripe_invoice(
                        sow,
                        sow["client_email"],
                        sow.get("client_name", ""),
                        team_id=team_id,
                    )
                    if inv:
                        sow["stripe_invoice_id"] = inv["invoice_id"]
                        sow["status"] = "invoiced"
                        save_sow(sow["id"], sow)
                        logger.info(
                            f"Auto-invoiced SOW {sow['id']}: {inv['invoice_url']}"
                        )

                # DATA MOAT: Record outcome timing
                try:
                    created = datetime.fromisoformat(sow.get("created_at", ""))
                    sent = datetime.fromisoformat(sow.get("sent_at", ""))
                    signed = datetime.now()
                    save_outcome(
                        sow["id"], team_id, "won",
                        final_value=sow.get("pricing", {}).get("total", 0),
                        time_to_send_ms=sow.get("_time_to_send_ms", 0),
                        time_to_sign_ms=int(
                            (signed - sent).total_seconds() * 1000
                        ),
                    )
                except Exception:
                    pass

                break
        except Exception:
            continue

    return {"status": "ok"}


# --- Stripe Webhook ---


@api.post("/webhooks/stripe")
async def stripe_webhook(req: Request):
    """Stripe webhook for payment notifications."""
    if not STRIPE_WEBHOOK_SECRET:
        return {"status": "webhook_secret_not_configured"}

    payload = await req.body()
    sig = req.headers.get("stripe-signature", "")

    try:
        event = stripe.Webhook.construct_event(payload, sig, STRIPE_WEBHOOK_SECRET)
    except Exception as e:
        logger.error(f"Stripe webhook verification failed: {e}")
        return Response(status_code=400, content=str(e))

    # Handle payment events — track outcomes for pricing intelligence
    if event["type"] == "invoice.paid":
        invoice_data = event["data"]["object"]
        sow_title = invoice_data.get("metadata", {}).get("sow_title", "")
        logger.info(f"Invoice paid: {invoice_data['id']} for {sow_title}")

        # DATA MOAT: Record successful outcome
        # Find the SOW by stripe_invoice_id and update status
        for f in (DATA_DIR / "sows").glob("*.json"):
            try:
                sow = json.loads(f.read_text())
                if sow.get("stripe_invoice_id") == invoice_data["id"]:
                    sow["status"] = "paid"
                    sow["paid_at"] = datetime.now().isoformat()
                    save_sow(sow["id"], sow)

                    # Calculate full funnel timing
                    created = datetime.fromisoformat(sow.get("created_at", ""))
                    sent = datetime.fromisoformat(sow.get("sent_at", ""))
                    paid = datetime.now()
                    save_outcome(
                        sow["id"],
                        sow.get("_team_id", ""),
                        "won",
                        final_value=invoice_data.get("amount_paid", 0) / 100,
                        time_to_send_ms=sow.get("_time_to_send_ms", 0),
                        time_to_pay_ms=int(
                            (paid - sent).total_seconds() * 1000
                        ),
                    )
                    break
            except Exception:
                continue

    elif event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        logger.info(f"Payment completed: {session['id']}")

    return {"status": "ok"}


# --- Thank You Page ---


@api.get("/thank-you")
async def thank_you():
    """Post-payment thank you page."""
    return HTMLResponse(
        content=(
            "<html><body style='font-family:system-ui;text-align:center;padding:80px;"
            "background:#f8f9fa'>"
            "<div style='max-width:500px;margin:0 auto;background:white;padding:40px;"
            "border-radius:12px;box-shadow:0 2px 8px rgba(0,0,0,0.1)'>"
            "<h1 style='color:#22c55e'>✅ Payment Received</h1>"
            "<p style='color:#666;font-size:18px'>Thank you! Your payment has been "
            "processed successfully.</p>"
            "<p style='color:#999;font-size:14px'>You'll receive a confirmation "
            "email shortly.</p>"
            "</div></body></html>"
        )
    )


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 3000))
    logger.info(f"⚡ Starting SowFlow on port {port}")
    logger.info(f"   Install: {APP_URL}/slack/install")
    logger.info(f"   Health:  {APP_URL}/health")
    uvicorn.run(api, host="0.0.0.0", port=port)
