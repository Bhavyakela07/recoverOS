# RecoverOS Specification

**Spec v1.0.0 – 2026-08-29**

---

## Overview

This document defines the API contracts, business logic specifications, and behavioral requirements for RecoverOS. All interfaces use Pydantic v2 schemas as the single source of truth.

---

## Vocabulary Discipline (Cheap, High-Scoring)

Use the track's own words as section headings, UI labels, API names, and README anchors:

- **revenue at risk** — primary entity
- **bounded** — autonomous constraint
- **measured money recovered** — core metric
- **across a batch** — required measurement scope
- **compliant escalation** — human review with audit
- **stopping rules** — first-class module
- **close the loop** — detection-to-recovery pipeline

---

## API Contracts

### Base URL
```
http://localhost:8000
```

### Content Type
```
application/json
```

---

## Core Endpoints

### Health Check

**GET** `/health`

**Response** (200 OK):
```json
{
  "status": "healthy",
  "services": {
    "detector": "fake",
    "prediction": "fake",
    "ai": "fake",
    "strategy": "fake",
    "razorpay": "fake (test mode)",
    "policy": "REAL (deterministic)",
    "tools": "governed + idempotent"
  },
  "policy_version": "v1.0.0",
  "timestamp": "2026-08-29T00:00:00Z"
}
```

---

### BatchRecoveryRun

**POST** `/batch/recovery`

Request body (DemoInjectRequest):
```json
{
  "seed": 42,
  "case_count": 50,
  "holdout_ratio": 0.15,
  "include_suppressed": true,
  "include_human_review": true,
  "include_denied": true
}
```

**Response** (200 OK):
```json
{
  "cases_detected": 50,
  "revenue_at_risk": "₹523,450.00",
  "treatment_count": 42,
  "control_count": 8,
  "recovery_rate_treatment": "12.3%",
  "recovery_rate_control": "8.1%",
  "incremental_recovery_rate_pp": "4.2%",
  "measured_money_recovered": "₹64,384.35",
  "incremental_revenue": "₹21,984.90",
  "intervention_cost": "₹210.00",
  "net_recovered": "₹21,774.90",
  "cost_per_rupee_recovered": "₹0.01",
  "guardrail_metrics": {
    "suppression_rate": "2.4%",
    "human_review_rate": "14.3%",
    "policy_block_rate": "7.1%",
    "opt_out_rate": "0.0%",
    "repeat_contact_rate": "0.0%"
  }
}
```

**Note**: Every projected figure is labeled SIMULATED. Distinguish rigorously between EXPECTED (model projection) and MEASURED (observed outcome).

---

### List Cases

**GET** `/cases`

Query params:
- `is_control` (boolean): filter by control group
- `leak_source` (string): filter by leak source
- `page` (integer, default 1)
- `page_size` (integer, default 20)

**Response** (200 OK):
```json
{
  "cases": [
    {
      "case_id": "case_abc123",
      "leak": {
        "id": "leak_abc",
        "leak_source": "payment_failure",
        "customer_id": "cust_1001",
        "amount": "1500.00",
        "failure_category": "insufficient_funds",
        "failure_reason": "insufficient_funds",
        "retry_count": 1
      },
      "policy_decision": {
        "decision": "allow",
        "reason": "action_not_permitted",
        "policy_version": "v1.0.0",
        "details": {"checks": "all_passed"}
      },
      "status": "allow",
      "is_control": false
    }
  ],
  "total": 50,
  "page": 1,
  "page_size": 20
}
```

---

### Case Detail

**GET** `/cases/{case_id}`

**Response** (200 OK):
```json
{
  "case_id": "case_abc123",
  "leak": { ... },
  "customer": { ... },
  "prediction": { ... },
  "ai_recommendation": { ... },
  "strategies": [ ... ],
  "policy_decision": { ... },
  "stop_decision": { ... },
  "action_result": { ... },
  "is_control": false,
  "created_at": "2026-08-29T00:00:00Z"
}
```

---

### Decision Dossier

**GET** `/cases/{case_id}/dossier`

One-click export — full audit trail.

