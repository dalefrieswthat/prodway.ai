# Chat Q&A: Sowflow / FormPilot and OpenClaw integration

Summary of questions and answers from the planning conversation.

---

## Q: Would it make sense to integrate some of the sowflow features or formfilling of formpilot into openclaw?

**A:** Yes, but the integration point is **APIs**, not the Slack app or Chrome extension directly. OpenClaw uses **tools** — functions it can call (e.g. HTTP to your backend). So:

- **OpenClaw to Prodway:** OpenClaw calls Prodway APIs (e.g. create SOW, fill form, get status). That requires Prodway to expose APIs (REST, webhooks) that OpenClaw tools can call.
- **Prodway to OpenClaw:** Prodway could send events to OpenClaw (e.g. "SOW approved, notify user in Slack via OpenClaw").
- **Shared Slack:** If both have Slack apps in the same workspace, the clean path is still: Prodway exposes an API, OpenClaw has a tool that calls it. OpenClaw does not "pretend to be a Slack user" talking to your Slack app.
- **Chrome extension:** FormPilot in the browser can stay as-is. For OpenClaw-driven form filling, the clean path is a FormPilot backend API ("fill form X with data Y"); OpenClaw's tool calls that. Alternative is something driving the browser (e.g. Playwright) — more complex.

**What would make Prodway tool-friendly:**

1. **Stable APIs** for key actions (create/fill/approve/status).
2. **Webhooks** to notify external systems when something happens.
3. **Auth** (API keys or OAuth) so OpenClaw can authenticate.
4. **Docs** so tool authors can build "Prodway tools."

---

## Q: Let's get the exact api shape for being able to create the sow and trigger the invoice with Stripe. Can we do this even though Stripe already has its own API?

**A:** Yes. Stripe having its own API is why you put Prodway in the middle:

- **OpenClaw** (or any tool) only talks to **Prodway's API** (e.g. "create SOW", "trigger invoice").
- **Prodway's backend** then calls Stripe with your credentials and business logic. Callers never see or send Stripe keys.

So the "exact API shape" is for **Prodway's API**. That API would:

1. **Create SOW** — `POST /api/sows` with title, client, line items, etc.; returns SOW id, status, view/edit URLs.
2. **Trigger invoice** — `POST /api/invoices` with optional `sowId`, customer, line items (or from SOW), optional `collectPayment`; Prodway creates the invoice in Stripe and returns id, status, invoice URL, payment URL.

The full request/response shapes are in `api-spec.md`.

---

## Q: Let's create a plan for how we need to implement this work… save our spec file and implementation plan as well as this chat .md file with all my questions and your previous answers.

**A:** Created in `implement-sowflow-prodway.ai/`:

- **api-spec.md** — Exact API shape (create SOW, trigger invoice, optional SOW+invoice in one step).
- **implementation-plan.md** — Phased plan: backend API (routes, auth, Stripe adapter), token issuance, optional OpenClaw tool.
- **chat-qa.md** — This file: your questions and the answers above.
