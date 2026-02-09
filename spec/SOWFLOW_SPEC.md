# SowFlow AI - Product Specification

## Vision

The AI-powered deal engine for technical consultants and agencies. From client request to signed contract to invoice - in minutes, not days.

## One-Liner

> "Close contracts in minutes. AI scopes, drafts, and sends SOWs from a single Slack command."

---

## The Problem

Technical consultants and agencies lose deals because:

1. **Slow Response Time** - Client asks on Monday, SOW arrives Thursday, they've moved on
2. **Inconsistent Scoping** - Every SOW is written from scratch, quality varies
3. **Admin Overhead** - 2-3 hours to draft, format, send, follow up per deal
4. **No Institutional Memory** - Past projects don't inform future scoping
5. **Fragmented Tools** - Slack → Docs → DocuSign → Stripe → Linear = chaos

**Result:** Consultants leave $100K+ on the table annually from slow/missed deals.

---

## The Solution

**One command. Complete deal flow.**

```
/sow Need help migrating from EC2 to K8s. 
     Currently 50k daily users, need to scale to 500k. 
     Timeline: 6 weeks.
```

**Output in 10 seconds:**
- Analyzed scope with recommended approach
- Draft SOW with milestones and pricing
- One-click to send via DocuSign
- Auto-generated Stripe/Mercury invoice
- Project scaffolded in Linear/Jira

---

## Core Workflows

### Workflow 1: SOW Generation

```
INPUT (Slack or Web):
├── Client context (company, current stack, goals)
├── Project requirements (what they asked for)
└── Constraints (timeline, budget hints)

PROCESSING:
├── RAG: Find similar past projects
├── Analysis: Scope complexity, risk factors
├── Pricing: Based on your historical rates + complexity
└── Generation: Full SOW from your templates

OUTPUT:
├── Executive Summary
├── Scope of Work (detailed tasks)
├── Deliverables
├── Timeline with milestones
├── Pricing (fixed, hourly, or hybrid)
├── Terms and conditions
└── Signature blocks
```

### Workflow 2: Contract Execution

```
REVIEW (Slack interactive or Web UI):
├── Edit any section inline
├── Adjust pricing/timeline
├── Add custom clauses
└── Approve final version

SEND:
├── Generate PDF from your branded template
├── Push to DocuSign with client email
├── Track: Sent → Viewed → Signed
└── Notify in Slack on each status change

PAYMENT:
├── On signature: Generate invoice
├── Mercury: ACH payment request
├── Stripe: Payment link with card option
├── Split: 50/50, milestone-based, custom
└── Auto-reconcile when paid
```

### Workflow 3: Project Kickoff

```
ON SIGNATURE:
├── Create project in Linear/Jira/Asana
├── Generate tasks from SOW milestones
├── Set due dates based on timeline
├── Invite client to project (optional)
└── Schedule kickoff meeting (Calendly/Cal.com)

ONGOING:
├── Track milestone completion
├── Auto-invoice on milestone delivery
├── Generate progress reports
└── Flag scope creep risks
```

---

## Integrations

### Required (MVP)
| Integration | Purpose | Auth Method |
|------------|---------|-------------|
| **Slack** | Primary interface, notifications | OAuth |
| **Google Docs** | Template storage, export | OAuth |
| **DocuSign** | E-signatures | OAuth |
| **Stripe** | Payment links, invoicing | OAuth |

### Phase 2
| Integration | Purpose | Auth Method |
|------------|---------|-------------|
| **Mercury** | ACH invoicing for larger deals | API Key |
| **Linear** | Project creation | OAuth |
| **Notion** | Alternative template storage | OAuth |
| **QuickBooks** | Accounting sync | OAuth |

### Phase 3
| Integration | Purpose | Auth Method |
|------------|---------|-------------|
| **HubSpot/Pipedrive** | CRM sync | OAuth |
| **Calendly** | Meeting scheduling | OAuth |
| **Loom** | Video proposal embeds | OAuth |

---

## AI Components

### 1. Scope Analyzer

```python
# Input: Client request + your past projects
# Output: Structured scope assessment

{
    "complexity": "medium",  # low, medium, high, enterprise
    "estimated_hours": 120,
    "risk_factors": ["external API dependency", "unclear requirements"],
    "similar_projects": ["ourfirm-k8s-migration", "acme-infra-overhaul"],
    "recommended_approach": "Phase 1: Assessment, Phase 2: Migration, Phase 3: Optimization",
    "confidence": 0.85
}
```

### 2. Pricing Engine

```python
# Input: Scope analysis + your rate history + market data
# Output: Pricing recommendation

{
    "recommended_price": 32000,
    "price_range": {"low": 25000, "high": 40000},
    "basis": "Similar project for ClientX was $28K, +15% for complexity",
    "hourly_equivalent": 267,  # $/hr
    "payment_structure": {
        "upfront": 0.5,
        "milestone_1": 0.25,
        "completion": 0.25
    }
}
```

### 3. SOW Generator

```python
# Input: Scope + pricing + your templates + past SOWs
# Output: Complete SOW document

{
    "title": "Kubernetes Migration & Infrastructure Scaling",
    "client": "Acme Corp",
    "sections": {
        "executive_summary": "...",
        "scope": [...],
        "deliverables": [...],
        "timeline": [...],
        "pricing": {...},
        "terms": "...",
    },
    "generated_at": "2026-02-09T...",
    "confidence": 0.92,
    "sources_used": ["past_sow_123", "template_k8s"]
}
```

