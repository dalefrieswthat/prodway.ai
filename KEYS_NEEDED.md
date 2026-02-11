# SowFlow — Setup Guide (Do These In Order)

## Architecture

```
prodway.ai          → GitHub Pages (landing page — stays as-is)
api.prodway.ai      → Railway (SowFlow backend — new)
```

Customers connect their OWN DocuSign and Stripe accounts.
Prodway is the platform — not in the money flow.

---

## Step 1: Get Your API Keys (do this now)

You can grab all these credentials before deploying anything.

### 1a. Anthropic
- **Already have this** ✅
- Variable: `ANTHROPIC_API_KEY`

### 1b. Slack App Credentials
Your existing Slack app already has these — no deployment needed.

1. Go to [api.slack.com/apps](https://api.slack.com/apps) → select your app
2. **Basic Information** page → scroll to "App Credentials":
   - Copy `Client ID` → `SLACK_CLIENT_ID`
   - Copy `Client Secret` → `SLACK_CLIENT_SECRET`
   - Copy `Signing Secret` → `SLACK_SIGNING_SECRET`

> These exist right now. You do NOT need Railway running to get them.

### 1c. Stripe Connect (optional — can add later)
1. Go to [dashboard.stripe.com/apikeys](https://dashboard.stripe.com/apikeys)
   - Copy Secret Key → `STRIPE_SECRET_KEY`
2. Go to [dashboard.stripe.com/settings/connect](https://dashboard.stripe.com/settings/connect)
   - Enable Standard Connect
   - Copy Client ID (starts with `ca_`) → `STRIPE_CLIENT_ID`

### 1d. DocuSign (optional — can add later)
1. Go to [developers.docusign.com](https://developers.docusign.com)
2. Create an app → Authorization Code Grant
   - Copy Integration Key → `DOCUSIGN_INTEGRATION_KEY`
   - Copy Secret Key → `DOCUSIGN_SECRET_KEY`

---

## Step 2: Deploy to Railway

### Option A: Via Dashboard (recommended)
1. Go to [railway.app](https://railway.app) → open your `prodway.ai` project
2. Click **"+ New"** → **"GitHub Repo"** → select your `prodway` repo
3. Railway detects `railway.json` and builds from `apps/sowflow/Dockerfile`
4. Go to your new service → **Variables** tab → add these:

```
ANTHROPIC_API_KEY=sk-ant-...
SLACK_CLIENT_ID=your-client-id
SLACK_CLIENT_SECRET=your-client-secret
SLACK_SIGNING_SECRET=your-signing-secret
APP_ENV=production
APP_URL=https://your-railway-url.up.railway.app
```

5. Wait for deploy to finish (check Logs tab)
6. Go to **Settings → Networking → Generate Domain**
7. Copy the generated URL (something like `sowflow-production-xxxx.up.railway.app`)
8. **Update** the `APP_URL` variable to match this URL

### Option B: Via CLI
```bash
npm install -g @railway/cli
railway login          # Opens browser
railway link           # Link to existing project
railway up             # Deploy
```

---

## Step 3: Verify It's Running

Visit your Railway URL in a browser:
```
https://your-railway-url.up.railway.app/health
```

You should see:
```json
{"status": "ok", "timestamp": "..."}
```

---

## Step 4: Add Custom Domain (optional but recommended)

In your DNS provider (where prodway.ai is registered):

```
Type:  CNAME
Name:  api
Value: your-railway-url.up.railway.app
```

Then in Railway → Settings → Networking → Custom Domain → add `api.prodway.ai`

Once DNS propagates, update `APP_URL` to `https://api.prodway.ai`

> If you skip this step, everything still works — just use the Railway URL directly.

---

## Step 5: Update Slack App (AFTER Railway is live)

Now that you have a live URL, go back to your Slack app:

### Option A: Paste the manifest
1. [api.slack.com/apps](https://api.slack.com/apps) → your app → **App Manifest**
2. Replace the entire JSON with the contents of `apps/sowflow/slack-manifest.json`
3. Replace `api.prodway.ai` with your actual URL if different
4. Save

### Option B: Update manually
1. **Socket Mode** → Toggle **OFF**
2. **Slash Commands** → `/sow` → Request URL: `https://YOUR-URL/slack/events`
3. **Interactivity** → ON → Request URL: `https://YOUR-URL/slack/events`
4. **Event Subscriptions** → ON → Request URL: `https://YOUR-URL/slack/events`
   - Subscribe to bot events: `app_home_opened`
5. **OAuth & Permissions** → Redirect URLs: `https://YOUR-URL/slack/oauth_redirect`

### Enable Distribution
1. **Manage Distribution** → check all boxes → Activate Public Distribution

---

## Step 6: Test It

1. Go to `https://YOUR-URL/slack/install` in your browser
2. Click "Add to Slack" → authorize for your workspace
3. Open Slack → find SowFlow in your apps
4. Type `/sow Need K8s migration, 50k users, 6 weeks`
5. You should see an AI-generated SOW with Send/Edit/Dismiss buttons

---

## Step 7: Connect DocuSign + Stripe (after basic flow works)

Once `/sow` works, add the integration keys to Railway variables:

```
STRIPE_SECRET_KEY=sk_test_...
STRIPE_CLIENT_ID=ca_...
DOCUSIGN_INTEGRATION_KEY=...
DOCUSIGN_SECRET_KEY=...
DOCUSIGN_AUTH_SERVER=account-d.docusign.com
DOCUSIGN_BASE_URL=https://demo.docusign.net/restapi
```

Then set up the OAuth redirect URIs:
- **Stripe Connect**: Add redirect URI `https://YOUR-URL/connect/stripe/callback`
- **DocuSign**: Add redirect URI `https://YOUR-URL/connect/docusign/callback`

Set up webhooks:
- **DocuSign Connect**: `https://YOUR-URL/webhooks/docusign` (Envelope Completed)
- **Stripe Webhooks**: `https://YOUR-URL/webhooks/stripe` (invoice.paid, checkout.session.completed)

---

## Quick Reference: All Variables

```bash
# Required (Step 1-2)
ANTHROPIC_API_KEY=
SLACK_CLIENT_ID=
SLACK_CLIENT_SECRET=
SLACK_SIGNING_SECRET=
APP_URL=https://your-railway-url.up.railway.app
APP_ENV=production

# Per-customer integrations (Step 7)
STRIPE_SECRET_KEY=
STRIPE_CLIENT_ID=
STRIPE_WEBHOOK_SECRET=
DOCUSIGN_INTEGRATION_KEY=
DOCUSIGN_SECRET_KEY=
DOCUSIGN_AUTH_SERVER=account-d.docusign.com
DOCUSIGN_BASE_URL=https://demo.docusign.net/restapi
```

---

## The End-to-End Flow (when everything is connected)

```
Customer installs SowFlow from Slack Marketplace
    ↓
Opens App Home → Connects their DocuSign + Stripe
    ↓
/sow Need K8s migration, 50k users, 6 weeks
    ↓
Claude AI generates full SOW (10 seconds)
    ↓
SOW posted in channel → [Send] [Edit] [Dismiss]
    ↓
Click Send → SOW sent via customer's DocuSign
    ↓
Client approves (signs) or denies (declines)
    ↓
On signature → Stripe invoice auto-created on customer's account
    ↓
💰 Client pays → SOW marked "paid"
```
