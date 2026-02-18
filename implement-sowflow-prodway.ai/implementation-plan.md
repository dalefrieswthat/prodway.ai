# Implementation plan: Prodway SOW + invoice API

**Goal:** Implement the API spec (create SOW, trigger invoice with Stripe) so OpenClaw and other tools can call Prodway.

---

## Prerequisites (before coding)

- [x] Confirm Prodway stack (framework, DB, existing SOW/invoice models if any).
- [x] Confirm where Stripe credentials are stored (env, DB per workspace, etc.).

---

## Phase 1: Backend API (Prodway)

### 1.1 Routes and controllers

- [x] Add `POST /api/sows` — validate body, persist SOW, return response shape from spec.
- [x] Add `POST /api/invoices` — validate body; if `sowId` present load SOW and derive line items; call Stripe adapter; persist invoice record; return response shape.
- [x] Add `POST /api/sows/with-invoice` — create SOW then create invoice in one sequence; return `{ sow, invoice }`.

### 1.2 Auth

- [x] Enforce `Authorization: Bearer <token>` on these routes.
- [x] Resolve token to workspace (and optionally user); use for scoping and for looking up Stripe credentials.

### 1.3 Stripe integration

- [x] Implement adapter/service: given workspace credentials + invoice payload, call Stripe API to create invoice (and payment link if `collectPayment`).
- [x] Map Stripe response to common response shape (`id`, `status`, `invoiceUrl`, `paymentUrl`).
- [x] Handle errors and map to `402`/`422` with optional `providerError`.

### 1.4 Data and persistence

- [x] Ensure SOW and Invoice entities exist; add fields if spec requires (e.g. `viewUrl`, `editUrl`, `paymentUrl`).
- [x] Store provider-specific ids (e.g. Stripe `inv_xxx`) for idempotency or status sync if needed later.

---

## Phase 2: API key / token issuance

- [ ] Provide a way to create API tokens for a workspace (e.g. settings page or admin endpoint).
- [ ] Document how to get a token for OpenClaw (or any tool).

---

## Phase 3: OpenClaw integration (optional, after API works)

- [ ] Add a custom OpenClaw tool (or plugin) that calls Prodway:
  - Tool 1: `create_sow` — params: title, clientName, lineItems, etc.; calls `POST /api/sows`.
  - Tool 2: `create_invoice` — params: sowId or lineItems, customer, etc.; calls `POST /api/invoices`.
- [ ] Store Prodway API base URL and token in OpenClaw config or env; tool uses them for requests.

---

## Files modified

- `apps/sowflow/main.py` — SOW + invoice endpoints, Stripe adapter, auth middleware.

---

## Success criteria

- [x] `POST /api/sows` creates a SOW and returns spec response.
- [x] `POST /api/invoices` creates invoice in Stripe and returns spec response.
- [x] All endpoints require valid Bearer token and scope to workspace.
