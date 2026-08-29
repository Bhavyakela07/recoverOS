# RecoverOS 5-Day Build Plan

**Plan v1.0.0 – 2026-08-29**

---

## Method: Walking Skeleton First

**Do NOT build layer by layer.** Build a **WALKING SKELETON** — a thin, ugly, end-to-end slice of the Demo Acceptance Test with every layer stubbed — on Day 1. Then thicken.

This guarantees:
- Always have something demoable
- Single best protection for solo dev against Day-5 disaster
- Architecture validated before investing in details

---

## Day 1: M0 — Scaffold + Walking Skeleton

**Goal**: End-to-end slice runs with fake services.

### Deliverables
- [x] Directory structure
- [x] requirements.txt, docker-compose.yml, .env.example
- [x] docs/architecture.md, docs/spec.md, docs/plan.md
- [x] ADRs (5 decision records)
- [x] FastAPI app with all service interfaces + fake implementations
- [x] Real PolicyEngine + StoppingRules (the crown jewels)
- [x] Fake detector, prediction, AI, strategy, Razorpay
- [x] Governed recovery tools (idempotent + policy-gated)
- [x] BatchRecoveryRun with holdout control
- [x] Demo/replay mode with curated cases
- [x] One dashboard tile: "Measured Money Recovered"
- [x] CHANGELOG.md, README.md

### Commands
```bash
docker-compose up -d postgres
cd backend && python -m venv .venv && source .venv/bin/activate
pip install -r ../requirements.txt
python -m uvicorn main:app --reload --port 8000
curl -X POST localhost:8000/batch/recovery -d '{"seed":42,"case_count":50,"holdout_ratio":0.15}'
curl localhost:8000/demo/replay
```

### Demo Acceptance Test (Target)
Walking skeleton processes curated cases → policy returns ALLOW/DENY/SUPPRESS → tools execute (fake) → money slide emitted.

---

## Day 2: M1-M3b — Core Infrastructure

**Goal**: Real persistence, real webhooks, second leak source live.

### M1: PostgreSQL Schema + Migrations
- [ ] SQLAlchemy models for all tables
- [ ] Alembic migration: initial schema
- [ ] Tables: merchants, customers, orders, payments, payment_attempts, revenue_leaks, failure_events, recovery_cases, model_predictions, ai_decisions, recovery_actions, policies, stopping_rules, recovery_experiments, batch_runs, contact_log, audit_events
- [ ] Indexes, FKs, UNIQUE constraints, created_at/updated_at

### M2: Razorpay Webhook + Signature Verification
- [ ] FastAPI webhook endpoint: `/webhook/razorpay`
- [ ] HMAC-SHA256 verification (raw body + secret)
- [ ] Events consumed: payment.failed, payment.captured, payment.authorized, order.paid
- [ ] Persist as RevenueLeak with idempotency (UNIQUE event_id)

### M3: Persistence + Idempotency
- [ ] Repository layer (SQLAlchemy async)
- [ ] Transaction management with rollback
- [ ] Idempotency key tracking (Redis or DB table)
- [ ] **Double-webhook test**: fire identical webhook twice → assert one record, one action

### M3b: Abandonment Sweep Detector
- [ ] APScheduler or FastAPI startup task
- [ ] Sweep logic: orders created, no payment after N minutes (configurable, default 30)
- [ ] Normalize to RevenueLeak with leak_source=checkout_abandonment
- [ ] Runs on schedule, independent of webhooks

### Commands
```bash
cd backend
alembic upgrade head
python -m pytest tests/test_idempotency.py -v
python -m pytest tests/test_detectors.py -v
```

---

## Day 3: M4-M6 — ML + AI Layer

**Goal**: Real ML predictions, real Claude reasoning, strategy simulation.

### M4: Calibrated Recovery Probability Model
- [ ] Synthetic dataset generator (seeded, committed, not giant CSV)
- [ ] XGBoost training with calibration (isotonic/Platt)
- [ ] Evaluation: precision, recall, F1, ROC-AUC, Brier score, calibration curve
- [ ] Model card in docs/model_card.md
- [ ] Fallback: calibrated logistic regression behind same interface
- [ ] Model serialized to ./models/recovery_model.xgb

