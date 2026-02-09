# API Keys & Configuration Needed

## 🔴 Required Now (for MVP demo)

### 1. Anthropic API Key
- **Get it**: [console.anthropic.com](https://console.anthropic.com)
- **Variable**: `ANTHROPIC_API_KEY`
- **Format**: `sk-ant-api03-...`

### 2. Slack App Credentials
- **Create at**: [api.slack.com/apps](https://api.slack.com/apps)
- **Variables needed**:
  - `SLACK_BOT_TOKEN` (starts with `xoxb-`)
  - `SLACK_APP_TOKEN` (starts with `xapp-`)
  - `SLACK_SIGNING_SECRET`

**Slack App Settings Required**:
```
OAuth Scopes: chat:write, commands, users:read
Slash Command: /sow
Socket Mode: Enabled
```

---

## 🟡 Required for Full Demo

### 3. DocuSign (E-Signatures)
- **Create at**: [developers.docusign.com](https://developers.docusign.com)
- **Variables needed**:
  - `DOCUSIGN_INTEGRATION_KEY`
  - `DOCUSIGN_SECRET_KEY`
  - `DOCUSIGN_ACCOUNT_ID`
  - `DOCUSIGN_ACCESS_TOKEN` (or we set up OAuth)
- **Callback URL**: `https://your-domain.com/auth/docusign/callback`

### 4. Stripe (Invoicing)
- **Get it**: [dashboard.stripe.com/apikeys](https://dashboard.stripe.com/apikeys)
- **Variables needed**:
  - `STRIPE_SECRET_KEY` (use `sk_test_...` for dev)
  - `STRIPE_WEBHOOK_SECRET` (for payment notifications)
- **Webhook URL**: `https://your-domain.com/webhooks/stripe`

---

## 🟢 Optional (Phase 2)

### 5. Database (for persistence)
Options:
- **Supabase** (Postgres, free tier): [supabase.com](https://supabase.com)
- **PlanetScale** (MySQL): [planetscale.com](https://planetscale.com)  
- **Neon** (Postgres): [neon.tech](https://neon.tech)

Variable: `DATABASE_URL`

### 6. Vector Store (for context/RAG)
Options:
- **Pinecone**: [pinecone.io](https://pinecone.io)
- **Qdrant Cloud**: [cloud.qdrant.io](https://cloud.qdrant.io)

Variables: `PINECONE_API_KEY`, `PINECONE_INDEX`

---

## Deployment Options

### Quick (for demo)
- **Railway**: [railway.app](https://railway.app) - $5/mo, instant deploy
- **Render**: [render.com](https://render.com) - Free tier available

### Production (SOC2 path)
- **AWS EKS**: You already know this 😎
- **Fly.io**: Good middle ground

---

## What I Need From You

Please provide:

```bash
# Copy this, fill in, and send back:

ANTHROPIC_API_KEY=

# After creating Slack app:
SLACK_BOT_TOKEN=
SLACK_APP_TOKEN=
SLACK_SIGNING_SECRET=

# Optional for full demo:
STRIPE_SECRET_KEY=
```

---

## Security Notes (SOC2 Prep)

✅ Already in place:
- Environment variables for secrets (not hardcoded)
- No secrets in git

🔜 Will add:
- Encryption at rest for stored SOWs
- Audit logging for all actions
- Data retention policies
- Access control per org
