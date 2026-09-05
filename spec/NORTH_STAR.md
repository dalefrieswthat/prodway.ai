# Prodway North Star

Treat this as a persistent product and architecture principle for all Prodway work. Before implementing any significant feature, architecture change, UX flow, integration, or roadmap item, evaluate it against this North Star.

## 1. Core Positioning

Prodway is:

**A Slack-first, web-powered engagement operating system for consultants and professional-services businesses.**

Our core promise is:

# Scope it. Sign it. Get paid.

Our differentiated workflow is:

**Conversation → Scope → SOW → Signature → Payment → Engagement → Change Order → Additional Revenue**

We are not building a generic AI document generator.

We are not building another PandaDoc.

We are not building a generic CRM.

We are not building a project-management suite.

We are not building a web application that happens to have a Slack integration.

We are building an AI-native professional-services engagement platform where Slack is a first-class interaction surface and the web application provides the deeper workspace.

## 2. Slack-First, Not Slack-Only

Slack is strategically important to Prodway and must remain a first-class product surface. The web application does NOT replace Slack. The two surfaces serve different purposes.

### Slack = speed and action

Use Slack for:

- creating engagements from conversations
- generating SOWs
- checking engagement status
- receiving signature notifications
- receiving payment notifications
- approving actions
- requesting invoices
- identifying potential scope changes
- reminders
- quick AI interactions
- opening the relevant engagement in Prodway

Example:

User: `/sow Build a two-week AI implementation for Acme. $20k. 50% upfront.`

Prodway:

```
Engagement created.

Acme — AI Implementation
$20,000
SOW ready

Open Engagement →
```

### Web = depth and control

Use the web application for:

- reviewing/editing SOWs
- Scope Health
- engagement history
- structured commercial terms
- version history
- payments
- milestones
- change orders
- client history
- integrations
- account/settings
- deeper engagement intelligence

The web app is the system of record. Slack is a first-class interaction layer over that system.

## 3. The Engagement Is the Product Core

The architectural center of Prodway is NOT Slack, Next.js, FormPilot, DocuSign, Stripe, Mercury, or the SOW generator.

It is:

# Engagement

Everything operates against the same Engagement domain:

- Slack → Prodway API → Engagement
- Web → Prodway API → Engagement
- FormPilot → Prodway API → Engagement
- Future AI agents → Prodway API → Engagement

Never create separate business logic for Slack and web when the behavior belongs to the Engagement domain.

## 4. The Engagement Graph

Prodway should progressively understand:

Client → Engagement → Scope → Deliverables → Acceptance Criteria → Commercial Terms → SOW Versions → Signature → Payment → Milestones → Client Requests → Change Orders → Completion

This structured history is the foundation of Prodway's long-term moat.

## 5. AI Generation Is the Wedge, Not the Moat

Generating an SOW with an LLM is not defensible by itself. Do not optimize the company around "better AI-generated documents." AI SOW creation is our entry point. The moat is accumulated structured engagement context.

Prodway should eventually understand:

- what this consultant normally charges
- how they structure engagements
- typical payment terms
- typical exclusions
- historical clients
- previous scopes
- previous deliverables
- what was signed
- what was paid
- what changed
- what requests were outside scope
- which changes generated additional revenue

Every architectural decision should preserve this structured context.

## 6. Structured Data Before Documents

A SOW must never become merely an HTML document, PDF, or rich-text blob. Canonical data remains structured:

```text
Engagement
  Client
  Project

  Scope
    Objectives
    Deliverables[]
    AcceptanceCriteria[]
    ClientResponsibilities[]
    Assumptions[]
    Exclusions[]

  CommercialTerms
    Value
    PaymentModel
    PaymentSchedule[]

  SOW
    Versions[]
```

Documents are representations of this data. This principle enables future intelligence.

## 7. Own the Revenue Workflow

Prodway should move progressively closer to revenue.

- Phase 1: **Conversation → SOW**
- Phase 2: **Conversation → SOW → Signature**
- Phase 3: **Conversation → SOW → Signature → Payment**
- Phase 4: **Conversation → SOW → Signature → Invoice → Payment**
- Phase 5: **Engagement → Scope Change → Change Order → Signature → Additional Payment**

The ultimate metric is not "How many documents did Prodway generate?" It is closer to: **How much professional-services revenue flowed through engagements managed by Prodway?**

## 8. Scope Intelligence Is Strategically Important

Prodway should become exceptionally good at understanding professional-services scope. Over time, Prodway should understand:

- whether deliverables are sufficiently specific
- whether acceptance criteria are measurable
- whether client responsibilities are defined
- whether exclusions are adequate
- whether payment terms create risk
- whether a client request is included in the signed scope
- whether a new request constitutes scope creep

This leads to **Scope Health** and eventually **Scope Monitoring**.

Example: a client asks in Slack, "Could you also build an analytics dashboard?" Prodway understands the active engagement and signed scope and responds: "Potential scope change detected. The current SOW includes infrastructure implementation but does not include application dashboard development. Create Change Order."

This is one of the most important long-term product capabilities.

## 9. Change Orders Are Revenue, Not Administration

Do not treat change orders as document templates. Prodway should eventually help consultants identify otherwise-lost revenue:

Client request → Compare against signed scope → Potential scope change → Generate Change Order → Additional deliverables → Timeline impact → Additional price → Signature → Payment → Updated engagement value

This transforms Prodway from administrative software into revenue infrastructure.

## 10. Make the Next Action Obvious

