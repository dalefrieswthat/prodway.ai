# SowFlow Quick Start

Get the `/sow` Slack command running in 5 minutes.

## Step 1: Get API Keys

### Anthropic API Key
1. Go to [console.anthropic.com](https://console.anthropic.com)
2. Sign up/login
3. Navigate to **API Keys**
4. Click **Create Key**
5. Copy the key (starts with `sk-ant-`)

### Slack App Setup
1. Go to [api.slack.com/apps](https://api.slack.com/apps)
2. Click **Create New App** → **From scratch**
3. Name: `SowFlow`, Workspace: your workspace
4. **OAuth & Permissions** → Add Bot Token Scopes:
   - `chat:write`
   - `commands`
   - `users:read`
5. **Slash Commands** → Create:
   - Command: `/sow`
   - Description: `Generate a Statement of Work`
   - Usage Hint: `[project description]`
6. **Socket Mode** → Enable:
   - Toggle on "Enable Socket Mode"
   - Generate App-Level Token with `connections:write` scope
7. **Install App** → Install to workspace
8. Copy:
   - **Bot User OAuth Token** (starts with `xoxb-`)
   - **App-Level Token** (starts with `xapp-`)

## Step 2: Setup Local Environment

```bash
cd apps/sowflow
./setup-local.sh
```

Or manually:

```bash
cd apps/sowflow
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## Step 3: Add Your Keys

Edit `.env` and add:

```bash
ANTHROPIC_API_KEY=sk-ant-your-key-here
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_APP_TOKEN=xapp-your-app-token
```

## Step 4: Run the Bot

```bash
source .venv/bin/activate
python main.py
```

You should see:
```
⚡ Starting SowFlow Slack Bot...
⚡ Bolt app is running!
```

## Step 5: Test in Slack

In any Slack channel, type:

```
/sow Need K8s migration for startup, 50k users scaling to 500k, 6 weeks
```

The bot will respond with a generated SOW!

---

## Troubleshooting

**Bot not responding?**
- Check that Socket Mode is enabled in Slack app settings
- Verify `SLACK_APP_TOKEN` is correct (starts with `xapp-`)
- Check bot logs for errors

**API errors?**
- Verify `ANTHROPIC_API_KEY` is correct
- Check your Anthropic account has credits

**Import errors?**
- Make sure virtual environment is activated: `source .venv/bin/activate`
- Reinstall: `pip install -r requirements.txt`
