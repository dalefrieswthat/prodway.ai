# Billing & Subscription Specification

> **Status:** Production  
> **Last Updated:** April 2026

---

## Overview

Prodway uses a pay-first subscription model. Users complete Stripe Checkout before connecting their Slack workspace. The $5/month subscription covers both SowFlow and FormPilot, with metered overage billing for SOW generation beyond 25/month.

## Pricing

| Item | Price |
|------|-------|
| Prodway Suite (SowFlow + FormPilot) | $5/month |
| Included SOWs | 25/month |
| Additional SOWs | $0.25 each (metered) |

## Stripe Configuration

### Products & Prices
- **Base Price (`STRIPE_PRICE_BASE_ID`):** $5/month recurring
- **Usage Price (`STRIPE_PRICE_USAGE_ID`):** $0.25/unit metered (sum aggregation)

### Signup Flow

```
User clicks "Sign Up" on prodway.ai
    → GET /signup
    → Stripe Checkout Session (subscription mode)
    → Payment completes
    → Webhook: checkout.session.completed
        → Store subscription details with signup_token
    → Redirect to /signup/connect-slack
    → User clicks "Add to Slack"
    → Slack OAuth flow
    → OAuth callback with signup_token
    → Link subscription to team_id
    → Redirect to /install/success
```

### Subscription Lifecycle

| Event | Handler |
|-------|---------|
| `checkout.session.completed` | Create billing record, store signup_token mapping |
| `customer.subscription.updated` | Update subscription status |
| `customer.subscription.deleted` | Mark subscription inactive |
| `invoice.paid` | Log invoice for analytics |

### Metered Usage

After 25 SOWs in a billing period:
```python
stripe.SubscriptionItem.create_usage_record(
    usage_item_id,
    quantity=1,
    action="increment"
)
```

### Paywall Enforcement

| Action | Check | Blocked Response |
|--------|-------|------------------|
| `/sow [description]` | `can_team_generate_sow()` | Ephemeral message with subscribe link |
| Edit SOW button | `is_team_subscribed()` | Ephemeral "subscription required" |
| FormPilot API calls | `validate_subscription()` | 401 (no key) or 402 (no subscription) |

## API Key System

- Format: `pw_` + 32-char URL-safe token
- Generated from Slack App Home (subscribed users only)
- Stored in team integrations file
- Validated via `GET /api/validate-key`
- Cached for 5 minutes on FormPilot side
- Fail-open during SowFlow outage (for `pw_` prefix keys)
