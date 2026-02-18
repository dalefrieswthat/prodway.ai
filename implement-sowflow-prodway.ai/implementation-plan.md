# Implementation plan: Prodway SOW + invoice API

**Goal:** Implement the API spec (create SOW, trigger invoice with Mercury/Stripe) so OpenClaw and other tools can call Prodway. Target: sooner the better.

---

## Prerequisites (before coding)

- [ ] Confirm Prodway stack (framework, DB, existing SOW/invoice models if any).
- [ ] Confirm where Mercury and Stripe credentials are stored (env, DB per workspace, etc.).
- [ ] Get Mercury and Stripe API docs / SDKs for creating invoices and payment links.

---

## Phase 1: Backend API (Prodway)

### 1.1 Routes and controllers

- [ ] Add `POST /api/sows` — validate body, persist SOW, return response shape from spec.
- [ ] Add `POST /api/invoices` — validate body; if `sowId` present load SOW and derive line items; call Mercury or Stripe adapter based on `provider`; persist invoice record; return response shape.
- [ ] (Optional) Add `POST /api/sows/with-invoice` — create SOW then create invoice in one transaction or sequence; return `{ sow, invoice }`.

### 1.2 Auth

- [ ] Enforce `Authorization: Bearer <token>` on these routes.
- [ ] Resolve token to workspace (and optionally user); use for scoping and for looking up Mercury/Stripe credentials.

### 1.3 Mercury integration

- [ ] Implement adapter/service: given workspace credentials + invoice payload, call Mercury API to create invoice (and payment link if requested).
- [ ] Map Mercury response to common response shape (`id`, `status`, `invoiceUrl`, `paymentUrl`).
- [ ] Handle errors and map to `402`/`422` with optional `providerError`.

### 1.4 Stripe integration

- [ ] Implement adapter/service: given workspace credentials + invoice payload, call Stripe API to create invoice (and payment link if `collectPayment`).
- [ ] Map Stripe response to same common response shape.
- [ ] Handle errors and map to `402`/`422` with optional `providerError`.

### 1.5 Data and persistence

- [ ] Ensure SOW and Invoice (or equivalent) entities exist; add fields if spec requires (e.g. `viewUrl`, `editUrl`, `paymentUrl`).
- [ ] Store provider-specific ids (e.g. Stripe `inv_xxx`) for idempotency or status sync if needed later.

---

## Phase 2: API key / token issuance

- [ ] Provide a way to create API tokens for a workspace (e.g. settings page or admin endpoint).
- [ ] Document how to get a token for OpenClaw (or any tool).

---

## Phase 3: OpenClaw integration (optional, after API works)

- [ ] Add a custom OpenClaw tool (or plugin) that calls Prodway:
  - Tool 1: `create_sow` — params: title, clientName, lineItems, etc.; calls `POST /api/sows`.
  - Tool 2: `create_invoice` — params: provider (mercury | stripe), sowId or lineItems, customer, etc.; calls `POST /api/invoices`.
- [ ] Store Prodway API base URL and token in OpenClaw config or env; tool uses them for requests.

---

## Order of work (tomorrow)

1. **Morning:** Implement `POST /api/sows` (no Mercury/Stripe yet) — persistence, validation, response shape. Verify with curl/Postman.
2. **Midday:** Implement Mercury adapter (create invoice + optional payment link); then wire `POST /api/invoices` for `provider: "mercury"`. Test with real/sandbox Mercury.
3. **Afternoon:** Implement Stripe adapter; wire `POST /api/invoices` for `provider: "stripe"`. Test with Stripe test mode.
4. **Optional:** `POST /api/sows/with-invoice` and/or OpenClaw tool stubs.

---

## Files to create/modify (Prodway repo — adjust to your structure)

- New: `api/sows/routes.ts` (or equivalent) — SOW endpoints.
- New: `api/invoices/routes.ts` — Invoice endpoint.
- New: `services/mercury-invoice.ts` (or similar) — Mercury API client for invoices.
- New: `services/stripe-invoice.ts` — Stripe API client for invoices.
- New or extend: `middleware/auth.ts` — Bearer token validation and workspace resolution.
- Extend: SOW and Invoice models/migrations if needed for new fields.

---

## Success criteria

- [ ] `POST /api/sows` creates a SOW and returns spec response.
- [ ] `POST /api/invoices` with `provider: "mercury"` creates invoice in Mercury and returns spec response.
- [ ] `POST /api/invoices` with `provider: "stripe"` creates invoice in Stripe and returns spec response.
- [ ] All endpoints require valid Bearer token and scope to workspace.
