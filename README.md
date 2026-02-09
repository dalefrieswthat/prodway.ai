# Prodway AI

**AI tools for service businesses to scale without scaling headcount.**

## Products

### 🚀 DealFlow
Generate SOWs, send contracts, invoice clients - all from Slack.

```
/sow K8s migration for startup, 50k users, scale to 500k, 6 weeks
```
→ Full SOW in 5 seconds → DocuSign → Stripe invoice

[→ apps/dealflow](./apps/dealflow)

### 📋 FormPilot (Coming Soon)
Chrome extension that auto-fills any form with your company data.

[→ apps/formpilot](./apps/formpilot)

---

## Quick Start

### DealFlow (Slack Bot)

```bash
# Set up environment
cd apps/dealflow
pip install -r requirements.txt

# Configure (see apps/dealflow/README.md for Slack app setup)
export SLACK_BOT_TOKEN="xoxb-..."
export SLACK_APP_TOKEN="xapp-..."
export ANTHROPIC_API_KEY="sk-ant-..."

# Run
python main.py
```

### Local Development Stack

```bash
# Start databases
cd docker
docker-compose up -d postgres redis qdrant

# Run API
cd ..
pip install -e .
uvicorn packages.api.main:app --reload
```

---

## Project Structure

```
prodway/
├── apps/
│   ├── dealflow/        # Slack SOW bot (MVP)
│   └── formpilot/       # Chrome extension (planned)
├── packages/
│   ├── ai/              # Claude + embeddings
│   ├── api/             # FastAPI backend
│   ├── core/            # Shared models, config
│   ├── ingestors/       # Slack, GitHub, etc.
│   ├── integrations/    # DocuSign, Stripe
│   └── shared/          # Common utilities
├── docker/              # Local dev stack
└── spec/                # Product specs
```

---

## The Vision

1. **Today**: Consulting services + AI tooling for myself
2. **Soon**: DealFlow as a product for other consultants  
3. **Future**: Full suite of AI tools for service businesses

**Revenue**: $30K signed, $40K pipeline (using these tools)

---

## Links

- Spec: [spec/DEALFLOW_SPEC.md](./spec/DEALFLOW_SPEC.md)
- Product Spec: [spec/PRODUCT_SPEC.md](./spec/PRODUCT_SPEC.md)
