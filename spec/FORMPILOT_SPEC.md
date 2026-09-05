# FormPilot — Product Specification

> **Status:** Production (Chrome Extension + API)  
> **Last Updated:** April 2026

---

## Overview

FormPilot is a Chrome extension that auto-fills web forms using AI and a company profile. Founders use it to rapidly complete YC applications, investor forms, and partnership questionnaires — fields are matched to profile data and filled in one click.

## Architecture

```
Chrome Extension (content script)
    ↓ POST /formpilot/suggest-mappings
FormPilot API (FastAPI)
    ↓ AI prompt (Gemini or Claude)
AI Provider
    ↓ JSON array of {index, value}
FormPilot API
    ↓ Validated mappings
Chrome Extension
    ↓ DOM injection
Form fields auto-filled
```

**Runtime:** FastAPI  
**AI:** Gemini gemma-3-4b-it (default, cheapest) or Anthropic Claude Haiku (fallback)  
**Auth:** Prodway API key (validated against SowFlow billing system)  
**Billing:** Included with $5/mo Prodway subscription  

## Core Workflows

### 1. Suggest Mappings (`POST /formpilot/suggest-mappings`)
1. Extension detects form fields on page (label, placeholder, name, semantic type)
2. Sends fields + company profile + optional context to API
3. AI generates value for each empty field
4. API validates: type checks (email, URL, phone), length constraints, semantic guards
5. Returns `{mappings: [{index, value}]}` — extension fills fields

### 2. Suggest Single Field (`POST /formpilot/suggest-field`)
1. User clicks a specific field for AI assistance
2. Sends field metadata + nearby fields (context) + profile
3. AI generates value + reasoning
4. Validation applied; returns `{value, reasoning}`

### 3. Import from URL (`POST /formpilot/import-from-url`)
1. User pastes a LinkedIn or company URL
2. API fetches page, strips HTML to text
3. AI extracts structured profile (company, contact, address) + context
4. Returns `{profile, context}` for extension to store

### 4. Health Check (`GET /formpilot/health`)
- Returns `{"status": "ok", "service": "formpilot-api"}`

### 5. Usage Stats (`GET /prodway/stats`, `POST /prodway/record-fill`, `POST /prodway/record-sow`)
- Aggregate counters for landing page metrics
- Consent-gated recording

## Validation Rules

### Type Validators
| Semantic Type | Validator | Rule |
|---------------|-----------|------|
| `email` | `_looks_like_email` | `user@domain.tld` pattern |
| `phone` | `_looks_like_phone` | 7-15 digits after stripping formatting |
| `website` | `_looks_like_url` | Starts with http(s):// or matches domain pattern |
| `linkedinUrl` | `_looks_like_linkedin_url` | Contains "linkedin" or looks like URL |
| `videoUrl` | `_looks_like_video_url` | Loom, YouTube, Vimeo, etc. domains |
| `pitchDeckUrl` | `_looks_like_url` | Any valid URL |

### Length Constraints
| Type | Min | Max |
|------|-----|-----|
| `shortDescription` | 20 | 500 |
| `description` | 50 | 5,000 |
| `companyName` | 1 | 200 |
| `firstName` | 1 | 50 |
| `zip` | 2 | 20 |

### Semantic Guards
- Company names rejected from person name fields (checks LLC, Inc, Corp suffixes)
- Person names rejected from URL fields
- Missing URLs omitted rather than guessed

## Authentication

FormPilot uses the **Prodway API key** model:
1. User subscribes via SowFlow Slack app ($5/mo)
2. API key generated in Slack App Home (`pw_` prefix)
3. Extension sends key via `X-API-Key` header or `Authorization: Bearer`
4. FormPilot API validates against SowFlow's `/api/validate-key`
5. Validation cached for 5 minutes (TTL)
6. Fail-open for `pw_` keys during SowFlow outages

## API Endpoints

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| POST | `/formpilot/suggest-mappings` | API Key | Batch field mapping |
| POST | `/formpilot/suggest-field` | API Key | Single field suggestion |
| POST | `/formpilot/import-from-url` | API Key | Extract profile from URL |
| GET | `/formpilot/health` | None | Health check |
| POST | `/prodway/record-fill` | None | Record form fill count |
| POST | `/prodway/record-sow` | None | Record SOW sent |
| GET | `/prodway/stats` | None | Aggregate usage stats |

## Data Model

FormPilot is stateless on the server side. All persistent data:
- Company profile → stored in Chrome extension local storage
- Subscription status → managed by SowFlow billing system
- Usage stats → `usage_db.py` (SQLite or JSON)
