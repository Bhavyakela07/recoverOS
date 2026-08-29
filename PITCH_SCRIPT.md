# 5-Minute Pitch / Demo Script — AI Revenue Recovery Agent

*Razorpay AI Buildathon 2026*

---

**[0:00–0:40] Hook + Problem**

"Every business running online payments loses revenue not because customers don't want to pay — but because a payment failed and nobody followed up the right way. A network blip, an expired card, insufficient funds — these get treated identically today: either ignored, or hit with the same generic retry. That's revenue leakage that's completely avoidable.

We built the **AI Revenue Recovery Agent** — a system that looks at every failed payment, figures out *why* it failed, decides *if* it's worth recovering and *how*, and writes a personalized message to win that revenue back."

**[0:40–1:30] What it does (live demo: Dashboard)**

"Here's our dashboard, running on a synthetic dataset of 650 Indian payment transactions. At a glance: total transactions, successful vs failed, and — this is the key number — **potential recoverable revenue**. Right now we're looking at roughly [X]% of failed revenue as recoverable, not by guessing, but by an explainable AI pipeline underneath.

You can see failure reasons breaking down — card declines, insufficient funds, network failures — and priority distribution across High, Medium, and Low."

**[1:30–2:45] The AI pipeline (Transaction Explorer)**

"Let's drill into one failed transaction. [Select one in Transaction Explorer.]

First, our **Recovery Priority Score** — a transparent, weighted formula factoring in transaction amount, how recoverable this specific failure reason typically is, the customer's segment and history, and how many retries have already happened. Nothing hidden — you can see exactly why this scored a 78 and got marked High Priority.

Second, a **Scikit-learn RandomForest model** trained on historical recovery outcomes estimates the actual probability a retry succeeds — here, 71%.

Third, our **Decision Agent** — a rule engine, not a black box — combines all of that and recommends: 'Ask Customer to Update Payment Method,' with a one-sentence explanation of why. Every recommendation is justified, every time."

**[2:45–3:45] Personalized recovery message (live demo)**

"Now the part that actually reaches the customer. [Click 'Generate AI Recovery Message'.]

This calls an LLM to write a short, warm, professional message personalized to this exact customer, amount, and failure reason — not a copy-pasted template. And critically: if the API key isn't available, or the call fails, the app **automatically falls back** to a varied template engine so the whole system keeps working. No single point of failure."

**[3:45–4:30] AI Recovery Center + Analytics**

"In the AI Recovery Center, we surface every High-Priority case ranked by score, and can batch-generate recovery messages for the top cases in one click — this is what an ops or growth team would actually use day to day.

And in Analytics, we show the ML model's feature importances and a recovery-rate trend — so this isn't just a UI, there's a real trained model backing the numbers, with proper train/test evaluation: accuracy, precision, recall, ROC-AUC, all logged."

**[4:30–5:00] Close**

"To be clear — this runs on fully synthetic demo data, and it's not connected to Razorpay's live systems. But the architecture is built to plug in: swap the synthetic dataset for a real failed-payment webhook feed, and this pipeline — analysis, priority, ML probability, explainable decision, personalized outreach — works exactly the same way.

The core idea: **stop treating every failed payment the same way.** Score it, explain it, act on it, and recover the revenue that was never actually lost — just unclaimed. Thank you."

---

### Anticipated Q&A

**Q: Is this connected to real Razorpay data?**
A: No — synthetic demo data only, clearly labeled throughout the app. The architecture is designed so a real payment-failure feed could be plugged in later.

**Q: Why RandomForest and not a deep learning model?**
A: Interpretability. Feature importances let us explain *why* the model predicts a given recovery probability — important for a finance-adjacent decision, and appropriate given the dataset size.

**Q: What happens if the LLM API is down or the key is missing?**
A: The message generator automatically falls back to a template engine that still varies message wording per transaction — the app never breaks or blocks on the LLM call.

**Q: How is the priority score different from the ML model?**
A: The priority score answers "how much is this worth recovering" (a transparent business formula). The ML model answers "how likely is a retry to actually work" (a learned probability from historical outcomes). The Decision Agent combines both.
