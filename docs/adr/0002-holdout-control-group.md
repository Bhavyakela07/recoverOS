# ADR-0002: Holdout Control Group

## Status
Accepted

## Date
2026-08-29

## Context
The track says: "Show measured money recovered across a batch."

**Problem**: Without a control group, "recovered" is just "how many failed payments eventually succeeded anyway," which is a number we did not earn.

The bar says "measured" — but how do we measure what we earned vs what would have happened anyway?

## Decision
**15-20% holdout control group.**

Control cases are detected, scored, and audited — but receive NO active intervention. This creates a counterfactual baseline: "of these similar cases, how many recovered on their own?" The incremental recovery rate is treatment minus control.

## Consequences

### Positive
- **Credible uplift**: Measured incremental revenue, not vanity metric
- **Science, not vibes**: Counterfactual baseline with random assignment
- **Compliance**: Control cases are still audited — no ethical issue
- **Differentiation**: Most submissions don't use control groups

### Negative
- **Sacrificed recovery**: 15-20% of eligible cases get no intervention
- **Small sample**: Demo control group may not be statistically significant
- **Complexity**: Need is_control flag, treatment/control grouping logic

## Rationale

A number with a denominator is not a vibe. The track asks for "measured money recovered" — that requires attribution, and attribution requires a control group.

**Alternative considered and rejected**: Pre/post comparison ("revenue before vs after"). Rejected because it confounds seasonality, market changes, and natural recovery.

**Trade-off**: We sacrifice 15-20% of recoverable revenue in exchange for a credible, defensible measured uplift figure. For a demo with a seeded population, this is the smallest group that still produces a visible spread in the money slide.

## Notes
- Holdout ratio: 15-20% (configurable)
- Random assignment seeded for reproducibility
- Control cases are NOT ignored — they are scored and audited
- Future: bandit-based allocation to reduce control group size while maintaining statistical power