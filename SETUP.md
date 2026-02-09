# SowFlow Demo Setup

Get the `/sow` Slack command working in 10 minutes.

## Prerequisites

- Python 3.10+
- Anthropic API key (for Claude)
- Slack workspace where you can install apps

## Step 1: Create Slack App (5 min)

1. Go to **[api.slack.com/apps](https://api.slack.com/apps)**
2. Click **"Create New App"** → **"From scratch"**
3. Name: `SowFlow`, Workspace: your workspace

### Configure OAuth Scopes

Go to **OAuth & Permissions** → Add these Bot Token Scopes:
- `chat:write`
- `commands`
- `users:read`

### Create Slash Command

Go to **Slash Commands** → **Create New Command**:
- Command: `/sow`
- Request URL: leave blank (we'll use Socket Mode)
- Description: `Generate a Statement of Work`
- Usage Hint: `[project description]`

### Enable Socket Mode

Go to **Socket Mode** → Toggle **ON**

Generate an App-Level Token:
- Click "Generate Token and Scopes"
- Name: `socket-token`
- Add scope: `connections:write`
- Copy the token (starts with `xapp-`)

### Install App

Go to **Install App** → **Install to Workspace**

Copy the **Bot User OAuth Token** (starts with `xoxb-`)

## Step 2: Get API Keys

### Anthropic (Required)
1. Go to [console.anthropic.com](https://console.anthropic.com)
2. Get your API key

### DocuSign (Optional - for sending contracts)
1. Go to [developers.docusign.com](https://developers.docusign.com)
2. Create developer account
3. Create an app, get Integration Key
4. Follow OAuth flow to get access token

### Stripe (Optional - for invoicing)
1. Go to [dashboard.stripe.com/developers](https://dashboard.stripe.com/developers)
2. Copy your Secret Key (use test key for demo)

## Step 3: Set Environment Variables

```bash
# Required
export SLACK_BOT_TOKEN="xoxb-your-bot-token"
export SLACK_APP_TOKEN="xapp-your-app-token"
export ANTHROPIC_API_KEY="sk-ant-your-key"

# Optional (for full demo)
export DOCUSIGN_ACCESS_TOKEN="your-token"
export DOCUSIGN_ACCOUNT_ID="your-account-id"
export STRIPE_SECRET_KEY="sk_test_your-key"
```

Or create a `.env` file:

```bash
SLACK_BOT_TOKEN=xoxb-...
SLACK_APP_TOKEN=xapp-...
ANTHROPIC_API_KEY=sk-ant-...
```

## Step 4: Run the Bot

```bash
cd /Users/daleyarborough/Code/prodway/apps/sowflow

# Install dependencies
pip install -r requirements.txt

# Run
python main.py
```

You should see:
```
⚡ Starting SowFlow Slack Bot...
   Use /sow <description> to generate a Statement of Work
```

## Step 5: Test It!

In any Slack channel, type:

```
/sow K8s migration for funded startup, currently on EC2 with 50k daily users,
need infrastructure to scale to 500k. Looking for 6 week timeline.
```

You should get a formatted SOW with:
- Executive Summary
- Scope of Work
- Deliverables
- Timeline
- Pricing
- Action buttons: Send | Edit | Dismiss

## Demo Script

For the perfect demo:

1. **Show the pain**: "Normally this takes 2-3 hours..."
2. **Type the command**: `/sow [description]`
3. **Wait 5 seconds**: SOW appears
4. **Click through**: Show the buttons work
5. **Reveal**: "From Slack message to signed contract in under 60 seconds"

## Troubleshooting

### "Dispatch failed" error
- Make sure Socket Mode is enabled
- Check that `SLACK_APP_TOKEN` starts with `xapp-`

### "Invalid auth" error
- Verify `SLACK_BOT_TOKEN` starts with `xoxb-`
- Make sure the app is installed to the workspace

### No response from /sow
- Check the terminal for errors
- Verify the bot is running
- Make sure Claude API key is valid

### Claude errors
- Check API key is valid
- Verify you have credits/quota

## Next Steps

1. **Add DocuSign**: Enable the "Send to Client" button
2. **Add Stripe**: Auto-generate invoices
3. **Customize templates**: Edit the SOW format in `main.py`
4. **Add to team**: Invite others to test