### M5: Claude Structured Reasoning
- [ ] Anthropic SDK integration
- [ ] Structured outputs with Pydantic validation
- [ ] System prompt (versioned in repo)
- [ ] PII redaction before LLM call
- [ ] Invalid output: 1 repair retry → deterministic fallback
- [ ] Log every invalid output (real metric)
- [ ] Hinglish/regional message drafts (SHOULD)

### M6: Strategy Simulator
- [ ] Five strategies minimum: retry, reminder, incentive, follow_up, escalate, none
- [ ] Expected net recovery calculation
- [ ] argmax among policy-allowed, non-stopped options
- [ ] Ranked table with SIMULATED labels
- [ ] Unit tests for strategy math

### Commands
```bash
cd backend
python -m pytest tests/test_ml.py -v
python -m pytest tests/test_ai.py -v
python -m pytest tests/test_strategy.py -v
```

---

## Day 4: M7-M9 — Governor + Measurement

**Goal**: Real policy engine, real governed tools, real measured money.

### M7: Policy Engine + StoppingRules
- [ ] PolicyEngine class with versioned config
- [ ] StoppingRules as pure, testable module
- [ ] Table-driven tests: exhaustive coverage
- [ ] Version recorded on every decision (policy_version field)
- [ ] Separate test file for stopping rules

### M8: Governed Idempotent Tools (Test Mode)
- [ ] Real RazorpayGateway for test mode
- [ ] RecoveryTools: retry_payment, send_recovery_message, follow_up, escalate_to_human, record_audit_event
- [ ] Idempotency key validation in tool
- [ ] Policy token validation in tool (refuses without ALLOW)
- [ ] All tools execute against Razorpay test mode (rzp_test_ keys)

### M9: BatchRecoveryRun + Holdout + Uplift Report
- [ ] Holdout assignment: 15-20% random to CONTROL
- [ ] Control cases: detected, scored, audited, NO intervention
- [ ] Full report: cases, revenue_at_risk, treatment/control counts, recovery rates, INCREMENTAL RECOVERY RATE, measured_money_recovered, incremental_revenue, intervention_cost, NET_RECOVERED, cost_per_rupee, guardrail metrics
- [ ] **This is the bar** — if M9 green, the track's core demand is met

### Commands
```bash
cd backend
python -m pytest tests/test_policy.py -v
python -m pytest tests/test_stopping_rules.py -v
python -m pytest tests/test_tools.py -v
python -m pytest tests/test_batch.py -v
```

---

## Day 5: M10-M11 — Frontend + Demo Polish

**Goal**: 3-page dashboard, Decision Dossier, demo-ready, README, Loom.

### M10: Frontend (3 Pages Only)

**Stack**: Next.js 14 + TypeScript + Tailwind + Recharts

**Pages**:
1. `/dashboard` — Revenue at risk, MEASURED money recovered, recovery rate, incremental vs control, active cases, human escalations, suppressed by rules, policy blocks, live recovered-rupee counter
2. `/recovery` — Case list with filters, sort, control tags
3. `/recovery/[id]` — Case money page: leak details, probability, AI diagnosis with evidence chips, ranked alternatives (SIMULATED), expected net recovery, stopping-rule check, policy decision, action status, outcome, audit timeline, "Export Decision Dossier"

**Design**: Confident, calm, financial. Restrained palette, one accent, real data density, tabular numerals for money. Label all simulated values.

### M11: Demo/Replay + E2E + README + ADRs + Loom
- [ ] Seeded injector for deterministic demo
- [ ] Curated cases: ALLOW, HUMAN_REVIEW, DENY, SUPPRESSED, CONTROL
- [ ] One-click Decision Dossier export (JSON + human-readable)
- [ ] End-to-end test: webhook → detect → predict → reason → govern → execute → measure
- [ ] README with one-liner, bar-mapping table, limitations
- [ ] ADRs (5 records)
- [ ] 60-90s Loom video in README

