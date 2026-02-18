# SowFlow - AI-Powered SOW Generation

Generate Statements of Work from a single Slack command. Full deal flow: AI scope → DocuSign e-signature → Stripe invoicing.

## Quick Start

### 1. Create Slack App

1. Go to [api.slack.com/apps](https://api.slack.com/apps)
2. Click "Create New App" → "From scratch"
3. Name it "SowFlow" and select your workspace

### 2. Configure Slack App

**OAuth & Permissions** → Add Bot Token Scopes:
- `chat:write`
- `commands`
- `users:read`

**OAuth & Permissions** → Add Redirect URL:
- `https://your-domain.com/slack/oauth_redirect`

**Slash Commands** → Create:
- Command: `/sow`
- Request URL: `https://your-domain.com/slack/events`
- Description: "Generate a Statement of Work"
- Usage Hint: "[project description]"

**Event Subscriptions** → Enable:
- Request URL: `https://your-domain.com/slack/events`
- Subscribe to bot events: `app_home_opened`

**Interactivity** → Enable:
- Request URL: `https://your-domain.com/slack/events`

### 3. Set Environment Variables

Copy `ENV_TEMPLATE.txt` to `.env` and fill in:

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-your-key
SLACK_CLIENT_ID=your-client-id
SLACK_CLIENT_SECRET=your-client-secret
SLACK_SIGNING_SECRET=your-signing-secret
APP_URL=https://your-domain.com

# Optional (for full deal flow)
STRIPE_SECRET_KEY=sk_test_...
STRIPE_CLIENT_ID=ca_...
DOCUSIGN_INTEGRATION_KEY=...
DOCUSIGN_SECRET_KEY=...
```

### 4. Run

```bash
cd apps/sowflow
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python main.py  # Starts on port 3000
```

### 5. Use It

In any Slack channel:

```
/sow Need K8s migration for startup, currently on EC2 with 50k daily users,
need to scale to 500k. Timeline: 6 weeks.
```

## Commands

| Command | Description |
|---------|-------------|
| `/sow [description]` | Generate a new SOW |
| `/sow list` | View your recent SOWs |
| `/sow view [id]` | View a specific SOW |

## Features

- **AI-Powered Scoping**: Claude analyzes your description and generates scope, deliverables, timeline, pricing
- **Smart Pricing**: Suggests pricing based on complexity ($5K–$75K+)
- **DocuSign Integration**: Send SOWs for e-signature via customer's own DocuSign
- **Stripe Invoicing**: Auto-generate invoices on signature via Stripe Connect
- **Data Moat**: Every edit teaches the AI to generate better SOWs
- **Multi-Tenant**: Any Slack workspace can install via OAuth

## Architecture

- **OAuth Multi-Tenant**: Workspaces install via `/slack/install` — no bot tokens needed
- **Per-Customer Integrations**: Each team connects their own DocuSign + Stripe accounts
- **File-Based Storage**: JSON persistence in `./data/` (Postgres migration planned)
- **Auto-Invoice on Signature**: DocuSign webhook triggers Stripe invoice creation

## Deployment

```bash
# Docker
docker build -t sowflow .
docker run -p 3000:3000 --env-file .env sowflow

# Railway
railway up
```
