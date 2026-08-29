# RecoverOS Architecture

**Architecture Document v1.0.0 – 2026-08-29**

## One Sentence
RecoverOS is a **governed AI decision engine** for revenue recovery: detect revenue at risk, price interventions by expected net recovery, govern every action through deterministic policy, and prove incremental rupee recovery against a holdout control group.

---

## TL;DR (Judges Should Read This First)

- **Pipeline**: Webhook + sweep → normalize into RevenueLeak → predict → reason → simulate → govern → execute → audit → measure
- **Bounded Autonomy**: LLM recommends, deterministic policy engine governs, tools execute in test mode only
- **Measured Value**: Incremental rupees vs control group, net of intervention cost (the money slide)
- **Two Live Detectors**: PAYMENT_FAILURE (webhook) + CHECKOUT_ABANDONMENT (sweep)
- **Policy Engine + StoppingRules**: Pure, deterministic, versioned, independently tested
- **Audit Trail**: Decision Dossier exports every case end-to-end

---

## Core Philosophy

**"The LLM recommends. The policy engine governs."**

- Claude has **NO authority** to move money. Never.
- Every financial action passes **deterministic, server-side policy validation** before execution.
- Claude output is **UNTRUSTED INPUT**: schema-validated, enum-constrained, range-checked.
- **PostgreSQL is the single source of truth** (no frontend secrets).
- **Write tools refuse execution** without proof of a passing policy decision.

---

## System Overview

```
                                           +-------------------+
                                           |  BACKEND API      |
                                           |  (FastAPI + Pydantic)|
                                           +-------------------+
                                                    |
                     +------------------------|------------------------+
                     |                        v                        |
        +------------+------------+           +-------------------+
        |            |            |           |   DECISION LAYER   |
        v            v            v           |   (ML + LLM + Policy)|
    Razorpay Test Mode    Scheduled Sweep     |   +----------------+   |
    webhook:payment.failed   orders created   |   | ML: XGBoost     |   |
    signature-verified       no payment > N   |   | recovery_prob  |   |
                 |                minutes     |   | (calibrated)   |   |
                 +----------------+-----------+   +----------------+   |
                                 v               v                    v
                        DETECTOR LAYER  ->  StrategySimulator  ->  GOVERNOR
              (pluggable)      normalizes           expected NET      deterministic
                           everything       recovery · argmax     policy + stopping
                          into RevenueLeak                           |
                                 |                                 |
                                 v                                 v
                      +---------------------------+--------------------+
                      |                           |                    |
                      v                           v                    v
                 PostgreSQL                      ALLOW            SUPPRESS/HUMAN_REVIEW
                 SOURCE OF TRUTH                 (governs)         (stopping rules)
                  idempotency · audit ·          |                 |
                  holdout assignment            v                 v
                                          Recovery Tools    BatchRecoveryRun
                                         (idempotent, gated)      |
                                        retry · message ·        v
                                        follow-up · escalate  MEASURED MONEY RECOVERED
                                                 \               |
                                                  \-------------\/
                                                          DASHBOARD
```

---

## Component Details

### 1. Detector Layer (Pluggable)

**Purpose**: Source-agnostic revenue leak detection → unified RevenueLeak entity.

**Interfaces**:
- `detect()` → `List[RevenueLeak]`

**Live Detectors**:
- `PaymentFailureDetector`: Razorpay `payment.failed` webhook (HMAC-SHA256 verified)
- `CheckoutAbandonmentDetector`: Scheduled sweep (order created, no payment after N minutes)

**Dormant Detectors**:
- `SubscriptionFailureDetector`: Schema + stub
- `OverdueReceivableDetector`: Schema + stub

**Key Decision**: Two live, two dormant shows the abstraction works without shipping four products. Judges reward this architectural clarity.

### 2. PostgreSQL (Source of Truth)

**Schema Highlights**:
- `revenue_leaks`: Unified leak entity, leak_source enum
- `ai_decisions`: LLM in/out with reason_codes, confidence, latency, model version
- `policies`: Versioned configuration
- `stopping_rules`: Versioned, configurable thresholds
- `recovery_experiments`: Holdout/control assignment
- `batch_runs`: One row per BatchRecoveryRun + uplift results
- `audit_events`: Complete audit trail per case

**Constraints**: PKs, FKs, UNIQUE constraints, transactions with rollback, created_at/updated_at everywhere.

### 3. ML Service (Recovery Probability)

**Model**: XGBoost + calibration (fallback: calibrated logistic regression)

**Input Features**:
- amount, payment_method, failure_code, leak_source, retry_count
- customer historical success rate, prior successes/failures
- time_since_leak, hour/day, alternate-method availability

**Output**: recovery_probability [0,1], risk_score [0,1], calibrated

**Calibration**: Isotonic or Platt — not optional because strategy simulator multiplies probability by rupees.

### 4. Decision Layer

#### 4.1 AI Reasoning (LLM)

**Job**: Understand leak and context, review history, obtain recovery probability, compare interventions, recommend ONE, explain grounded in evidence.

