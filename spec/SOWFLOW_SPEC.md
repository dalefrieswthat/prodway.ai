# SowFlow — Product Specification

> **Status:** Production (Slack Marketplace-ready)  
> **Last Updated:** April 2026

---

## Overview

SowFlow is an AI-powered Statement of Work generator that runs as a Slack app. Consultants describe a project in natural language via `/sow`, and the system generates a structured SOW with pricing, timeline, and deliverables — ready to send for e-signature and invoicing.

## Architecture

```
User → /sow command → Slack → FastAPI (Bolt handler)
                                    ↓
                             AI Provider (Gemini/Claude)
                                    ↓
                            Structured JSON SOW
                                    ↓
                        Slack Block Kit message with actions
                                    ↓
                        Send → DocuSign / Stripe / Both
```

**Runtime:** FastAPI + Slack Bolt (HTTP mode, NOT Socket Mode)  
**AI:** Gemini (default, cost-optimized) or Anthropic Claude (BYOK/fallback)  
**Storage:** File-based JSON on EFS (upgrade path to Postgres)  
**Billing:** Stripe — $5/mo base + $0.25/SOW after 25 included  

## Core Workflows

### 1. SOW Generation (`/sow [description]`)
1. User runs `/sow Need K8s migration for startup, 50k users, 6 weeks`
2. System checks subscription status via Stripe billing
3. AI generates structured SOW: title, summary, scope, deliverables, timeline, pricing
4. SOW posted to channel as Block Kit message with action buttons
5. Generation metadata recorded (tokens, latency, cost)
6. Usage tracked for metered billing (> 25 SOWs/month)

### 2. SOW List (`/sow list`)
- Shows team's SOWs with status icons (draft, sent, signed, paid, dismissed)
- Up to 10 most recent, sorted by creation date

### 3. Send SOW (Button Action)
- Opens modal to collect: company name, signer(s) email/name/role
- Up to 5 signers per SOW
- Send options (based on connected integrations):
  - DocuSign e-signature
  - Stripe payment link
  - Stripe invoice
- SOW converted to HTML for DocuSign envelope

### 4. Edit SOW (Button Action)
- Paywall check: only subscribers can edit
- Opens modal with pre-filled fields: title, summary, scope, pricing
- Edits tracked as training signals for AI improvement
- Generation metadata updated (was_edited, fields_edited)

### 5. Dismiss SOW (Button Action)
- Marks SOW as dismissed
- Outcome recorded for analytics

## Data Model (File-based)

```
data/
├── installations/    # Slack OAuth tokens (per workspace)
├── states/           # OAuth state tokens (ephemeral)
├── sows/             # SOW JSON files ({sow_id}.json)
├── integrations/     # Per-team settings: DocuSign, Stripe, billing, API keys
├── api_tokens/       # CLI-generated API tokens
├── invoices/         # Invoice tracking
├── audit/            # Append-only audit log per team
├── edits/            # SOW edit history (training data)
├── generations/      # AI generation metadata (cost, latency)
└── outcomes/         # Deal outcomes (signed, paid, dismissed)
```

## Integrations

### DocuSign (OAuth2 per workspace)
- Connect: `/connect/docusign?team_id=T123`
- Token refresh: automatic via refresh_token
- SOW → HTML → DocuSign envelope with anchor tabs
- Webhook: `docusign-envelope-completed` → marks SOW signed, auto-creates invoice

### Stripe Connect (OAuth2 per workspace)
- Connect: `/connect/stripe?team_id=T123`
- Payment links: one-time payment URL from SOW pricing
- Invoices: auto-generated on DocuSign completion
- Billing: platform subscription ($5/mo + metered usage)

### Slack
- OAuth multi-tenant (any workspace can install)
- Scopes: `chat:write`, `commands`, `users:read`
- App Home: shows API key for FormPilot, subscription status

## Billing Model

| Component | Price |
|-----------|-------|
| Base subscription | $5/month |
| Included SOWs | 25/month |
| Overage | $0.25 per SOW |

Managed via Stripe Products + Prices. Metered usage reported via `SubscriptionItem.create_usage_record`.

## API Endpoints

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | `/health` | None | Health check |
| GET | `/version` | None | Deployment version |
| GET | `/slack/install` | None | OAuth install redirect |
| GET | `/slack/oauth_redirect` | Slack | OAuth callback |
| POST | `/slack/events` | Slack signing | All Slack events |
| GET | `/connect/docusign` | Query param | DocuSign OAuth start |
| GET | `/connect/docusign/callback` | OAuth | DocuSign callback |
| GET | `/connect/stripe` | Query param | Stripe Connect start |
| GET | `/connect/stripe/callback` | OAuth | Stripe Connect callback |
| POST | `/webhooks/docusign` | None | DocuSign webhooks |
| POST | `/webhooks/stripe` | Stripe sig | Stripe webhooks |
| GET | `/signup` | None | Pay-first signup page |
| GET | `/signup/connect-slack` | Query param | Post-payment Slack connect |
| POST | `/api/contact` | None | Contact form |
| GET | `/api/validate-key` | X-API-Key | API key validation |
| GET | `/api/billing/checkout` | Query param | Stripe Checkout |
| GET | `/api/billing/portal` | Query param | Stripe Customer Portal |
| GET | `/install/success` | Query param | Post-install success page |

## Security

- **Encryption at rest:** API keys encrypted with Fernet (AES-128-CBC)
- **Audit logging:** Append-only per-team JSONL files
- **Rate limiting:** API key validation capped at 5 attempts/60s per team
- **OAuth state:** Expiring state tokens for CSRF protection
- **Secrets:** AWS Secrets Manager (14 keys)
