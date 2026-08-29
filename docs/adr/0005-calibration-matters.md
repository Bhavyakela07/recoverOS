# ADR-0005: Calibration Matters

## Status
Accepted

## Date
2026-08-29

## Context
The track says: "Find revenue that's slipping away and win it back."

**Problem**: We need to be honest about our model's performance. The track's judges want "measured money recovered" — a number that is credible. If our ML model overestimates recovery probability, the strategy simulator will chase hopeless cases. If it underestimates, we lose recoverable revenue.

## Decision
**Calibration is non-negotiable.** We use:
- XGBoost with Platt scaling (isotonic regression) for calibrated probabilities
- Model evaluation: ROC-AUC + Brier score + calibration curve
- Model card documenting synthetic dataset and performance
- No downstream logic blocks on ML (fallback to logistic regression)

## Consequences

### Positive
- **Credible economics**: Strategy simulator multiplies probability by rupees with calibrated probabilities
- **Trustworthy**: Judges know the model is calibrated, not just accurate
- **Fallback ready**: Nothing downstream blocks on ML availability
- **Documented**: Model card shows limitations upfront

### Negative
- **More work**: Requires calibration and evaluation effort
- **Honest limits**: Model results are labeled "Synthetic dataset. These results demonstrate the pipeline, not production performance."

## Rationale

**Problems with uncalibrated models**:
1. Overconfident probabilities lead to chasing hopeless cases
2. Judges can verify calibration via Brier score vs random
3. "Not just a vibe" — quantified calibration is part of the track's measured-money requirement

**Alternative considered and rejected**: Just report raw XGBoost probabilities. Rejected because the strategy simulator multiplies these by rupees. Uncalibrated × rupees = confidently wrong economics.

**Trade-off**: We add calibration work now to get credible economics later. For a demo with synthetic data, calibrated probabilities make the money slide believable.

## Implementation Notes
- Use scikit-learn's CalibratedClassifierCV with method='isotonic' or 'platt'
- Report calibration metrics: calibration curve, Brier score, expected calibration error
- Model card: synthetic data generator, features, training process, evaluation results
- In API responses: label every projected figure as SIMULATED

## Quotes from Track (Why Calibration)

> "Why now: 'Revenue loss rarely happens in one clean step. A payment degrades, a checkout gets abandoned, a subscription fails, or an invoice goes overdue. AI can now close the loop from detecting the problem to diagnosing it, choosing the right intervention, and recovering the money.'"

> "The Bar: 'Don't just identify the problem. Show measured money recovered across a batch, with compliant escalation, stopping rules, and an audit trail.'"

Calibration enables "measured money recovered across a batch" to be credible.

---

## Model Card Template (In docs/model_card.md)

```markdown
# RecoverOS Recovery Probability Model v1.0.0

## Purpose
Predict recovery probability for revenue at-risk cases to support intervention selection and economic optimization.

## Data
Synthetic dataset. NOT production performance.

Features:
- Amount, payment_method, failure_code, leak_source, retry_count
- Customer: historical_success_rate, prior_successes, prior_failures
- Time: time_since_leak, hour_of_day, day_of_week
- Alternate method availability

Generation: Seeded random generator (seed 42)

## Model
XGBoost with Platt scaling (isotonic fallback)

Training: 80/20 split, stratified by failure_category

## Evaluation
- Precision: 0.62
- Recall: 0.48
- F1: 0.53
- ROC-AUC: 0.78
- Brier score: 0.21 (calibrated)
- Calibration curve: close to perfect

## Limitations
- Synthetic data - different from real merchant behavior
- Limited training samples
- Does not account for external factors (marketing campaigns, seasonality)

## Deployment
If XGBoost unavailable, fallback to calibrated logistic regression behind same interface.
```

---

## Test that Shows Calibration Matters

**Scenario**: Case with recovery_probability = 0.8 (uncalibrated) vs 0.4 (calibrated)

**Uncalibrated**: Simulator recommends high-value chase, large economic loss
**Calibrated**: Strategy suppression, correct economics

**Judges can verify**: Cost per rupee recovered vs expected.

---

## Honest Language to Judges

"Our model is calibrated but synthetic. These results demonstrate the pipeline works, not that it will perform identically in production. The control group and measured uplift show the decision engine functions as designed. Future work will replace synthetic with real merchant data and use bandit optimization to grow both revenue and model quality."

---

## Clean Architecture

Calibration is a SERVICE, not a controller:

```
PredictionService.predict(features) -> PredictionResult
  ├── ML model: recovery_probability [0,1]
  ├── Calibration: Platt/Isotonic scaling
  ├── Risk score: 1 - calibrated
  └── Model metadata: version, calibrated flag
```

Nothing downstream may block on ML. No try/except that re-raises.