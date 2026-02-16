# Integrations (OpenClaw, etc.) & Data Moat

> How Prodway stays integratable with agent frameworks and builds a defensible data moat for investors/accelerators.

---

## 1. Why OpenClaw and “agent-ready” matters

**OpenClaw** (and similar tools—n8n, LangChain agents, custom RPA) do:

- Browser control, form filling, multi-channel (Slack, WhatsApp, etc.)
- Persistent memory and skills/plugins
- Automation that runs continuously on behalf of users

**Prodway’s angle:** We own **company/customer context** (who you are, what you do, one-pagers, YC answers). Agents need that same context to fill forms, draft SOWs, and personalize outreach. If we expose it via a **stable API + optional shared DB**, we become the **company-data layer** those agents call—integratable by design.

---

## 2. What “easily integratable” requires

### 2.1 API-first, documented contract

| Requirement | What we do |
|------------|------------|
| **Stable REST/API** | FormPilot API already: `POST /formpilot/suggest-mappings`, `POST /formpilot/import-from-url`. Add: `GET/PUT /v1/orgs/:id/profile`, `GET/PUT /v1/orgs/:id/context` so OpenClaw (or any client) can read/write profile + context without going through the extension. |
| **Auth** | API key or OAuth per org/workspace so agents can act on behalf of a “team” or “company.” |
| **Webhooks (optional)** | Notify external systems when profile/context is updated, or when a form was filled (event payload). Enables OpenClaw to keep its own cache in sync. |
| **Open schema** | Publish a small JSON schema for “company profile” and “company context” so integrators know the shape. |

No shared DB is strictly required for **integratable**: the integrator (OpenClaw, n8n, etc.) calls our API and we can still store only in our DB. Shared DB is an option only if we want to co-deploy or run their stack; see below.

### 2.2 OpenClaw specifically

- **Skill/plugin**: OpenClaw can add a “Prodway” skill that (a) calls our API to get profile + context, (b) uses our suggest-mappings for form-fill tasks, (c) optionally pushes updated context back after a run. We only need the API; no need to run OpenClaw ourselves.
- **Browser + form fill**: OpenClaw already does browser control. We don’t replace that; we provide **what to fill** (mappings) and **with what** (profile + context). So: OpenClaw drives the browser, we drive the data.

**Concrete next steps for “OpenClaw-ready”:**

1. Add **org-scoped profile/context API** (see §3).
2. Add **API key** (or OAuth) for server-to-server (e.g. OpenClaw backend calling us).
3. Document the contract (OpenAPI + a short “Integrating with Prodway” page).
4. Optionally: an **OpenClaw skill** in their repo that calls our API (we can publish a minimal example).

---

## 3. Shared DB and storing more customer data

### 3.1 Why a shared DB / central store helps

Today:

- **SowFlow**: team-level integrations (DocuSign, Stripe) and SOWs in file/DB per deployment.
- **FormPilot**: profile + context in Chrome `storage.local` (no central copy unless we add one).

To be **integratable** and **moat-building**, we want:

- **One place** where “company profile” and “company context” live per customer/org.
- **All products** (SowFlow, FormPilot, future) and **all integrators** (OpenClaw, Zapier, etc.) read/write that same store via API.

That implies a **shared DB** (or at least a shared “profile/context” service and schema) for Prodway—not necessarily a DB shared with OpenClaw’s own infra. OpenClaw talks to us over HTTPS; we persist in our DB.

### 3.2 Suggested data model (minimal, moat-friendly)

- **Orgs (or “workspaces”)**
  One per customer/team. Id, name, slug, created_at, settings (e.g. default timezone).

- **Company profile (structured)**
  One per org: company name, contact name, email, phone, website, address, city, state, zip, country, LinkedIn URL, short description, etc. (what FormPilot already has in options). Stored in DB so API can serve it to FormPilot, SowFlow, and agents.

- **Company context (unstructured)**
  One per org: long-form text (one-pager, YC answers, investor memo). Used for AI mapping and long-form fields. Stored in DB; API: GET/PUT body or chunked if we add RAG later.

- **Usage / events (optional but strong for moat)**
  - Form fill events: org_id, timestamp, domain/page (or hash), number of fields filled, success/fail.
  - SOW events: org_id, created/sent/signed, time-to-send.
  This powers: “teams like yours…”, better defaults, and defensible analytics that accelerators like.

- **Integrations**
  Existing: Slack workspace id, DocuSign/Stripe tokens per org. Add: API keys or OAuth clients for programmatic access (OpenClaw, etc.).

No need to store raw form HTML or PII beyond what’s in profile; keep events aggregated or pseudonymized where possible.

### 3.3 What this requires of us

| Piece | Requirement |
|-------|--------------|
| **DB** | Postgres (or existing DB) with tables for orgs, profile, context, and optionally events. Migrations and a single “profile/context” service (or routes in existing API). |
| **Auth** | Org-scoped API keys (or OAuth2 client credentials) so OpenClaw/agents can act as “this org.” |
| **FormPilot** | Extension continues to work offline with local storage; when user is “logged in” or has linked org, extension syncs profile/context from API and pushes updates back. Optional first release: API-only, extension still local-only. |
| **SowFlow** | Already has team/workspace; map that to same org id so SOWs and FormPilot share one profile/context. |

---

## 4. Defensible moat (what investors/accelerators look for)

- **Data moat**
  Central profile + context + usage (with consent) lets us: (1) improve AI (e.g. better field mapping, SOW quality), (2) surface insights (“teams that fill YC applications use these fields most”), (3) build vertical-specific defaults. The more products and integrators that write to our store, the more valuable the store becomes.

- **Integration moat**
  Being the **company-data layer** for FormPilot, SowFlow, and third-party agents (OpenClaw, Zapier) makes us infrastructure. Switching cost grows with usage and connected systems.

- **Single schema, multiple surfaces**
  One profile/context schema, served to: Chrome extension, Slack, future web app, and any agent. Same data, many distribution channels—clear story for scaling and partnerships.

---

## 5. Recommended order

1. **Short term (integratable without big DB)**
   - Add **read/write profile + context API** under a single “Prodway API” (or extend FormPilot API) with org/workspace id and API key auth.
   - Document the contract (OpenAPI + integration page).
   - FormPilot can stay local-only; agents and future products use the API.

2. **Next (shared DB)**
   - Introduce **orgs + profile + context** in Postgres (or current DB).
   - Migrate SowFlow “team” to same org id; FormPilot gets optional “sync with Prodway” using the same API.
   - Add **usage/events** (form fills, SOW created/sent) for analytics and moat.

3. **Then (deeper integrations)**
   - Webhooks for profile/context changes.
   - Example OpenClaw skill or n8n workflow that calls our API.
   - Optional: “Connect OpenClaw” in Prodway UI (OAuth or API key creation).

This keeps us **easily integratable with OpenClaw and similar technologies** (API-first, clear schema, auth) and builds toward a **shared DB and richer customer data** for more valuable insights and a defensible moat, without requiring OpenClaw to share our DB.