**Response** (200 OK):
```json
{
  "case_id": "case_abc123",
  "leak": { ... },
  "customer": { ... },
  "prediction": { ... },
  "ai_recommendation": { ... },
  "strategy_options": [ ... ],
  "selected_strategy": { ... },
  "stopping_rules_check": {
    "stop": false,
    "rule": null,
    "explanation": "No stopping rules triggered"
  },
  "policy_decision": { ... },
  "action_result": { ... },
  "audit_timeline": [
    {"event": "leak_detected", "timestamp": "..."},
    {"event": "leak_verified", "timestamp": "..."},
    {"event": "prediction_generated", "timestamp": "..."},
    {"event": "ai_analysis_generated", "timestamp": "..."},
    {"event": "strategy_simulated", "timestamp": "..."},
    {"event": "policy_checked", "decision": "allow"},
    {"event": "action_executed", "result": { ... }}
  ]
}
```

---

### Demo Injection

**POST** `/demo/inject`

Deterministic demo population injection.

**Request**:
```json
{
  "seed": 42,
  "case_count": 50,
  "holdout_ratio": 0.15
}
```

---

### Demo Replay

**GET** `/demo/replay`

Returns curated demo cases including:
- **ALLOW** — recovers successfully
- **HUMAN_REVIEW** — paused for human review
- **DENY** — policy blocks action
- **SUPPRESSED** — stopped by rule
- **CONTROL** — holdout case (no intervention)

---

## Data Models

### RevenueLeak

```json
{
  "id": "string",
  "leak_source": "payment_failure | checkout_abandonment | subscription_failure | overdue_receivable",
  "payment_id": "string | null",
  "order_id": "string | null",
  "invoice_id": "string | null",
  "customer_id": "string",
  "amount": "Decimal",
  "currency": "INR",
  "failure_category": "enum",
  "failure_reason": "string | null",
  "retry_count": 0,
  "detected_at": "datetime",
  "created_at": "datetime"
}
```

### AIRecommendation

```json
{
  "leak_diagnosis": "<=280 chars, plain language>",
  "failure_category": "enum",
  "recommended_action": "retry | reminder | incentive | follow_up | escalate | none",
  "confidence": 0.0-1.0,
  "reason_codes": ["enum", ...],
  "evidence": [{"signal": "string", "value": "string"}],
  "customer_message_draft": "string | null",
  "message_language": "en | hinglish | regional",
  "requires_human_review": true | false
}
```

### PolicyResult

```json
{
  "decision": "allow | deny | human_review | suppress",
  "reason": "policy reason code",
  "policy_version": "v1.0.0",
  "stopping_rule_triggered": "enum | null",
  "details": {}
}
```

### StrategyOption

```json
{
  "action": "retry | reminder | incentive | follow_up | escalate | none",
  "expected_recovery": "Decimal",
  "intervention_cost": "Decimal",
  "expected_net_recovery": "Decimal",
  "probability_weighted": "Decimal",
  "policy_allowed": true | false,
  "stopped_by_rule": "enum | null",
  "simulated": true
}
```

---

## Business Logic Specifications

### Detection

**PaymentFailure Detector**:
1. Receive Razorpay webhook `payment.failed`
2. Verify X-Razorpay-Signature (HMAC-SHA256 over raw body with webhook secret)
3. Reject on mismatch
4. Parse and persist as RevenueLeak
5. Return existing record on duplicate (UNIQUE constraint on event id)

**CheckoutAbandonment Detector**:
1. Scheduled sweep (APScheduler)
2. Find orders created but no terminal payment after N minutes (default N=30)
3. Persist as RevenueLeak with leak_source=checkout_abandonment

### Recovery Probability (ML)

**Model**: XGBoost with calibration

**Training**:
- Seeded synthetic dataset (not a giant CSV)
- Features: amount, payment_method, failure_code, leak_source, retry_count, customer historical success rate, prior successes/failures, time_since_leak, hour/day, alternate-method availability
- Output: recovery_probability [0,1], risk_score [0,1]
- Calibration: isotonic or Platt

**Evaluation Metrics**:
- precision, recall, F1, ROC-AUC
- calibration curve / Brier score
- Model card in docs/

**Fallback**: If training slips, ship calibrated logistic regression behind PredictionService.predict. Nothing downstream blocks on ML.

### Strategy Simulation

For each leak, simulate at least five strategies:

| Strategy | Expected Recovery | Intervention Cost | Expected NET Recovery |
|----------|------------------|-------------------|----------------------|
| retry | recovery_prob × amount | $0.50 | ... |
| reminder | recovery_prob × amount | $1.00 | ... |
| incentive | recovery_prob × amount | $50.00 | ... |
| follow_up | recovery_prob × amount | $5.00 | ... |
| escalate | recovery_prob × amount | $100.00 | ... |
| none | $0 | $0 | $0 |

**Selection**: argmax(expected_net_recovery) among policy-allowed, non-stopped options. Governor first, optimizer second.

