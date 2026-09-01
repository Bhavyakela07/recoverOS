# 3-Minute Hackathon Demo Script — RecoverOS

**Razorpay AI Buildathon 2026 | Track 03: AI Revenue Recovery Agent**

---

## ⏱️ Timeline & Pitch Flow (3 Minutes)

### [0:00–0:40] Hook & Problem Statement
> "Every merchant running online payments loses revenue not because customers don't want to buy, but because a payment failed due to a bank timeout, network failure, or expired card. Most systems either ignore these failures or blindly spam retry emails, driving up customer fatigue and bank decline fees.
> 
> We built **RecoverOS** — an autonomous, policy-governed AI revenue recovery agent that decides **which failed payments are worth recovering, why an action should be taken, and when to stop**."

---

### [0:40–1:40] Story 1: Recoverable Failed Payment (Closed-Loop Demo)
> *"Let's look at Order #RZP-34005 (₹2,499) in the AI Recovery Center.*
> 
> 1. **Failure Diagnosis**: The payment failed due to a temporary bank network timeout.
> 2. **Calibrated ML Inference**: Our Isotonic-Calibrated XGBoost model estimates a **94% model-estimated recovery probability**.
> 3. **Policy Evaluation**: The Policy Engine checks IST Quiet Hours (outside 22:00-08:00 IST), customer contact caps, and amount limits — issuing a policy decision of **`ALLOW`**.
> 4. **`WHY THIS DECISION?` Card**: Highlights positive signals (*temporary bank failure, high recovery score, customer tier*).
> 5. **Razorpay Test Link & Outreach**: Generates an official Razorpay Test Mode Payment Link (`plink_...`) and formats a personalized email / WhatsApp outreach card.
> 6. **Closed-Loop Outcome**: When the customer pays, Razorpay fires a `payment.captured` webhook. RecoverOS verifies the HMAC signature, enforces database idempotency, transitions the case to **`RECOVERED`**, and updates the recovered revenue on the dashboard!"*

---

### [1:40–2:30] Story 2: The `DO_NOT_RETRY` Case (Financial Safety)
> *"Now look at Order #RZP-10982 (₹1,200).
> 
> 1. **Failure Diagnosis**: Declined due to Insufficient Funds with 3 previous failed retries.
> 2. **Calibrated ML Inference**: Recovery probability drops below 15%.
> 3. **Policy Guardrail**: The Policy Engine triggers a hard stopping rule (`MAX_RETRIES` & `MIN_PROBABILITY`).
> 4. **First-Class Callout**: RecoverOS flags this case as **`🛑 DO_NOT_RETRY`**.
> 5. **LLM Financial Guardrail**: The LLM cannot override this financial decision. RecoverOS stops outreach, saving merchant reputation and preventing bank decline fees."*

---

### [2:30–3:00] Analytics & Technical Polish
> *"In the Analytics tab, we compare our 90% Treatment group against a 10% Control holdout to measure true net recovery uplift.
> 
> Everything in RecoverOS is built with production rigor: HMAC-SHA256 signature verification, `webhook_events.event_id` database idempotency, and clean fallback between Razorpay Test Mode and Demo Mode.
> 
> RecoverOS doesn't just retry payments — it governs recovery with intelligence, safety, and closed-loop verification. Thank you!"*

---

## ❓ Anticipated Q&A

**Q: Is RecoverOS connected to live Razorpay APIs?**  
*A: When `RAZORPAY_KEY_ID` and `RAZORPAY_KEY_SECRET` are provided, RecoverOS uses the official `razorpay` Python SDK to create real Razorpay Test Mode Payment Links (`plink_...`). Without credentials, it operates in an explicitly labeled `DEMO MODE (SIMULATED)`.*

**Q: Can the LLM override a policy decision or execute financial actions?**  
*A: No. The Policy Engine and ML models make all financial and retry decisions. The LLM functions strictly as a customer communication formatting layer.*

**Q: How does RecoverOS handle double webhook deliveries?**  
*A: `webhook_events.event_id` has a `UNIQUE` database constraint. If Razorpay sends duplicate webhooks, RecoverOS detects the existing record and returns `HTTP 200 {"status": "ignored"}` with zero duplicate payment link creations or double-counted revenue.*
