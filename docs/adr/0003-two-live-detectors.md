# ADR-0003: Two Live Detectors Instead of Four

## Status
Accepted

## Date
2026-08-29

## Context
The track frames revenue leakage as a CATEGORY with four sources: payment fails, checkout abandoned, subscription lapses, invoice overdue.

**Problem**: Building four products in 5 days as a solo dev is impossible. But claiming four and shipping two loses trust.

## Decision
**Two live detectors: PAYMENT_FAILURE (event-driven) and CHECKOUT_ABANDONMENT (sweep-driven). Two dormant: SUBSCRIPTION_FAILURE and OVERDUE_RECEIVABLE (schema + stub).**

All four are:
- Visible in the schema (leak_source enum)
- Visible in the dashboard filter (two marked dormant)
- Visible in the docs
- Exactly this is said out loud in README and pitch

## Consequences

### Positive
- **Honest scope**: Shows architectural thinking without overpromising
- **Source-agnostic pipeline proven**: One detector is event-driven (webhook), the other is sweep-driven — proves the abstraction works
- **Trustworthy**: Judges hear we know the category has four parts
- **Resource efficient**: Two detectors take < 3 days; four would take 5+ days
- **SHOULD not CUT**: Subscription detector is SHOULD, not CUT — we can wire it if time allows

### Negative
- **Not "full coverage"**: Two sources are not live end-to-end
- **Potential perception**: Judges may ask "where are the other two?"

## Rationale

The track wants us to show we UNDERSTOOD the category, not that we built four products.

**Alternative considered and rejected**: Building four leak detectors poorly. Rejected because partial, buggy implementations on all four are worse than two solid ones.

**Alternative considered and rejected**: Calling one detector "payment failures" and pretending it covers all four. Rejected because it's dishonest and fails the vocabulary discipline.

**Trade-off**: We ship two live, two dormant with clear labeling, proving the pipeline is source-agnostic rather than webhook-shaped. This is better than four flaky detectors or one dishonest claim.

## Implementation Notes
- PAYMENT_FAILURE: Razorpay `payment.failed` webhook (HMAC verified)
- CHECKOUT_ABANDONMENT: Scheduled sweep (order created, no payment after N minutes)
- SUBSCRIPTION_FAILURE: Schema + detector stub (dormant, comment: "SHOULD if time permits")
- OVERDUE_RECEIVABLE: Schema + detector stub (dormant, comment: "SHOULD if time permits")
- All four appear in:
  - RevenueLeak.leak_source enum
  - Dashboard leak-source filter (two greyed out)
  - docs/architecture.md detector layer
  - Pitch: "Two live, two dormant — honestly"