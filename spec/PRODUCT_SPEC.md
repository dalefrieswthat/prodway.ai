# Context Engine - Product Specification

## Vision

A personal AI platform that learns from your communication patterns, code style, and workflows across all your tools - enabling you to scale your consultancy through AI agents rather than headcount.

## Problem Statement

As a solo DevOps consultant:
- You spend 40%+ of time on communication (Slack, email, updates)
- Your unique value is your experience and patterns, not typing speed
- Scaling requires hiring, but training people to "think like you" takes months
- Context is scattered across Slack, Notion, GitHub, Gmail, LinkedIn

## Solution

An AI-powered "digital twin" that:
1. **Captures** your patterns across all platforms
2. **Learns** your communication style, code patterns, decision-making
3. **Drafts** responses, updates, code reviews in your voice
4. **Scales** by handling routine work with human-in-the-loop approval

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     CONTEXT ENGINE                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │   Ingestors  │    │   Storage    │    │   Agents     │       │
│  │              │    │              │    │              │       │
│  │  - Slack     │───▶│  - Postgres  │───▶│  - Drafter   │       │
│  │  - GitHub    │    │  - Pinecone  │    │  - Reviewer  │       │
│  │  - Gmail     │    │  - S3        │    │  - Updater   │       │
│  │  - Notion    │    │              │    │              │       │
│  │  - LinkedIn  │    └──────────────┘    └──────────────┘       │
│  │  - Cursor    │           │                   │               │
│  └──────────────┘           │                   │               │
│                             ▼                   ▼               │
│                    ┌──────────────────────────────┐             │
│                    │         AI Core              │             │
│                    │  - Claude API (reasoning)    │             │
│                    │  - Embeddings (semantic)     │             │
│                    │  - RAG Pipeline (context)    │             │
│                    └──────────────────────────────┘             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Core Features

### Phase 1: Context Collection (MVP)

| Feature | Description | Priority |
|---------|-------------|----------|
| Cursor Context Watcher | Monitor cursor-context folders across projects | P0 |
| Slack Export Ingestion | Parse and embed Slack exports | P0 |
| GitHub Activity Sync | Commits, PRs, reviews → embeddings | P1 |
| Gmail Export Ingestion | Email patterns and templates | P1 |
| Notion Sync | SOPs, docs, processes | P2 |

### Phase 2: AI Drafting

| Feature | Description | Priority |
|---------|-------------|----------|
| Slack Draft Bot | "Draft response like Dale" | P0 |
| Email Draft Assistant | Generate emails in your style | P1 |
| PR Review Bot | Code reviews matching your patterns | P1 |
| Daily Update Generator | Auto-draft standup updates | P2 |

### Phase 3: Autonomous Agents

| Feature | Description | Priority |
|---------|-------------|----------|
| Client Update Agent | Send approved updates automatically | P0 |
| Triage Agent | Categorize and prioritize incoming messages | P1 |
| Proposal Generator | Draft SOWs based on past proposals | P1 |
| Meeting Prep Agent | Generate briefs from context | P2 |

---

## Technical Decisions

### Stack

| Component | Technology | Rationale |
|-----------|------------|-----------|
| **Language** | Python 3.12 | Best AI/ML ecosystem |
| **Framework** | FastAPI | Async, typed, fast |
| **Database** | PostgreSQL | Structured data, JSONB |
| **Vector Store** | Pinecone | Managed, scalable |
| **AI Provider** | Anthropic Claude | Best reasoning, safe |
| **Queue** | Redis + Celery | Background jobs |
| **Storage** | S3 | Raw exports, backups |
| **Deployment** | Docker + K8s | You know this well |

### Data Model

```
Projects
├── id, name, path
├── cursor_context_path
└── last_synced_at

Messages (from all sources)
├── id, source (slack|github|gmail|notion)
├── content, embedding
├── author, timestamp
├── project_id (optional)
└── metadata (JSONB)

Patterns (learned)
├── id, type (communication|code|decision)
├── description, examples
├── embedding
└── frequency, confidence

Agents
├── id, name, type
├── system_prompt
├── context_sources[]
└── approval_required (bool)
```

---

## API Design

### Ingest Endpoints

```
POST /api/v1/ingest/slack
POST /api/v1/ingest/github
POST /api/v1/ingest/gmail
POST /api/v1/ingest/notion
POST /api/v1/ingest/cursor-context
```

### Agent Endpoints

```
POST /api/v1/agents/draft
  body: { context: string, type: "slack" | "email" | "pr-review" }
  returns: { draft: string, confidence: float, sources: [] }

POST /api/v1/agents/approve
  body: { draft_id: string, approved: bool, edits?: string }

GET /api/v1/agents/pending
  returns: { drafts: [] }
```

### Context Endpoints

```
GET /api/v1/context/search
  query: { q: string, sources?: [], limit?: int }
  returns: { results: [], embeddings_used: int }

GET /api/v1/context/patterns
  returns: { patterns: [] }
```

---

## Project Structure

```
context-engine/
├── spec/                    # Specifications (you are here)
│   ├── PRODUCT_SPEC.md
│   ├── API_SPEC.md
│   └── DATA_SPEC.md
├── src/
│   ├── api/                 # FastAPI routes
│   ├── ingestors/           # Platform connectors
│   │   ├── slack.py
│   │   ├── github.py
│   │   ├── gmail.py
│   │   ├── notion.py
│   │   └── cursor_context.py
│   ├── agents/              # AI agents
│   │   ├── drafter.py
│   │   ├── reviewer.py
│   │   └── updater.py
│   ├── storage/             # Database & vector store
│   │   ├── postgres.py
│   │   └── pinecone.py
│   ├── ai/                  # AI/LLM integration
│   │   ├── claude.py
│   │   ├── embeddings.py
│   │   └── rag.py
│   └── core/                # Shared utilities
│       ├── config.py
│       └── models.py
├── tests/
├── scripts/                 # CLI tools
│   ├── sync_slack.py
│   ├── sync_github.py
│   └── train_patterns.py
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── k8s/                     # You know what this is for
├── .env.example
├── pyproject.toml
└── README.md
```

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Time saved on comms | 50%+ | Track drafts approved vs written |
| Draft acceptance rate | 80%+ | Approved without major edits |
| Context retrieval accuracy | 90%+ | Relevant sources returned |
| Response latency | < 3s | Time from request to draft |

---

## Milestones

### Week 1-2: Foundation
- [ ] Project scaffold
- [ ] PostgreSQL + Pinecone setup
- [ ] Cursor context watcher (local)
- [ ] Basic embedding pipeline

### Week 3-4: Ingestion
- [ ] Slack export ingestion
- [ ] GitHub activity sync
- [ ] First RAG queries working

### Week 5-6: Drafting
- [ ] Slack draft bot
- [ ] Human-in-the-loop approval flow
- [ ] First "production" drafts

### Week 7-8: Polish
- [ ] Gmail integration
- [ ] Notion sync
- [ ] Dashboard for approvals
- [ ] Deploy to K8s

---

## Security Considerations

- All credentials in AWS Secrets Manager
- Data encrypted at rest (RDS, S3)
- API keys rotated monthly
- Audit log for all agent actions
- Human approval required for external sends (initially)

---

## Open Questions

1. Should LinkedIn be real-time or periodic sync?
2. Fine-tune a model or rely purely on RAG?
3. Self-host embeddings or use OpenAI/Voyage?
4. Mobile app for approvals or web-only?