Every engagement should eventually answer: **What should I do next?**

Examples: Generate SOW, Improve acceptance criteria, Send for signature, Follow up on unsigned SOW, Collect deposit, Start engagement, Complete milestone, Request milestone payment, Review possible scope change, Create change order, Send final invoice, Close engagement.

The dashboard should prioritize actions over analytics.

## 11. Slack Should Become More Valuable as Prodway Becomes More Powerful

Do not progressively move everything into the web application. As capabilities are added, ask: **Is there a useful Slack interaction for this?**

Examples:

- DocuSign: "Acme signed your $30,000 SOW."
- Stripe: "Acme paid the $15,000 project deposit."
- Mercury: "Invoice #1042 for $15,000 was paid."
- Scope Intelligence: "Potential out-of-scope request detected in the Acme engagement."
- Milestones: "The Acme engagement reaches its final milestone tomorrow."

The user should be able to take lightweight actions without opening Prodway when appropriate.

## 12. But Do Not Force Complex Work Into Slack

Slack-first does not mean every workflow must happen inside Slack. Use this rule:

**Quick interaction → Slack. Deep interaction → Web.**

Examples:

- Create SOW → Slack
- Edit complex SOW → Web
- Payment received notification → Slack
- Review payment history → Web
- Potential scope creep → Slack
- Compare request against full contract → Web
- Create change order → Slack can initiate
- Edit/finalize change order → Web

This division should remain intentional.

## 13. Integration Philosophy

Integrations are not standalone features. They should complete parts of the engagement lifecycle.

- DocuSign: signature infrastructure
- Stripe: payment collection infrastructure
- Mercury: invoice/financial workflow infrastructure
- Slack: interaction infrastructure
- FormPilot: data-entry/autofill infrastructure

Future integrations should be evaluated based on whether they strengthen **Conversation → Scope → Signature → Revenue**. Do not accumulate integrations simply to make an integrations page look impressive.

## 14. Product Simplicity

Prodway should remain significantly simpler than traditional proposal, CRM, accounting, or project-management platforms. The initial web navigation should remain intentionally small:

Dashboard, Engagements, Clients, Integrations, Settings

Do not add top-level navigation simply because a new entity exists. Complexity must earn its place.

## 15. Product Decision Filter

Before implementing a significant feature, ask: does this help a professional-services business:

1. Scope work faster?
2. Produce a stronger engagement?
3. Get an agreement signed faster?
4. Get paid faster?
5. Understand what is happening with an engagement?
6. Prevent unbilled scope creep?
7. Capture additional revenue?
8. Reduce administrative work?
9. Build useful engagement memory?

If the answer is no to essentially all of these, challenge whether the feature belongs in Prodway.

## 16. Architecture Decision Filter

Before implementing significant architecture, ask: does this

- preserve structured engagement data?
- keep domain logic inside the Prodway API?
- work across both Slack and web?
- preserve historical context?
- avoid unnecessary provider coupling?
- make future signature/payment/change-order workflows possible?
- contribute to the Engagement Graph?

Avoid implementation shortcuts that undermine these principles for temporary frontend convenience.

## 17. UX Decision Filter

When designing a workflow, ask: **Can this begin naturally from a conversation?** If yes, consider Slack. Then ask: **Does completing this require significant review, editing, comparison, or historical context?** If yes, use the web application for that portion.

The transition should feel seamless. Slack: "Potential scope change detected. Review →". Web: full comparison between client request and signed SOW.

## 18. Long-Term Product Vision

Prodway eventually becomes an AI engagement operations agent. The user should eventually be able to ask:

- "What needs my attention?"
- "Which SOWs haven't been signed?"
- "Who owes me money?"
- "Which projects have scope-creep risk?"
- "Did Acme request anything outside the SOW?"
- "Create a change order."
- "Invoice the next milestone."
- "Create a renewal engagement based on last year's project."

Prodway can answer because it owns structured engagement context, not because it is simply connected to an LLM.

## 19. North Star Metrics

Near term: **Engagements created**, then **SOWs sent**, then **Signed engagement value**, then **Payments facilitated**, then **Additional revenue captured through change orders**.

Long-term North Star candidate: **Gross Engagement Value managed through Prodway**. Supporting metric: **Revenue captured/protected through Prodway**.

Do not optimize primarily for AI generations, messages, or document count.

## 20. Current Execution Priority

Do not allow this long-term vision to expand Phase 1 scope. The current priority remains:

**Login → Create Engagement → AI extraction → Structured SOW → Basic edit → Professional PDF**

Build the smallest excellent version of that workflow first. The North Star guides architecture. It does not justify prematurely building future phases.

## Standing Instruction

Treat this document as a product constitution for Prodway. When planning future tickets:

1. Reference the relevant North Star principles.
2. Identify whether the feature belongs primarily in Slack, Web, or both.
3. Identify what Engagement-domain data it creates or consumes.
4. Explain how it advances the core lifecycle: **Conversation → Scope → SOW → Signature → Payment → Engagement → Change Order → Revenue**
5. Flag requests that materially conflict with this strategy before implementing them.
6. Prefer the smallest implementation that advances the North Star.
7. Do not use future vision as justification for expanding the currently approved phase.

Most importantly: **do not let Prodway become a dashboard-first generic SaaS product with Slack bolted onto it.**

Prodway is:

# Slack-first. Web-powered. Engagement-centered. AI-native.

And its job is simple:

# Help professional-services businesses scope work, get it signed, get paid, and capture the revenue they have earned.
