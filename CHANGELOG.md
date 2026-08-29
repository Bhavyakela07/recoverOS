# RecoverOS Changelog

All notable changes to RecoverOS will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.1.0-m0-skeleton] — 2026-08-29

### Added — Milestone 0: Scaffold + Walking Skeleton

**This is the walking skeleton — a thin, ugly, end-to-end slice of the Demo Acceptance Test.**

- Directory structure: backend/, frontend/, docs/, tests/, demo/
- README.md with one-liner, bar-mapping table, quick start, demo script
- docs/architecture.md — system architecture, data flows, component boundaries
- docs/spec.md — API contracts, schemas, business logic specs
- docs/plan.md — 5-day solo build plan, milestones, dependencies
- docs/adr/ — 5 Architecture Decision Records:
  - 0001: Policy engine over LLM (bounded autonomy)
  - 0002: Holdout control group for measured uplift
  - 0003: Two live detectors, two dormant (honest scope)
  - 0004: n8n off critical path (preserve AI-coding advantage)
  - 0005: Calibration matters (credible economics)
- backend/main.py — FastAPI app with walking skeleton
  - Fake detector, prediction, AI, strategy services
  - REAL PolicyEngine + StoppingRules (deterministic, versioned)
  - Governed recovery tools (idempotent + policy-gated)
  - BatchRecoveryRun with holdout control + uplift report
  - Demo/replay mode with curated cases
- backend/services/interfaces.py — service interfaces + fake implementations
  - LeakDetector, PredictionService, AIService, StrategySimulator, RazorpayGateway
  - FakeDetector, FakePredictionService, FakeAIService, FakeStrategySimulator, FakeRazorpayGateway
- backend/services/policy_engine.py — deterministic policy + stopping rules
  - PolicyEngine class (pure, versioned)
  - evaluate_policy() — table-driven decision logic
  - evaluate_stopping_rules() — first-class stopping rules module
  - StoppingRules as pure function, named, versioned, testable
  - PolicyResult, StopDecision schemas
- backend/services/recovery_tools.py — governed, idempotent tools
  - RecoveryTools: retry_payment, send_recovery_message, follow_up, escalate_to_human, record_audit_event
  - IdempotencyManager
  - validate_policy_token() — tool refuses without proof of ALLOW
- backend/models/schemas.py — Pydantic v2 schemas (single source of truth)
  - RevenueLeak, CustomerProfile, PredictionResult, AIRecommendation
  - StrategyOption, PolicyResult, StopDecision
  - RecoveryAction, RecoveryActionResult, BatchRecoveryReport
  - DecisionDossier, LeakSource, FailureCategory, RecoveryAction enums
  - PolicyDecision, PolicyReason, StoppingRuleReason, ReasonCode enums
- backend/runner.py — demo runner script
- docker-compose.yml — PostgreSQL service
- requirements.txt — dependencies
- .env.example — environment variables template
- CHANGELOG.md

### Vocabulary Discipline
All APIs and documentation use track's own words:
- "revenue at risk"
- "bounded"
- "measured money recovered"
- "across a batch"
- "compliant escalation"
- "stopping rules"
- "close the loop"

### The Bar (5 Demands) — M0 Verification
| Demand | Status | Where |
|--------|--------|-------|
| ACT (don't just detect) | ✅ Walking skeleton | Governed recovery tools execute |
| MEASURED money across batch | ✅ Walking skeleton | BatchRecoveryRun + holdout control |
| COMPLIANT escalation | ✅ Walking skeleton | HUMAN_REVIEW path |
| STOPPING rules | ✅ Walking skeleton | StoppingRules module, named |
| AUDIT trail | ✅ Walking skeleton | Decision Dossier export |

### Demo Acceptance Test (Walking Skeleton Target)
- ✅ Fake payment.failed webhook → persisted as RevenueLeak
- ✅ Fake ML → calibrated probability
- ✅ Fake Claude → structured grounded recommendation
- ✅ Strategy simulator → 5 strategies ranked by expected NET recovery
- ✅ Stopping rules checked
- ✅ Policy returns ALLOW
- ✅ Tool executes in test mode
- ✅ Outcome recorded
- ✅ Dashboard counter increments
- ✅ Decision Dossier exports

### Limits & Honesty (M0 Confirmed)
- Synthetic dataset — demonstrates pipeline, not production performance
- Two of four sources live — payment failure + checkout abandonment
- Subscription & overdue are schema + stub (dormant)
- Test mode only — no real money moves anywhere
- Small control group — 15-20% for demo, not statistical rigor

---

## Planned Milestones (After M0)

### [0.2.0-m1-db] — PostgreSQL Schema + Migrations
- SQLAlchemy models for all tables
- Alembic migrations
- Real persistence + idempotency (double-webhook test)

### [0.3.0-m2-webhook] — Razorpay Webhook + Signature Verification
- /webhook/razorpay endpoint
- HMAC-SHA256 verification
- Events: payment.failed, payment.captured, payment.authorized, order.paid

### [0.4.0-m3b-sweep] — Abandonment Sweep Detector
- APScheduler scheduled sweep
- Orders created, no payment after N minutes
- Second live leak source

### [0.5.0-m4-ml] — Calibrated XGBoost + Eval + Fallback
- Synthetic dataset generator (seeded)
- XGBoost + isotonic/Platt calibration
- Eval: precision, recall, F1, ROC-AUC, Brier score
- Model card in docs/
- Fallback: calibrated logistic regression

### [0.6.0-m5-ai] — Claude Structured Reasoning
- Anthropic SDK integration
- Structured outputs with Pydantic validation
- PII redaction before LLM call
- Invalid output repair + deterministic fallback
- Hinglish/regional message drafts

### [0.7.0-m6-strategy] — Strategy Simulator
- Five strategies minimum
- Expected net recovery calculation
- argmax among policy-allowed, non-stopped options
- Unit tests for strategy math

### [0.8.0-m7-governor] — Policy Engine + StoppingRules
- PolicyEngine class with versioned config
- StoppingRules as pure, testable module
- Table-driven tests: exhaustive coverage
- Version recorded on every decision

### [0.9.0-m8-tools] — Governed Idempotent Tools
- Real RazorpayGateway for test mode
- All tools execute against Razorpay test mode (rzp_test_ keys)
- Idempotency key validation
- Policy token validation

### [0.10.0-m9-measured-money] — BatchRecoveryRun + Holdout + Uplift
- Holdout assignment: 15-20% random to CONTROL
- Full report: cases, revenue_at_risk, treatment/control counts, INCREMENTAL RECOVERY RATE
- measured_money_recovered + incremental_revenue + net_recovered
- Guardrail metrics

### [0.11.0-m10-dashboard] — Dashboard + Decision Dossier
- Next.js 14 + TypeScript + Tailwind + Recharts
- /dashboard — revenue at risk, MEASURED money recovered, recovery rate
- /recovery — case list with filters, sort
- /recovery/[id] — case money page + Decision Dossier export

### [0.12.0-m11-demo] — Demo/Replay + E2E + README + ADRs + Loom
- Seeded injector for deterministic demo
- Curated cases: ALLOW, HUMAN_REVIEW, DENY, SUPPRESSED, CONTROL
- One-click Decision Dossier export
- End-to-end test
- 60-90s Loom video
- Honest limitations section

---

## Versioning

- Format: MAJOR.MINOR.PATCH-MILESTONE
- MAJOR: Breaking changes to core architecture
- MINOR: New feature or milestone completion
- PATCH: Bug fixes, documentation updates
- MILESTONE: M0-M11

---

## License

Built for Razorpay Buildathon Track 03. Demo code only.