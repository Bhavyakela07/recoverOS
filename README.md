# AI Revenue Recovery Agent

An AI-powered system that analyzes failed and at-risk payment transactions, figures out *why* they failed, prioritizes which ones are worth recovering, decides the best recovery action, and writes a personalized customer message to win the revenue back.

Built for the **Razorpay AI Buildathon 2026**.

> ⚠️ **Disclaimer:** All transaction and customer data in this project is **synthetically generated** for demonstration purposes only. No real payment or customer data is used, stored, or transmitted anywhere. This project is **not officially affiliated with or connected to Razorpay** — it does not use the real Razorpay API and does not process real payments.

---

## Table of Contents

1. [Problem Statement](#problem-statement)
2. [Motivation](#motivation)
3. [Solution](#solution)
4. [Key Features](#key-features)
5. [Architecture](#architecture)
6. [Technology Stack](#technology-stack)
7. [Project Structure](#project-structure)
8. [How the AI Agent Works](#how-the-ai-agent-works)
9. [How Recovery Priority Is Calculated](#how-recovery-priority-is-calculated)
10. [Machine Learning Approach](#machine-learning-approach)
11. [Dataset](#dataset)
12. [Installation](#installation)
13. [Environment Variables](#environment-variables)
14. [How to Run](#how-to-run)
15. [Screenshots](#screenshots)
16. [Example Workflow](#example-workflow)
17. [Future Improvements](#future-improvements)
18. [Limitations](#limitations)

---

## Problem Statement

Every day, a meaningful share of online payments fail — due to insufficient funds, declined cards, expired cards, network glitches, or authentication timeouts. Most businesses treat every failed payment the same way (or don't follow up at all), which means:

- High-value, easily-recoverable transactions get no special attention.
- Customers who could have completed the payment with a simple nudge never receive one.
- Revenue that could have been recovered with the right message, at the right time, is silently lost.

## Motivation

Payment failure isn't a single problem — it's several different problems wearing the same mask ("Failed"). A network blip needs a retry. An expired card needs the customer to act. Insufficient funds needs patience and a gentle nudge. Treating all of these identically wastes recovery effort and annoys customers with the wrong kind of follow-up.

## Solution

**AI Revenue Recovery Agent** treats failed-payment recovery as a pipeline:

```
Failed Payment
     │
     ▼
AI Analysis (classify failure reason, compute recovery score)
     │
     ▼
Recovery Priority (High / Medium / Low)
     │
     ▼
AI Agent Decision (best recovery action, explainable)
     │
     ▼
Personalized Customer Message (LLM-generated, with fallback)
     │
     ▼
Potential Revenue Recovered
```

Every step is transparent and explainable — there is no unexplained black-box decision anywhere in the pipeline.

## Key Features

- 📊 **Interactive Streamlit dashboard** — metrics, charts, filters, and drill-downs.
- 🧠 **Rule-based Recovery Priority Score** (0–100) with a fully documented formula.
- 🤖 **Explainable AI Decision Agent** — recommends one of 6 recovery actions, always with a plain-language reason.
- 🔬 **Scikit-learn ML model** — predicts the probability a failed transaction will actually recover if retried, trained on historical outcomes.
- ✍️ **LLM-powered personalized messages** — unique per customer, with an automatic template-based fallback if no API key is set.
- 💰 **Revenue recovery estimation** — total, successful, failed, and potential recoverable revenue, plus recovery rate.
- 🔎 **Transaction Explorer** with a full detail view per transaction.
- 🔐 **No hard-coded secrets** — API key loaded from `.env`, safe fallback mode built in.

## Architecture

```
┌─────────────────┐     ┌────────────────────┐     ┌───────────────────┐
│  data/           │────▶│  agents/analyzer.py │────▶│  agents/decision_  │
│  payments.csv    │     │  (priority scoring)  │     │  agent.py (action) │
└─────────────────┘     └────────────────────┘     └─────────┬──────────┘
        │                          ▲                          │
        │                          │                          ▼
        │               ┌──────────┴─────────┐     ┌────────────────────┐
        │               │ models/             │     │ agents/message_    │
        │               │ recovery_model.py    │     │ generator.py (LLM) │
        │               │ (ML probability)     │     └─────────┬──────────┘
        │               └──────────────────────┘               │
        ▼                                                       ▼
┌────────────────────────────────────────────────────────────────────┐
│                          app.py (Streamlit UI)                       │
│   Dashboard │ Transaction Explorer │ AI Recovery Center │ Analytics  │
└────────────────────────────────────────────────────────────────────┘
```

## Technology Stack

- **Python 3.11+**
- **Streamlit** — dashboard/frontend
- **Pandas / NumPy** — data processing
- **Scikit-learn** — recovery-likelihood classification model
- **Plotly** — interactive charts
- **OpenAI API** — personalized message generation (optional, with fallback)
- **python-dotenv** — environment variable management
- **joblib** — model persistence

## Project Structure

```
ai-revenue-recovery-agent/
│
├── app.py                      # Streamlit dashboard (entry point)
├── requirements.txt
├── README.md
├── .gitignore
├── .env.example
│
├── data/
│   ├── generate_data.py        # synthetic dataset generator
│   └── payments.csv            # generated demo dataset
│
├── agents/
│   ├── __init__.py
│   ├── analyzer.py              # recovery priority scoring + explanations
│   ├── decision_agent.py        # explainable action recommendation
│   └── message_generator.py     # LLM + template message generation
│
├── models/
│   ├── __init__.py
│   ├── recovery_model.py        # RecoveryModel class (train/predict/save/load)
│   ├── train_model.py           # training script
│   └── recovery_model.pkl       # saved trained model (generated)
│
├── utils/
│   ├── __init__.py
│   └── data_processor.py        # loading, metrics, filters
│
└── assets/
```

## How the AI Agent Works

The "AI Agent" here is deliberately **two cooperating pieces**, not one opaque model — this makes the whole system explainable end-to-end:

1. **Rule-based Recovery Priority Score** (`agents/analyzer.py`) — a transparent weighted formula (see below) that scores *how much this transaction is worth recovering*.
2. **ML Recovery Likelihood Model** (`models/recovery_model.py`) — a RandomForestClassifier that estimates *how likely a retry is to actually succeed*, learned from historical outcomes.
3. **Decision Agent** (`agents/decision_agent.py`) — a rule engine that combines the priority, the failure reason, the retry count, and the ML probability to pick one of six recovery actions, and writes a one-sentence justification for it.
4. **Message Generator** (`agents/message_generator.py`) — takes the decision agent's chosen action and generates a personalized message via an LLM (or a varied template if no API key is configured).

Nothing in this pipeline is a black box — every score and every recommendation comes with a human-readable "why."

## How Recovery Priority Is Calculated

`agents/analyzer.py` computes a **Recovery Priority Score (0–100)** as a weighted sum of five factors:

| Factor | Weight | Logic |
|---|---|---|
| Transaction amount | 40% | Normalized against the largest transaction in the dataset — bigger amounts matter more |
| Failure reason recoverability | 25% | E.g. Network Failure (0.90) is much easier to recover than Unknown Error (0.25) |
| Customer segment | 15% | Premium (1.0) > Regular (0.65) > New (0.35) |
| Customer history | 10% | Loyal Customer (1.0) > Regular Customer (0.75) > Occasional Buyer (0.45) > New Customer (0.2) |
| Retry count | 10% | 0 retries = 1.0 (fresh, worth trying), 3+ retries = 0.2 (diminishing returns / customer fatigue) |

The final score buckets into:
- **High Priority** ≥ 65
- **Medium Priority** 40–64
- **Low Priority** < 40

Every transaction also gets a generated explanation, e.g.:
> "High Priority (score 78.4/100) because the transaction value is high, the failure reason ('Network Failure') is usually easy to recover from, the customer belongs to the Premium segment, the customer has a reliable history (Loyal Customer), and no retries have been attempted yet."

## Machine Learning Approach

**Why ML is used here (and not just for show):** the rule-based score tells you *which* transactions to prioritize, but not *how likely* a retry is to actually work. That's a genuinely different, learnable signal — so a small, explainable classifier complements the rules instead of duplicating them.

- **Model:** `RandomForestClassifier` (scikit-learn) — chosen for interpretability via feature importances and because it needs no feature scaling.
- **Target:** `recovered_after_retry` — whether a historically failed transaction was eventually recovered (simulated in the synthetic dataset, standing in for real-world outcome data you'd have in production).
- **Features:** `amount`, `retry_count` (numeric) + one-hot encoded `payment_method`, `failure_reason`, `customer_segment`, `customer_history`.
- **Leakage avoidance:** only failed transactions with a known outcome are used for training; successful transactions (which have no retry outcome) are excluded from the training set entirely.
- **Train/test split:** 75/25, stratified on the target so both classes appear in both splits.
- **Evaluation metrics printed on every training run:** accuracy, precision, recall, F1-score, ROC-AUC.
- **Persistence:** the trained model (and the exact one-hot column layout it was trained on) is saved with `joblib` to `models/recovery_model.pkl`, and loaded by the Streamlit app at runtime.

Run `python models/train_model.py` to retrain and see metrics printed to the terminal.

## Dataset

`data/generate_data.py` generates a synthetic dataset of ~650 Indian payment transactions across 220 synthetic customers, with:

- `transaction_id`, `customer_id`, `customer_name`
- `amount` (INR, realistic ranges by customer segment)
- `currency`, `payment_method` (UPI, Credit Card, Debit Card, Netbanking, Wallet)
- `transaction_date` (last 90 days)
- `payment_status` (Success / Failed)
- `failure_reason` (7 categories, only set for failed transactions)
- `customer_history`, `customer_segment`
- `retry_count`
- `recovered_after_retry` — historical outcome label used to train the ML model

All names, amounts, and outcomes are **fabricated** — no real customer or payment data is used.

## Installation

```bash
# 1. Clone or copy the project
cd ai-revenue-recovery-agent

# 2. Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate        # on Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
```

## Environment Variables

Copy the example file and (optionally) add your OpenAI API key:

```bash
cp .env.example .env
```

`.env`:
```
OPENAI_API_KEY=your_api_key_here
```

**The app works without this key.** If it's missing or invalid, `agents/message_generator.py` automatically falls back to a varied, template-based message generator so the full app still runs end-to-end.

## How to Run

```bash
# 1. Generate the synthetic dataset
python data/generate_data.py

# 2. Train the ML recovery-likelihood model
python models/train_model.py

# 3. Launch the dashboard
streamlit run app.py
```

The app opens at `http://localhost:8501`.

### GitHub commands

```bash
git init
git add .
git commit -m "Initial commit: AI Revenue Recovery Agent"
git branch -M main
git remote add origin https://github.com/<your-username>/ai-revenue-recovery-agent.git
git push -u origin main
```

### Testing instructions

There's no real payment gateway involved, so "testing" here means verifying the pipeline runs cleanly:

```bash
# Sanity-check every file compiles
python -m py_compile app.py agents/*.py models/*.py utils/*.py data/generate_data.py

# Confirm the full pipeline (data -> scoring -> ML -> decision -> message) runs without errors
python -c "
from utils.data_processor import load_data, compute_summary_metrics
from agents.analyzer import analyze_failed_transactions
df = load_data('data/payments.csv')
df = analyze_failed_transactions(df)
print(compute_summary_metrics(df))
"
```

### Common errors and fixes

| Error | Fix |
|---|---|
| `FileNotFoundError: data/payments.csv` | Run `python data/generate_data.py` first |
| Model warnings / `ML recovery model not trained yet` banner in sidebar | Run `python models/train_model.py` |
| `ModuleNotFoundError` for any package | Run `pip install -r requirements.txt` inside your active virtual environment |
| LLM messages always show "Template fallback" | Check `.env` has a valid `OPENAI_API_KEY` and that `python-dotenv`/`openai` are installed |
| Streamlit shows a blank/old dashboard after code changes | Press `R` in the running app, or restart with `streamlit run app.py` |

## Screenshots

*(Add screenshots here after running the app locally)*

- `assets/dashboard.png` — Dashboard overview
- `assets/transaction_detail.png` — Transaction detail + AI analysis
- `assets/recovery_center.png` — AI Recovery Center

## Example Workflow

1. Open the **Dashboard** — see 650 synthetic transactions, ~445 successful, ~205 failed, with a recovery rate estimate.
2. Go to **Transaction Explorer**, pick a failed transaction (e.g. a ₹1,930 UPI payment declined by the bank).
3. See its **Recovery Score**, **Priority**, and a plain-English explanation of why.
4. See the **AI Decision Agent's** recommended action (e.g. "Ask Customer to Update Payment Method") with its reasoning.
5. Click **"Generate AI Recovery Message"** — get a unique, personalized message ready to send.
6. Go to **AI Recovery Center** to see all High-Priority cases ranked and batch-generate messages for the top few.
7. Check **Analytics** for the ML model's feature importances and the recovery-rate trend over time.

## Future Improvements

- Real Razorpay Webhook integration to ingest live failed-payment events (currently out of scope — see Disclaimer).
- A/B testing different message tones and tracking actual recovery outcomes to close the feedback loop.
- SMS/WhatsApp delivery channels alongside the generated message.
- Multi-language message generation for regional customers.
- A more advanced ML model (gradient boosting) once real historical outcome data is available at scale.

## Limitations

- All data is synthetic; recovery outcomes and probabilities are illustrative, not real-world calibrated.
- The ML model is trained on simulated (not real) outcome labels, so its metrics describe internal consistency of the simulation, not real-world accuracy.
- No real payment gateway, webhook, or Razorpay API integration is implemented in this version.
- The LLM message generator depends on an external API; without a key it uses templates, which are less varied than true LLM output.

---

*This project is a demo built for the Razorpay AI Buildathon 2026. It is an independent project and is not an official Razorpay product.*
