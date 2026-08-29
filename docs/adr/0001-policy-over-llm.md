# ADR-0001: Policy Engine Over LLM

## Status
Accepted

## Date
2026-08-29

## Context
The track says: "an agent that detects revenue at risk, determines the right intervention, and executes a bounded recovery workflow."

Key phrase: **bounded**. And the bar: "Show measured money recovered across a batch, with compliant escalation, stopping rules, and an audit trail."

The obvious temptation is to let the LLM call Razorpay directly: it detects a payment failure, decides to retry, and calls the API.

**Problem**: The LLM is not deterministic. It hallucinates. It might retry too many times, charge the wrong amount, or ignore contact caps. In fintech, an untrusted agent touching money is a compliance nightmare.

## Decision
**The LLM recommends. The policy engine governs.**

Claude outputs a `recommended_action` in a fixed enum. A deterministic, versioned policy engine evaluates that recommendation against hard rules (probability thresholds, amount limits, retry caps, consent, contact caps, quiet hours). The policy engine returns ALLOW, DENY, HUMAN_REVIEW, or SUPPRESS. **Only ALLOW reaches the recovery tools**.

## Consequences

### Positive
- **Trustworthy**: Judges and merchants know exactly what the rules are
- **Testable**: Policy engine is pure functions, table-driven tests, 100% coverage
- **Auditable**: Every decision has a machine-readable reason and version
- **Bounded**: LLM structurally cannot bypass the governor — enforcement lives in the tool
- **Compliant**: Human review, consent checks, and quiet hours are policy inputs

### Negative
- **Less "AI magic"**: Submissions that let the LLM act directly may seem smarter
- **More code**: Policy engine + StoppingRules as separate modules

## Rationale

The bar says "bounded" explicitly. A policy engine is the engineering answer to "how do you trust AI with payments?" It is not flashy, but it is **correct** and **explainable**.

**Alternative considered and rejected**: Letting the LLM call payment APIs directly with prompt-level guardrails. Rejected because guardrails in prompts are soft and fail under edge cases.

**Trade-off**: We accept less "AI magic" in exchange for correctness, auditability, and compliance — the three things fintech judges care about most.