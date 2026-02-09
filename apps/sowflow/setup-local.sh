#!/bin/bash
# Quick setup script for local SowFlow development

set -e

echo "🚀 Setting up SowFlow locally..."

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.12+"
    exit 1
fi

# Create virtual environment
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate and install
echo "📥 Installing dependencies..."
source .venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q

# Check for .env file
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found. Creating from template..."
    cp .env.example .env
    echo ""
    echo "📝 Please edit .env and add your API keys:"
    echo "   - ANTHROPIC_API_KEY (get from console.anthropic.com)"
    echo "   - SLACK_BOT_TOKEN (from Slack app settings)"
    echo "   - SLACK_APP_TOKEN (from Slack app settings)"
    echo ""
    echo "See KEYS_NEEDED.md for detailed setup instructions."
    exit 1
fi

# Validate required keys
source .env
missing_keys=()

if [ -z "$ANTHROPIC_API_KEY" ] || [ "$ANTHROPIC_API_KEY" = "sk-ant-your-api-key-here" ]; then
    missing_keys+=("ANTHROPIC_API_KEY")
fi

if [ -z "$SLACK_BOT_TOKEN" ] || [ "$SLACK_BOT_TOKEN" = "xoxb-your-bot-token-here" ]; then
    missing_keys+=("SLACK_BOT_TOKEN")
fi

if [ -z "$SLACK_APP_TOKEN" ] || [ "$SLACK_APP_TOKEN" = "xapp-your-app-token-here" ]; then
    missing_keys+=("SLACK_APP_TOKEN")
fi

if [ ${#missing_keys[@]} -gt 0 ]; then
    echo "❌ Missing required API keys in .env:"
    for key in "${missing_keys[@]}"; do
        echo "   - $key"
    done
    echo ""
    echo "Please update .env with your actual keys."
    exit 1
fi

echo "✅ Setup complete!"
echo ""
echo "To run the bot:"
echo "  source .venv/bin/activate"
echo "  python main.py"
echo ""
