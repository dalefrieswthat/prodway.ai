# Prodway AI - Project Context

## Company
Prodway AI builds AI tools for service businesses to scale without headcount.
Products: **SowFlow** (Slack SOW generation + DocuSign + Stripe) and **FormPilot** (Chrome form auto-fill).
Domain: prodway.ai. Target: funded startups (YC, Antler, a16z).

## Code Search
Prefer grepika MCP tools over built-in Grep/Glob for code search:
- `mcp__grepika__search` - Pattern/regex/NLP search (replaces Grep)
- `mcp__grepika__toc` - Directory tree (replaces Glob patterns)
- `mcp__grepika__outline` - File structure extraction
- `mcp__grepika__refs` - Symbol references
Run `mcp__grepika__index` first if results seem stale.

## Repo Layout
- `apps/sowflow/` - SowFlow API (FastAPI, Slack Bolt OAuth, Claude, DocuSign, Stripe)
- `apps/formpilot/` - Chrome extension (Manifest V3)
- `apps/web/static-deploy/` - Landing page (GitHub Pages -> prodway.ai)
- `cursor-context/` - Specs, investor docs, setup guides (see README.md inside)
- `k8s/base/` - Kubernetes manifests (future)

## Dev Workflow
```bash
cd apps/sowflow && python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && cp ../../ENV_TEMPLATE.txt .env
python main.py  # FastAPI on port 3000
```

## Deployment
- Landing: GitHub Pages (push to main auto-deploys)
- API: Railway (`railway up`), target: api.prodway.ai
- Slack: OAuth HTTP mode (not Socket Mode)

## Standards
- Python: type hints, docstrings
- HTML/CSS: semantic, mobile-first, dark theme
- Git: **concise** commits (`feat: add X`, `fix: Y`, `refactor: Z`)
- Never add Co-authored-by Cursor trailers
- Design quality: Airbnb standard

## Deeper Context
See `cursor-context/` for: product specs, investor positioning, integration strategy, setup guides.
