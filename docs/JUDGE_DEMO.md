# 📖 RecoverOS — Judge Demo Playbook & Q&A Guide

**Razorpay AI Buildathon 2026 | Track 03: AI Revenue Recovery Agent**

---

## 🚀 Quick Launch Commands

Open two terminal windows in `/Users/bhavya/recoveros`:

```bash
# Terminal 1: FastAPI Backend Daemon (Port 8000)
source venv/bin/activate
PYTHONPATH=.:backend python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8000

# Terminal 2: Streamlit Web Dashboard (Port 8501)
source venv/bin/activate
PYTHONPATH=.:backend python3 -m streamlit run app.py --server.port 8501
```

---

## 🎙️ 30-Second Introduction Pitch

> *"Hello judges! RecoverOS is an autonomous, policy-governed AI Revenue Recovery Agent built for Track 03 of the Razorpay AI Buildathon.*
> *When payment transactions fail due to bank drops, network timeouts, or expired cards, generic retry bots spam customers or trigger excessive bank decline fees.*
> *RecoverOS solves this with one core thesis: **AI Recommends. Policy Governs.** Our calibrated ML engine predicts recovery probability, but our deterministic Policy Engine decides whether an action is safe, justified, and worth attempting."*

---

## 🎬 4 Demo Scenarios Walkthrough

### Scenario A — Safe Recovery (Order `#RZP-34005`, ₹2,499)
- **Failure Cause:** Transient bank network timeout.
- **AI Prediction:** `p_recovery = 94%` (High likelihood).
- **Policy Engine Evaluation:** IST Active (Not Quiet Hours), 0 prior retries, amount under ₹50k limit.
- **System Action:** **`ALLOW`** $\rightarrow$ Generates 1-click Razorpay payment link (`plink_...`) & dispatches live email to `bhavyakela0009@gmail.com`.

### Scenario B — Safety Block (Fraud / Risk Failure)
- **Failure Cause:** Risk check failure (`payment_risk_check_failed`).
- **Canonical Classification:** `NEVER_FRAUD` / `UNSAFE_STOP`.
- **Policy Engine Evaluation:** Security risk rule triggered.
- **System Action:** **`DO_NOT_RETRY`** $\rightarrow$ Automatic retry strictly blocked to protect merchant reputation.

### Scenario C — Guardrail Block (Order `#RZP-10982`, ₹1,200)
- **Failure Cause:** Insufficient funds after 3 retries.
- **AI Prediction:** `p_recovery = 25%` (Low likelihood).
- **Policy Engine Evaluation:** Exceeded max retry count policy cap.
- **System Action:** **`🛑 DO_NOT_RETRY`** $\rightarrow$ Blocks outreach to prevent customer spam & decline fees.

### Scenario D — Unknown Error (`CUSTOM_999_ERR`)
- **Failure Cause:** Unrecognized or ambiguous error string.
- **Canonical Classification:** `UNKNOWN_HUMAN_REVIEW`.
- **Policy Engine Evaluation:** Fail-closed default logic.
- **System Action:** **`UNKNOWN_HUMAN_REVIEW`** $\rightarrow$ Escalates to human review (no silent network retry conversion).

---

## ❓ Judge Q&A Cheat Sheet

### Q1: "Razorpay already has retry engines. Why is RecoverOS needed?"
> **Answer:** *"Razorpay provides payment infrastructure and APIs. RecoverOS focuses on the governance layer — deciding **when NOT to retry**, enforcing quiet hours, preventing brand damage, handling fraud signals, and managing customer consent. We enhance Razorpay's infrastructure by adding policy-governed decisioning."*

### Q2: "What happens if the AI model makes a mistake?"
> **Answer:** *"The AI model never executes actions directly. Our architecture enforces **Policy-Over-LLM Governance**. If the AI model predicts high recovery but the Policy Engine detects a quiet hour violation or contact cap, the Policy Engine overrides the AI and blocks the action."*

### Q3: "How is Brier score calculated in your ML engine?"
> **Answer:** *"Unlike static demos that hardcode metrics, our ML engine uses an 80/20 train/test holdout split (`train_test_split`). We fit `CalibratedClassifierCV(XGBClassifier, method='isotonic')` on the training set and compute the actual Brier score loss directly from holdout predictions using `sklearn.metrics.brier_score_loss`."*

### Q4: "Is your payment data real or synthetic?"
> **Answer:** *"We believe in 100% engineering honesty. The data is generated using a method-conditioned synthetic generator (`SYNTHETIC_SIMULATION`) to demonstrate calibration and policy rules. It is explicitly disclosed in our UI and README."*

### Q5: "What did you personally build?"
> **Answer:** *"We built the entire closed-loop system: canonical failure mapping layer (`payment_failures.py`), Isotonic XGBoost probability engine (`ml_engine.py`), deterministic policy engine (`policy_engine.py`), Razorpay HMAC webhook receiver, database idempotency tracking, Streamlit executive dashboard, and automated test suite."*