### Policy Engine

**Decision Logic** (in priority order):
1. Stopping rules check → SUPPRESS if triggered
2. Consent check → DENY if no consent
3. Action permitted → DENY if not
4. Amount limit → HUMAN_REVIEW if exceeded
5. Recovery probability threshold → DENY if below threshold
6. Risk score ceiling → DENY if above ceiling
7. Retry count limit → HUMAN_REVIEW if exhausted
8. Contact caps → DENY if exceeded
9. Quiet hours → DENY if outside
10. Mandate limits → DENY/HUMAN_REVIEW if exceeded
11. Action budget → DENY if exceeded

**Output**: ALLOW, DENY, or HUMAN_REVIEW with machine-readable reason.

### Stopping Rules (First-Class Module)

Rules checked independently:
1. **max_retry_attempts**: retry_count >= max_retries (default: 3)
2. **contact_cap**: 24h or 7d contact count exceeded
3. **quiet_hours**: Current hour within no-contact window (9PM–8AM)
4. **min_expected_net_recovery**: Net recovery < threshold
5. **min_recovery_probability**: Probability < threshold (default: 15%)
6. **opt_out**: Customer has withdrawn consent
7. **fraud_signal**: Risk score >= threshold (default: 85%)
8. **cooldown**: Not enough time since last attempt
9. **action_budget**: Global per-run action budget exceeded

**Output**: StopDecision(stop: bool, rule: enum, explanation: str)

**SUPPRESS** is a first-class terminal outcome — not an error.

### Idempotency

**Critical for demo**:
- Razorpay event id stored with UNIQUE constraint
- Duplicate webhook = no-op, returns existing result
- Every write tool takes idempotency key
- Retried tool call never double-charges or double-messages
- Test must fire identical webhook twice → assert one record, one action

### Consent & Compliance

- Never store raw card data or CVV (rely on Razorpay tokenization)
- Recurring payments respect RBI e-mandate / AFA constraints (policy inputs)
- Honor consent and opt-out on every outbound message
- PII redacted before LLM — only ids, amounts, categories, aggregates
- All figures labeled SIMULATED in UI

---

## Error Handling Specification

Handle explicitly, each with defined fallback AND audit entry:

| Error | Fallback | Audit Entry |
|-------|----------|-------------|
| duplicate webhook | no-op (return existing) | idempotent_ack |
| invalid signature | reject | signature_failed |
| Razorpay API failure | retry + audit | api_failure |
| Claude timeout | deterministic fallback | ai_timeout |
| invalid Claude JSON | repair → deterministic | ai_invalid |
| ML unavailable | logistic regression | ml_fallback |
| DB failure | retry + audit | db_failure |
| policy rejection | audit + suppression | policy_blocked |
| stopping-rule suppression | audit + no execution | suppressed |
| duplicate action | idempotent no-op | idempotent_ack |
| network failure | retry + audit | network_failure |
| sweep overlap | reject second | sweep_overlap |

---

## Testing Specification

**Pytest Focus**:
1. Policy engine — table-driven, exhaustive
2. Stopping rules — table-driven, own file
3. Idempotency — duplicate webhook produces one record, one action
4. LLM output validation — malformed, hostile, out-of-range
5. Strategy math — expected net recovery, argmax among allowed
6. One full end-to-end happy path

**Test Data**:
- Synthetic datasets with seeded random generators
- Deterministic demo cases: ALLOW, HUMAN_REVIEW, DENY, SUPPRESSED, CONTROL

---

## Security Specification

- Keys via environment variables only (.env.example committed, .env.gitignored)
- Never expose secrets to frontend
- Verify webhook signatures before parsing
- Validate all external input
- Treat LLM output as untrusted input
- Server-side authorization for every financial action
- Redact PII before LLM or logs
- Test mode only everywhere (rzp_test_ keys)

---

## Demo Requirements

**The Demo** (3 minutes max):
- Build DEMO/REPLAY MODE: seeded injector that deterministically pushes curated population through full live pipeline
- Curated set includes: ALLOW, HUMAN_REVIEW, DENY, SUPPRESSED, CONTROL cases
- Script follows: 0:00 leak → 0:25 batch → 0:55 money slide → 1:30 case detail → 2:00 thesis moment → 2:35 dossier → 2:50 close

---

## Definition of Done

A milestone is DONE only when:
- Tests pass
- Behavior verified against actual database (not mocks)
- Docs updated
- Committed

**Never claim something works when it is mocked** — say "mocked" out loud.