### SHOULD (Only if MUST is Green)
- [ ] Live pipeline view on /dashboard (stages light up)
- [ ] Hinglish/regional message drafts
- [ ] Subscription detector wired (third live source)
- [ ] n8n garnish (Slack/email notifications only)

### If Day 4 Slips
**Sacrifice Day 5 frontend polish — NEVER the batch measurement.** The bar asks for measured money, not a beautiful dashboard.

---

## Daily Checkpoints

### End of Each Day:
- [ ] Tests pass
- [ ] Behavior verified against actual database (not mocks)
- [ ] Docs updated (architecture.md, spec.md, plan.md)
- [ ] Committed with milestone tag (M0, M1, M2, ...)

### Never:
- Claim DB writes succeeded without querying the DB
- Say something works when mocked — say "mocked" out loud
- Add SHOULD items before MUST items are green

---

## Risk Register & Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| ML training takes too long | High | Medium | Fallback: logistic regression behind same interface |
| Razorpay webhook debugging | Medium | High | Fake webhook for skeleton; real webhook Day 2 |
| Claude API latency/errors | Medium | Medium | Deterministic fallback; structured outputs |
| DB schema changes | Low | High | M1 migrations; no changes after M1 |
| Day 4 slip | Medium | High | Cut SHOULD items immediately; protect M9 |
| Frontend takes too long | Medium | Medium | 3 pages max; Recharts for money slide |

---

## Open Questions (Must Verify Before Day 1)

1. **Judging criteria and weights** — confirm from buildathon page
2. **Team-size cap** — confirm solo entries eligible
3. **Submission format** — public repo? deployed link? video length?
4. **Official build window** — confirm code written before window is allowed
5. **Razorpay test mode mandated?** — assume yes, confirm
6. **Sponsor tooling bonus points** — would revisit n8n decision if yes

---

## Success Criteria

**Minimum Viable Submission (Bar Met)**:
- BatchRecoveryRun runs with holdout control
- Measured money recovered + incremental uplift reported
- Policy engine + stopping rules govern every action
- Decision Dossier exports for any case
- Demo runs end-to-end in 3 minutes
- README with bar-mapping table

**Winning Submission** (All MUST +):
- 2 live detectors (payment + abandonment)
- Calibrated XGBoost with model card
- Claude structured reasoning with evidence
- Hinglish drafts
- Live pipeline view on dashboard
- Loom video
- Honest limitations section

---

## Commit & Tag Strategy

```bash
# Each milestone
git add -A
git commit -m "M0: Scaffold + walking skeleton"
git tag m0-skeleton

git commit -m "M1: PostgreSQL schema + migrations"
git tag m1-db

git commit -m "M2: Razorpay webhook + signature verification"
git tag m2-webhook

git commit -m "M3: Persistence + idempotency (double-webhook test)"
git tag m3-idempotency

git commit -m "M3b: Abandonment sweep detector"
git tag m3b-sweep

git commit -m "M4: XGBoost calibrated model + eval"
git tag m4-ml

git commit -m "M5: Claude structured reasoning + PII redaction"
git tag m5-ai

git commit -m "M6: Strategy simulator (expected net recovery)"
git tag m6-strategy

git commit -m "M7: Policy engine + StoppingRules, versioned + tested"
git tag m7-governor

git commit -m "M8: Governed idempotent tools in test mode"
git tag m8-tools

git commit -m "M9: BatchRecoveryRun + holdout + uplift report"
git tag m9-measured-money

git commit -m "M10: Dashboard (3 pages) + Decision Dossier"
git tag m10-dashboard

git commit -m "M11: Demo/replay + e2e + README + ADRs + Loom"
git tag m11-demo-ready
```

---

## Time Boxing Per Day

| Time | Activity |
|------|----------|
| 09:00-09:30 | Plan & review previous day |
| 09:30-12:30 | Deep work block 1 |
| 12:30-13:30 | Lunch / break |
| 13:30-17:30 | Deep work block 2 |
| 17:30-18:00 | Tests, docs, commit, tag |
| 18:00+ | Buffer / contingency |

**Protect the buffer.** Cut SHOULD items the moment they threaten a MUST.