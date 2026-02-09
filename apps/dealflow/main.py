"""
DealFlow - SOW Generation Slack Bot
====================================
MVP: /sow command that generates a Statement of Work from a description

Usage in Slack:
  /sow Need K8s migration for startup, 50k users scaling to 500k, 6 weeks

Returns:
  - Structured SOW draft
  - Pricing recommendation  
  - One-click actions: Edit | Send | Dismiss
"""

import os
import json
import re
from datetime import datetime, timedelta

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from anthropic import Anthropic

# Initialize
app = App(token=os.environ.get("SLACK_BOT_TOKEN"))
claude = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

# Your rates and templates
YOUR_HOURLY_RATE = 250  # $/hr
YOUR_NAME = "Dale Yarborough"
YOUR_COMPANY = "Prodway AI"
YOUR_EMAIL = "dale@prodway.ai"


# ============================================================================
# SOW GENERATION
# ============================================================================

SOW_SYSTEM_PROMPT = """You are an expert DevOps consultant helping generate Statements of Work.

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

Return as JSON with this structure:
{
  "title": "Project Title",
  "executive_summary": "...",
  "scope": ["item1", "item2", ...],
  "deliverables": ["item1", "item2", ...],
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
}
"""


def generate_sow(description: str) -> dict:
    """Generate a SOW from a project description using Claude."""
    
    response = claude.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        system=SOW_SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": f"Generate a SOW for this project:\n\n{description}"
        }]
    )
    
    # Extract JSON from response
    content = response.content[0].text
    
    # Try to parse JSON (handle markdown code blocks)
    json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', content)
    if json_match:
        content = json_match.group(1)
    
    try:
        sow = json.loads(content)
    except json.JSONDecodeError:
        # Fallback: return raw content as executive summary
        sow = {
            "title": "Project Proposal",
            "executive_summary": content[:500],
            "scope": ["See details above"],
            "deliverables": ["TBD"],
            "timeline": [{"phase": "TBD", "duration": "TBD", "description": "TBD"}],
            "pricing": {"total": 0, "currency": "USD", "structure": "TBD"}
        }
    
    return sow


def format_sow_for_slack(sow: dict) -> list:
    """Format SOW as Slack blocks."""
    
    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": f"📋 {sow.get('title', 'Statement of Work')}", "emoji": True}
        },
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*Executive Summary*\n{sow.get('executive_summary', 'N/A')}"}
        },
        {"type": "divider"},
    ]
    
    # Scope
    scope_items = sow.get('scope', [])
    if scope_items:
        scope_text = "*Scope of Work*\n" + "\n".join(f"• {item}" for item in scope_items[:8])
        blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": scope_text}})
    
    # Deliverables
    deliverables = sow.get('deliverables', [])
    if deliverables:
        del_text = "*Deliverables*\n" + "\n".join(f"✓ {item}" for item in deliverables[:6])
        blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": del_text}})
    
    # Timeline
    timeline = sow.get('timeline', [])
    if timeline:
        timeline_text = "*Timeline*\n"
        for phase in timeline[:5]:
            timeline_text += f"• *{phase.get('phase', 'Phase')}* ({phase.get('duration', 'TBD')})\n"
        blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": timeline_text}})
    
    blocks.append({"type": "divider"})
    
    # Pricing (prominent)
    pricing = sow.get('pricing', {})
    total = pricing.get('total', 0)
    structure = pricing.get('structure', 'TBD')
    
    blocks.append({
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": f"💰 *Pricing*\n\n*Total: ${total:,.0f} USD*\n{structure}"
        }
    })
    
    # Payment schedule
    schedule = pricing.get('payment_schedule', [])
    if schedule:
        schedule_text = "\n".join(
            f"• {p.get('milestone')}: ${p.get('amount'):,.0f} ({p.get('due')})"
            for p in schedule
        )
        blocks.append({
            "type": "context",
            "elements": [{"type": "mrkdwn", "text": schedule_text}]
        })
    
    blocks.append({"type": "divider"})
    
    # Action buttons
    blocks.append({
        "type": "actions",
        "elements": [
            {
                "type": "button",
                "text": {"type": "plain_text", "text": "✅ Send to Client", "emoji": True},
                "style": "primary",
                "action_id": "send_sow",
                "value": json.dumps(sow)
            },
            {
                "type": "button",
                "text": {"type": "plain_text", "text": "✏️ Edit", "emoji": True},
                "action_id": "edit_sow",
                "value": json.dumps(sow)
            },
            {
                "type": "button",
                "text": {"type": "plain_text", "text": "🗑️ Dismiss", "emoji": True},
                "style": "danger",
                "action_id": "dismiss_sow"
            }
        ]
    })
    
    return blocks


# ============================================================================
# SLACK HANDLERS
# ============================================================================

