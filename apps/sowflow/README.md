# SowFlow - AI-Powered SOW Generation

Generate Statements of Work from a single Slack command.

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

**Slash Commands** → Create:
- Command: `/sow`
- Request URL: (will use Socket Mode, so leave blank)
- Description: "Generate a Statement of Work"
- Usage Hint: "[project description]"

**Socket Mode** → Enable:
- Toggle on "Enable Socket Mode"
- Generate an App-Level Token with `connections:write` scope
- Save this as `SLACK_APP_TOKEN`

**Install App**:
- Go to "Install App" and install to your workspace
- Copy the "Bot User OAuth Token" as `SLACK_BOT_TOKEN`

### 3. Set Environment Variables

```bash
export SLACK_BOT_TOKEN="xoxb-your-bot-token"
export SLACK_APP_TOKEN="xapp-your-app-token"
export ANTHROPIC_API_KEY="sk-ant-your-key"
```

### 4. Run the Bot

```bash
cd apps/sowflow
pip install -r requirements.txt
python main.py
```

### 5. Use It!

In any Slack channel:

```
/sow Need K8s migration for startup, currently on EC2 with 50k daily users,
need to scale to 500k. Timeline: 6 weeks.
```

## Features

- **AI-Powered Scoping**: Claude analyzes your description and generates appropriate scope
- **Smart Pricing**: Suggests pricing based on complexity
- **One-Click Actions**: Send, Edit, or Dismiss the generated SOW
- **Slack-Native**: Works right in your existing workflow

## Coming Soon

- [ ] DocuSign integration for e-signatures
- [ ] Stripe integration for invoicing
- [ ] Template customization
- [ ] SOW history and analytics
- [ ] Team collaboration