### 4. Pattern Learner

```python
# Continuously learns from:
# - Approved vs rejected drafts
# - Edit patterns (what you always change)
# - Win/loss on sent SOWs
# - Client feedback

# Improves:
# - Pricing accuracy
# - Scope estimation
# - Template selection
# - Risk identification
```

---

## Data Model (Additions)

```sql
-- SOW Templates
CREATE TABLE sow_templates (
    id UUID PRIMARY KEY,
    org_id UUID REFERENCES organizations(id),
    name VARCHAR(255),
    category VARCHAR(100),  -- k8s, cicd, security, etc.
    content JSONB,  -- structured template
    variables TEXT[],  -- {{client_name}}, {{timeline}}, etc.
    usage_count INTEGER DEFAULT 0,
    win_rate FLOAT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Generated SOWs
CREATE TABLE sows (
    id UUID PRIMARY KEY,
    org_id UUID REFERENCES organizations(id),
    template_id UUID REFERENCES sow_templates(id),
    client_name VARCHAR(255),
    client_email VARCHAR(255),
    
    -- Content
    title VARCHAR(255),
    content JSONB,
    pricing JSONB,
    
    -- AI metadata
    scope_analysis JSONB,
    confidence FLOAT,
    sources_used TEXT[],
    
    -- Status tracking
    status VARCHAR(50),  -- draft, sent, viewed, signed, rejected
    docusign_envelope_id VARCHAR(255),
    
    -- Financials
    total_value DECIMAL(12,2),
    payment_structure JSONB,
    stripe_invoice_id VARCHAR(255),
    mercury_invoice_id VARCHAR(255),
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    sent_at TIMESTAMP WITH TIME ZONE,
    viewed_at TIMESTAMP WITH TIME ZONE,
    signed_at TIMESTAMP WITH TIME ZONE,
    paid_at TIMESTAMP WITH TIME ZONE
);

-- Project tracking (post-signature)
CREATE TABLE projects (
    id UUID PRIMARY KEY,
    org_id UUID REFERENCES organizations(id),
    sow_id UUID REFERENCES sows(id),
    
    name VARCHAR(255),
    external_id VARCHAR(255),  -- Linear/Jira ID
    external_url VARCHAR(500),
    
    milestones JSONB,
    current_milestone INTEGER DEFAULT 0,
    
    status VARCHAR(50),  -- active, completed, paused, cancelled
    
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE
);
```

---

## Slack Commands

```
/sow [description]
  → Generate new SOW from description

/sow list
  → Show pending SOWs and their status

/sow view [id]
  → Preview a draft SOW

/sow send [id]
  → Send SOW via DocuSign

/sow template [name]
  → Use a specific template

/sow history
  → Show past signed SOWs and revenue
```

---

## Metrics & Analytics

### For Users (Dashboard)
- Total contract value (MTD, YTD)
- Average deal size
- Time from request to signature
- Win rate on sent SOWs
- Revenue by client/project type

### For Us (Growth)
- SOWs generated per user
- Conversion: Generated → Sent → Signed
- Contract value flowing through platform
- Feature adoption (which integrations used)
- Time saved (vs manual baseline)

---

## Pricing

### Free Tier
- 3 SOWs per month
- Basic templates
- Slack integration only
- Manual DocuSign/payments

### Pro ($149/month)
- Unlimited SOWs
- Custom templates
- DocuSign integration
- Stripe integration
- Analytics dashboard

### Team ($99/user/month, min 3)
- Everything in Pro
- Team templates & sharing
- Client relationship tracking
- Mercury integration
- API access

### Enterprise (Custom)
- Everything in Team
- SSO/SAML
- Custom integrations
- Dedicated support
- SLA guarantee

---

## Competitive Advantage

| Competitor | What They Do | Why We Win |
|------------|-------------|------------|
| **PandaDoc** | Generic proposals | We understand technical scope |
| **Proposify** | Beautiful templates | We generate content, not just format |
| **HoneyBook** | Creative freelancers | We're built for technical services |
| **Bonsai** | Freelancer tools | We're end-to-end, not just contracts |
| **Manual process** | Google Docs + DocuSign | We're 10x faster with better pricing |

**Our Moat:**
1. Technical scoping expertise (DevOps-specific initially)
2. Learning from your past projects (RAG on your SOWs)
3. Complete workflow (not just one step)
4. Pricing intelligence (market + your data)

---

## Roadmap

### Month 1-2: MVP
- [ ] Slack /sow command
- [ ] Basic scope analysis
- [ ] Template-based generation
- [ ] Manual review flow
- [ ] DocuSign integration

### Month 3-4: Payments
- [ ] Stripe invoice generation
- [ ] Payment tracking
- [ ] Mercury integration
- [ ] Win/loss tracking

### Month 5-6: Intelligence
- [ ] Pattern learning from edits
- [ ] Pricing recommendations
- [ ] Similar project matching
- [ ] Risk scoring

### Month 7-8: Scale
- [ ] Team features
- [ ] Project kickoff automation
- [ ] Analytics dashboard
- [ ] API for custom integrations

---

## Why This Wins at Demo Day

1. **Clear Problem**: "Consultants lose deals because they're slow"
2. **Magical Demo**: Slack command → SOW → DocuSign → Invoice in 60 seconds
3. **Revenue Tied**: "Our users closed $X in contracts through us"
4. **Defensible**: Workflow + integrations + learning = hard to replicate
5. **Expandable**: Start DevOps → any technical service → all B2B services
