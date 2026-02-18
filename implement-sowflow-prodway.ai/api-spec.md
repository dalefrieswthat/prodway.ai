# Prodway API spec: SOW + invoice (Stripe)

API that Prodway exposes so tools like OpenClaw can create SOWs and trigger invoices. Prodway backend calls Stripe; callers never touch provider APIs directly.

**Auth:** `Authorization: Bearer <token>` (API key or OAuth2 access token per workspace).

---

## 1. Create SOW

**Endpoint:** `POST /api/sows` (or `POST /api/v1/sows`)

### Request body

| Field | Type | Required | Notes |
|-------|------|----------|--------|
| `title` | string | Yes | |
| `clientName` | string | Yes | |
| `clientEmail` | string | No | For sending |
| `description` | string | No | |
| `lineItems` | array | No | See line item shape below |
| `effectiveDate` | string | No | ISO date (YYYY-MM-DD) |
| `expiresAt` | string | No | ISO date |
| `metadata` | object | No | Key-value for internal use |

**Line item shape:**

```json
{
  "description": "string",
  "quantity": 1,
  "unitAmountCents": 10000,
  "currency": "usd"
}
```

### Response (201)

```json
{
  "id": "sow_abc123",
  "status": "draft",
  "title": "string",
  "clientName": "string",
  "totalCents": 10000,
  "currency": "usd",
  "createdAt": "2026-02-18T12:00:00Z",
  "viewUrl": "https://prodway.ai/sows/sow_abc123",
  "editUrl": "https://prodway.ai/sows/sow_abc123/edit"
}
```

### Errors

- `400` — validation
- `401` — auth
- `500` — server

Body: `{ "error": "code", "message": "..." }`

---

## 2. Trigger invoice (Stripe)

**Endpoint:** `POST /api/invoices`

### Request body

| Field | Type | Required | Notes |
|-------|------|----------|--------|
| `provider` | string | No | Defaults to `"stripe"` |
| `sowId` | string | No | If set, line items can be sourced from SOW |
| `customerId` | string | No | Provider-specific customer id if already exists |
| `customer` | object | Yes if no customerId | See customer shape below |
| `lineItems` | array | Yes if no sowId | Same shape as SOW line items |
| `dueDate` | string | No | ISO date |
| `metadata` | object | No | |
| `collectPayment` | boolean | No | If true, create payment link |

**Customer shape:**

```json
{
  "name": "string",
  "email": "string",
  "address": {
    "line1": "string",
    "city": "string",
    "postalCode": "string",
    "country": "us"
  }
}
```

### Response (201)

```json
{
  "id": "inv_xyz789",
  "provider": "stripe",
  "status": "draft",
  "sowId": "sow_abc123",
  "totalCents": 10000,
  "currency": "usd",
  "createdAt": "2026-02-18T12:00:00Z",
  "invoiceUrl": "https://...",
  "paymentUrl": "https://..."
}
```

`paymentUrl` present when `collectPayment` was true.

### Errors

- Same as SOW, plus `402` / `422` for provider errors. Body can include `providerError` for debugging.

---

## 3. Optional: Create SOW and invoice in one step

**Endpoint:** `POST /api/sows/with-invoice`

### Request body

All fields from Create SOW, plus:

| Field | Type | Required | Notes |
|-------|------|----------|--------|
| `invoice` | object | Yes | |
| `invoice.provider` | string | No | Defaults to `"stripe"` |
| `invoice.dueDate` | string | No | ISO date |
| `invoice.collectPayment` | boolean | No | Default false |

### Response (201)

```json
{
  "sow": { "id": "...", "..." },
  "invoice": { "id": "...", "..." }
}
```

---

## 4. Using Stripe

- Callers only call this Prodway API; they never use Stripe APIs directly.
- Prodway backend stores Stripe credentials per workspace and calls the Stripe API.