**Constraints**:
- REDACTED, STRUCTURED context only (no PII)
- STRICT JSON via structured outputs, Pydantic-validated
- On invalid output: one repair retry, then deterministic fallback
- GROUNDED explanations required
- reason_codes is a **FIXED enum** (human auditability)

**Schema**:
```json
{
  "leak_diagnosis": "<=280 chars, plain language",
  "failure_category": "enum",
  "recommended_action": "retry|reminder|incentive|follow_up|escalate|none",
  "confidence": 0.0-1.0,
  "reason_codes": ["enum", ...],
  "evidence": [{"signal": "tool.field", "value": "<...>"}],
  "customer_message_draft": "optional; policy-checked before send",
  "message_language": "en|hinglish|regional",
  "requires_human_review": true|false
}
```

#### 4.2 Strategy Simulator

**Purpose**: Compare at least five strategies (retry, reminder, incentive, follow-up, human escalation, "do nothing")

**Logic**:
- Expected recovery = recovery_probability × recoverable_amount
- Intervention cost per strategy (retry=$0.50, reminder=$1.00, incentive=$50, follow-up=$5, escalate=$100)
- Expected NET recovery = expected_recovery − intervention_cost
- Select argmax(expected_net_recovery) AMONG policy-allowed, non-stopped options

**Governor first, optimizer second** — never reverse.

#### 4.3 Governor (Policy Engine + StoppingRules)

**Two pure, deterministic, independently-testable modules**:

##### 4.3.1 Policy Engine
**Inputs**: recovery_probability, risk_score, amount, retry_count, proposed_action, merchant_policy, mandate limits, consent
**Output**: ALLOW | DENY | HUMAN_REVIEW, with machine-readable reason

**Core Rules**:
- IF probability ≥ threshold AND risk_score ≤ threshold AND retry_count < max_retries AND amount ≤ amount_limit AND action permitted AND consent valid AND contact cap not reached AND within allowed hours
- THEN ALLOW else HUMAN_REVIEW or DENY

##### 4.3.2 StoppingRules (First-Class Module)
**Track named these explicitly** — make them real, not scattered if-statements.

**Rules**:
- max retry attempts per leak
- max total contacts per customer per rolling window
- quiet hours / no-contact windows
- minimum expected net recovery (suppress if uneconomic)
- minimum recovery probability (suppress hopeless cases)
- hard stop on opt-out / consent withdrawal
- hard stop on fraud or chargeback signal
- cool-down period between attempts on same leak
- global per-run action budget

**Output**: StopDecision(stop: bool, rule: <enum>, explanation: str)

### 5. Recovery Tools (Governed, Idempotent)

**Rules**:
- Validate every argument with Pydantic
- Every write tool requires idempotency key AND passing PolicyResult token
- Tool refuses execution without proof of ALLOW
- **The enforcement lives in the tool, not in the prompt** — this is why the LLM structurally cannot bypass governor

**Tools**:
- `retry_payment()`: Execute payment retry (Razorpay test mode)
- `send_recovery_message()`: Send recovery SMS/WhatsApp/email
- `follow_up()`: Schedule follow-up call
- `escalate_to_human()`: Create human review queue item
- `record_audit_event()`: Audit trail write

### 6. BatchRecoveryRun (The Money Slide)

**Purpose**: Process a population of N leaks through the full live pipeline, emit measured incremental recovery report.

**Holdout Control**: Randomly assign ~15-20% of eligible cases to CONTROL (is_control = true)

**Report Fields**:
- cases detected, revenue at risk
- treatment/control group counts
- recovery rates and INCREMENTAL RECOVERY RATE
- measured money recovered
- incremental revenue (attributable)
- intervention cost
- net recovered
- cost per rupee recovered
- guardrail metrics (suppression, opt-out, repeat-contact, human-review load, policy-block breakdown)

**The centerpiece** — judges explicitly say "measured money recovered across a batch."

### 7. Frontend (3 Pages Only)

**Pages**:
- `/dashboard`: Revenue at risk · MEASURED Money Recovered · Recovery Rate · Incremental Recovery vs control · Active Cases · Human Escalations · Suppressed by Stopping Rules · Policy Blocks
- `/recovery`: Case list with source, amount, probability, recommended action, policy decision, status
- `/recovery/{id}`: Case money page (leak details · probability · AI diagnosis · ranked alternatives · stopping-rule check · policy decision · action status · outcome · audit timeline · "Export Decision Dossier")

**Design**: Confident, calm, financial. Restrained palette, one accent, real data density, tabular numerals for money. Label all simulated values.

---

## Technology Stack

**Frontend**: Next.js · TypeScript · Tailwind · Recharts
**Backend**: Python · FastAPI · Pydantic v2
**Database**: PostgreSQL (managed free tier or docker-compose)
**AI**: Claude API · structured outputs · tool calling
**ML**: XGBoost + calibration (fallback: calibrated logistic regression behind SAME interface)
**Scheduler**: APScheduler or FastAPI startup task
**Payments**: Razorpay TEST MODE only (rzp_test_ keys)
**Testing**: Pytest (policy, stopping rules, idempotency, LLM schema, strategy math, one end-to-end path)

---

## Integration Discipline