@app.command("/sow")
def handle_sow_command(ack, command, respond):
    """Handle /sow slash command."""
    ack()
    
    description = command.get("text", "").strip()
    
    if not description:
        respond({
            "response_type": "ephemeral",
            "text": "Please provide a project description.\n\nExample: `/sow K8s migration for startup, 50k users, need to scale to 500k, 6 week timeline`"
        })
        return
    
    # Show loading message
    respond({
        "response_type": "ephemeral",
        "text": "🔄 Generating SOW... (this takes about 5 seconds)"
    })
    
    try:
        # Generate SOW
        sow = generate_sow(description)
        
        # Store the original request
        sow['_original_request'] = description
        sow['_generated_at'] = datetime.now().isoformat()
        sow['_generated_by'] = command.get('user_id')
        
        # Format and send
        blocks = format_sow_for_slack(sow)
        
        respond({
            "response_type": "in_channel",  # Visible to channel
            "blocks": blocks,
            "text": f"SOW Generated: {sow.get('title', 'Project Proposal')}"
        })
        
    except Exception as e:
        respond({
            "response_type": "ephemeral",
            "text": f"❌ Error generating SOW: {str(e)}"
        })


@app.action("send_sow")
def handle_send_sow(ack, body, client, respond):
    """Handle 'Send to Client' button click."""
    ack()
    
    # Get SOW data from button value
    sow = json.loads(body["actions"][0]["value"])
    
    # For MVP: Open a modal to get client email
    client.views_open(
        trigger_id=body["trigger_id"],
        view={
            "type": "modal",
            "callback_id": "send_sow_modal",
            "private_metadata": json.dumps(sow),
            "title": {"type": "plain_text", "text": "Send SOW"},
            "submit": {"type": "plain_text", "text": "Send"},
            "blocks": [
                {
                    "type": "input",
                    "block_id": "client_email",
                    "element": {
                        "type": "email_text_input",
                        "action_id": "email_input",
                        "placeholder": {"type": "plain_text", "text": "client@company.com"}
                    },
                    "label": {"type": "plain_text", "text": "Client Email"}
                },
                {
                    "type": "input",
                    "block_id": "client_name",
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "name_input",
                        "placeholder": {"type": "plain_text", "text": "John Smith"}
                    },
                    "label": {"type": "plain_text", "text": "Client Name"}
                },
                {
                    "type": "input",
                    "block_id": "company_name",
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "company_input",
                        "placeholder": {"type": "plain_text", "text": "Acme Corp"}
                    },
                    "label": {"type": "plain_text", "text": "Company Name"}
                }
            ]
        }
    )


@app.view("send_sow_modal")
def handle_send_sow_submit(ack, body, client, view):
    """Handle SOW send modal submission."""
    ack()
    
    sow = json.loads(view["private_metadata"])
    values = view["state"]["values"]
    
    client_email = values["client_email"]["email_input"]["value"]
    client_name = values["client_name"]["name_input"]["value"]
    company_name = values["company_name"]["company_input"]["value"]
    
    user_id = body["user"]["id"]
    
    # TODO: Integrate with DocuSign here
    # For now, just confirm
    
    client.chat_postMessage(
        channel=user_id,
        text=f"✅ *SOW Ready to Send*\n\n"
             f"*To:* {client_name} ({client_email})\n"
             f"*Company:* {company_name}\n"
             f"*Project:* {sow.get('title')}\n"
             f"*Amount:* ${sow.get('pricing', {}).get('total', 0):,.0f}\n\n"
             f"_DocuSign integration coming soon! For now, the SOW has been saved._"
    )


@app.action("edit_sow")
def handle_edit_sow(ack, body, client):
    """Handle 'Edit' button click."""
    ack()
    
    sow = json.loads(body["actions"][0]["value"])
    
    # Open modal with editable fields
    client.views_open(
        trigger_id=body["trigger_id"],
        view={
            "type": "modal",
            "callback_id": "edit_sow_modal",
            "private_metadata": json.dumps(sow),
            "title": {"type": "plain_text", "text": "Edit SOW"},
            "submit": {"type": "plain_text", "text": "Save"},
            "blocks": [
                {
                    "type": "input",
                    "block_id": "title",
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "title_input",
                        "initial_value": sow.get("title", "")
                    },
                    "label": {"type": "plain_text", "text": "Title"}
                },
                {
                    "type": "input",
                    "block_id": "pricing",
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "pricing_input",
                        "initial_value": str(sow.get("pricing", {}).get("total", 0))
                    },
                    "label": {"type": "plain_text", "text": "Total Price (USD)"}
                },
                {
                    "type": "input",
                    "block_id": "summary",
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "summary_input",
                        "multiline": True,
                        "initial_value": sow.get("executive_summary", "")
                    },
                    "label": {"type": "plain_text", "text": "Executive Summary"}
                }
            ]
        }
    )


@app.action("dismiss_sow")
def handle_dismiss_sow(ack, respond):
    """Handle 'Dismiss' button click."""
    ack()
    respond({
        "response_type": "ephemeral",
        "text": "SOW dismissed.",
        "replace_original": True
    })


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("⚡ Starting DealFlow Slack Bot...")
    print("   Use /sow <description> to generate a Statement of Work")
    
    handler = SocketModeHandler(
        app, 
        os.environ.get("SLACK_APP_TOKEN")
    )
    handler.start()
