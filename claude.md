# Prodway AI - Project Context

> **Last Updated:** February 2026  
> **Status:** Active Development

---

## Overview

Prodway AI builds AI tools for service businesses to scale without scaling headcount. We're a product company with two core offerings: **SowFlow** (SOW generation) and **FormPilot** (form auto-fill).

**Mission:** Eliminate busywork from consulting businesses through AI automation.

---

## Products

### SowFlow
- **Status:** MVP in development
- **Tech:** Python, Slack Bolt, Anthropic Claude, DocuSign, Stripe
- **Location:** `apps/sowflow/`
- **Purpose:** Generate Statements of Work from Slack commands (`/sow`)

### FormPilot
- **Status:** Planned
- **Tech:** Chrome Extension
- **Purpose:** Auto-fill forms with company data

---

## Architecture

```
prodway/
├── apps/
│   ├── sowflow/          # Slack bot (MVP)
│   └── web/              # Landing page (static HTML)
├── packages/
│   ├── integrations/     # DocuSign, Stripe
│   └── shared/           # Common utilities
├── k8s/base/             # Kubernetes manifests
├── spec/                  # Product specifications
└── .github/workflows/     # CI/CD
```

**Deployment:**
- Landing page: GitHub Pages (`prodway.ai`)
- API: Railway (planned) / K8s (future)
- Images: GitHub Container Registry

---

## Tech Stack

**Backend:**
- Python 3.12+
- Slack Bolt (Socket Mode)
- Anthropic Claude API
- FastAPI (planned)

**Infrastructure:**
- GitHub Actions (CI/CD)
- Kubernetes (production-ready manifests)
- Docker

**Frontend:**
- Static HTML/CSS (landing page)
- No framework dependencies

---

## Key Decisions

1. **Monorepo structure** - All products under one repo for shared code
2. **Static landing page** - No build complexity, fast deploys
3. **Slack-first** - SowFlow starts as Slack bot, not web app
4. **K8s-ready** - Manifests prepared but not deployed yet
5. **Product positioning** - Focus on funded startups (YC, Antler, AZ16)

---

## Development Workflow

**Local Setup:**
```bash
cd apps/sowflow
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Environment Variables:**
- `SLACK_BOT_TOKEN` - Bot OAuth token
- `SLACK_APP_TOKEN` - App-level token (Socket Mode)
- `ANTHROPIC_API_KEY` - Claude API key

**Deployment:**
- Push to `main` → Auto-deploys landing page via GitHub Pages
- API deployment: Manual (Railway) or via K8s manifests

---

## Important Notes

**Branding:**
- Product name: **SowFlow** (not DealFlow)
- Company: **Prodway AI**
- Domain: `prodway.ai`

**Client Positioning:**
- We work with **companies backed by** YC, Antler, AZ16
- Not the VCs themselves
- Focus: Funded startups needing infrastructure/DevOps

**Current Status:**
- Landing page: ✅ Live at prodway.ai
- SowFlow: 🚧 MVP in development
- FormPilot: 📋 Planned

---

## Code Standards

- **Python:** Type hints, docstrings, clean functions
- **HTML/CSS:** Semantic HTML, mobile-first, dark theme
- **Git:** **VERY CONCISE** commit messages. Examples:
  - `feat: add trusted-by section`
  - `fix: update logo styling`
  - `refactor: rename DealFlow to SowFlow`
- **Documentation:** Keep it updated, keep it clean

---

## Future Work

- [ ] Complete SowFlow MVP
- [ ] Deploy API to Railway/K8s
- [ ] Add Stripe/DocuSign integrations
- [ ] Build FormPilot Chrome extension
- [ ] Add case studies page
- [ ] Set up proper secrets management (AWS Secrets Manager)

---

**Questions?** Check `spec/` folder for detailed product specs.