**Seam Interfaces**:
- Every external dependency sits behind one seam with a fake implementation
- Fake implementation allows any layer to be down while demo still runs
- Example: `LeakDetector.detect()` -> fake returns synthetic leaks

**Interface Examples**:
- `LeakDetector.detect() -> list[RevenueLeak]`
- `PredictionService.predict(features) -> ProbabilityResult`
- `AIService.analyze(context) -> Recommendation`
- `StrategySimulator.rank(case) -> list[StrategyOption]`
- `PolicyEngine.evaluate(inputs) -> PolicyResult`
- `StoppingRules.check(case) -> StopDecision`
- `RazorpayGateway.<action>(...) -> external response`
- `RecoveryTools.* -> execution result`

---

## Error Handling

**Handle explicitly, each with fallback + audit entry**:
- duplicate webhook → idempotent no-op
- invalid webhook signature → reject, audit
- Razorpay API failure or timeout → audit + fallback
- Claude timeout → deterministic fallback recommendation
- invalid Claude JSON → retry + fallback
- ML unavailable → fallback to logistic regression
- DB failure → retry + audit
- policy rejection → audit + suppression
- stopping-rule suppression → audit + no execution
- duplicate recovery action → idempotent no-op
- network failure → audit + retry
- sweep overlap (two sweeps) → lock / reject

---

## Security

- **Never hard-code keys** — .env.example only
- **Frontend holds no secrets** — PostgreSQL is single source of truth
- **Verify webhook signatures** before parsing
- **Validate all external input**
- **Treat LLM output as untrusted**
- **Server-side authorization** for every financial action
- **Redact PII** before LLM or logs
- **Test mode only, everywhere**

---

## Testing & Definition of Done

**Test Focus**:
1. Policy engine — table-driven, exhaustive (crown jewel)
2. Stopping rules — its own file, table-driven
3. Idempotency — duplicate webhook produces one record, one action
4. LLM output validation — malformed, hostile, out-of-range
5. Strategy math — expected net recovery, argmax among allowed
6. One full end-to-end happy path

**Milestone DONE**:
- Tests pass
- Behavior verified against actual database (not mocks)
- Docs updated
- Committed

**Never claim something works when mocked** — say "mocked" out loud.

---

## DEMO Acceptance Test (What Gets Green)

**Build to make THIS green before anything else**:
1. `payment.failed` webhook (insufficient funds, mid-value, retry_count=1)
2. → signature verified → persisted as RevenueLeak, idempotently
3. → ML returns calibrated probability
4. → Claude recommends delayed retry + reminder with cited evidence
5. → simulator ranks five strategies
6. → stopping rules pass
7. → policy returns ALLOW
8. → retry tool executes in Razorpay test mode
9. → outcome recorded as recovered
10. → dashboard counter increments
11. → Decision Dossier exports

If that passes, we have a submission. Everything else is amplification.

---

## CHANGE MANAGEMENT

**Module Coupling**:
- Loose coupling, interfaces everywhere
- Razorpay behind gateway, Claude behind AI service, ML behind prediction service
- Policy and stopping rules pure and isolated
- Never duplicate business logic across frontend and backend

**Change Process**:
1. Inspect existing implementation
2. Determine impact
3. Name the components that change
4. Make smallest safe change
5. Run regression tests
6. Update docs
7. Commit

**Do NOT rewrite working modules without cause.**

---

## MILESTONE ORDER (5 Days)

### Day 1: M0 - Scaffold + Walking Skeleton
- Directory structure, docs, .env.example, docker-compose.yml
- FastAPI app with fake services through complete pipeline
- One dashboard tile, seeded demo cases

### Day 2: M1-M3b - Core Infrastructure
- PostgreSQL schema + migrations
- Razorpay webhook + signature verification
- Persistence + idempotency (double-webhook test)
- Abandonment sweep detector (second leak source)

### Day 3: M4-M6 - ML + AI Layer
- XGBoost + calibration + eval + model card
- Claude structured reasoning + validation + PII redaction
- Strategy simulator (expected net recovery, argmax)

### Day 4: M7-M9 - Governor + Measurement
- Policy engine + StoppingRules, versioned + tested
- Governed, idempotent tools in test mode
- BatchRecoveryRun + holdout control + uplift report

### Day 5: M10-M11 - Frontend + Demo
- Dashboard (3 pages) + Decision Dossier export
- Demo/replay mode + e2e + README + ADRs + Loom
- **Only then**: Live pipeline view, Hinglish drafts, subscription detector

**If Day 4 slips, sacrifice Day 5 frontend polish — never the batch measurement.**

---

## WHAT GETS US SELECTED (The repo is the résumé)

1. **README** opening with one-liner, then table mapping each track bar clause to where it lives in the code
2. **Architecture, spec, plan docs** kept current
3. **ADRs** — short decision records: why policy-over-LLM, why holdout, why two live detectors, why n8n off critical path, why calibration matters
4. **Small, meaningful commits** with milestone tags
5. **60–90s Loom in README**
6. **Honest "limitations & next steps"** — synthetic data, small control group, two of four sources live, bandit-based selection future work

**Judges reward clarity, honesty, and measured value. Don't overclaim.**