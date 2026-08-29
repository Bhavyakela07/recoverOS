"""
analyzer.py
-----------
Analyzes failed transactions and computes a Recovery Priority Score.

The score is a transparent, rule-based weighted formula (NOT a black box).
Every factor and weight used is documented here so it can be explained
during a demo/interview.

Recovery Priority Score (0-100) is a weighted combination of:
    1. Transaction amount        (40%) - bigger amounts are worth recovering
    2. Failure reason recoverability (25%) - some failures are easier to fix
    3. Customer segment          (15%) - Premium customers are prioritized
    4. Customer history          (10%) - loyal/reliable customers score higher
    5. Retry count               (10%) - too many retries lowers the score
                                          (customer fatigue / diminishing returns)
"""

from __future__ import annotations

import pandas as pd

# --------------------------------------------------------------------------
# Weight configuration - documented and easy to explain / tune
# --------------------------------------------------------------------------

SCORE_WEIGHTS = {
    "amount": 0.40,
    "failure_reason": 0.25,
    "segment": 0.15,
    "history": 0.10,
    "retry_count": 0.10,
}

# How recoverable each failure reason typically is (0 = hard to recover,
# 1 = easy to recover). These drive both the priority score and, later,
# the AI agent's recommended action.
FAILURE_REASON_RECOVERABILITY = {
    "Network Failure": 0.90,
    "Bank Server Issue": 0.80,
    "Authentication Failure": 0.65,
    "Card Declined": 0.55,
    "Insufficient Funds": 0.45,
    "Expired Card": 0.35,
    "Unknown Error": 0.25,
}

SEGMENT_WEIGHT = {
    "Premium": 1.00,
    "Regular": 0.65,
    "New": 0.35,
}

HISTORY_WEIGHT = {
    "Loyal Customer": 1.00,
    "Regular Customer": 0.75,
    "Occasional Buyer": 0.45,
    "New Customer": 0.20,
}


def _amount_factor(amount: float, max_amount: float) -> float:
    """Normalize amount to a 0-1 scale relative to the dataset's max amount."""
    if max_amount <= 0:
        return 0.0
    return min(amount / max_amount, 1.0)


def _retry_factor(retry_count: int) -> float:
    """
    0 retries  -> 1.0 (fresh failure, high chance retry will work)
    1 retry    -> 0.75
    2 retries  -> 0.45
    3+ retries -> 0.20 (customer fatigue, diminishing returns)
    """
    mapping = {0: 1.00, 1: 0.75, 2: 0.45}
    return mapping.get(int(retry_count), 0.20)


def calculate_recovery_score(row: pd.Series, max_amount: float) -> float:
    """Compute the 0-100 Recovery Priority Score for a single failed transaction."""
    amount_f = _amount_factor(row["amount"], max_amount)
    reason_f = FAILURE_REASON_RECOVERABILITY.get(row.get("failure_reason"), 0.30)
    segment_f = SEGMENT_WEIGHT.get(row.get("customer_segment"), 0.40)
    history_f = HISTORY_WEIGHT.get(row.get("customer_history"), 0.30)
    retry_f = _retry_factor(row.get("retry_count", 0))

    score = (
        amount_f * SCORE_WEIGHTS["amount"]
        + reason_f * SCORE_WEIGHTS["failure_reason"]
        + segment_f * SCORE_WEIGHTS["segment"]
        + history_f * SCORE_WEIGHTS["history"]
        + retry_f * SCORE_WEIGHTS["retry_count"]
    ) * 100

    return round(score, 1)


def classify_priority(score: float) -> str:
    """Bucket a numeric score into a High / Medium / Low priority label."""
    if score >= 65:
        return "High Priority"
    elif score >= 40:
        return "Medium Priority"
    else:
        return "Low Priority"


def explain_score(row: pd.Series, score: float, priority: str) -> str:
    """
    Produce a short, human-readable explanation of why a transaction
    received its priority. Used throughout the UI so decisions are never
    an unexplained black box.
    """
    reasons = []

    if row["amount"] >= 5000:
        reasons.append("the transaction value is high")
    elif row["amount"] >= 1500:
        reasons.append("the transaction value is moderate")
    else:
        reasons.append("the transaction value is relatively small")

    reason_f = FAILURE_REASON_RECOVERABILITY.get(row.get("failure_reason"), 0.30)
    if reason_f >= 0.65:
        reasons.append(f"the failure reason ('{row['failure_reason']}') is usually easy to recover from")
    elif reason_f >= 0.40:
        reasons.append(f"the failure reason ('{row['failure_reason']}') is moderately recoverable")
    else:
        reasons.append(f"the failure reason ('{row['failure_reason']}') is historically harder to recover")

    segment = row.get("customer_segment")
    if segment == "Premium":
        reasons.append("the customer belongs to the Premium segment")
    elif segment == "New":
        reasons.append("the customer is new, with limited payment history")

    history = row.get("customer_history")
    if history in ("Loyal Customer", "Regular Customer"):
        reasons.append(f"the customer has a reliable history ({history})")
    elif history == "New Customer":
        reasons.append("the customer has no established payment history yet")

    retries = int(row.get("retry_count", 0))
    if retries == 0:
        reasons.append("no retries have been attempted yet")
    elif retries >= 3:
        reasons.append(f"the customer has already had {retries} failed retries, reducing urgency")
    else:
        reasons.append(f"{retries} retry attempt(s) have already been made")

    explanation = (
        f"{priority} (score {score}/100) because " + ", ".join(reasons[:-1])
        + f", and {reasons[-1]}."
    )
    return explanation


def analyze_failed_transactions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Given the full payments dataframe, compute recovery_score, priority,
    and an explanation for every FAILED transaction. Returns a copy of df
    with these new columns added (successful transactions get NaN/blank).
    """
    df = df.copy()
    max_amount = df["amount"].max()

    scores, priorities, explanations = [], [], []

    for _, row in df.iterrows():
        if row["payment_status"] == "Failed":
            score = calculate_recovery_score(row, max_amount)
            priority = classify_priority(score)
            explanation = explain_score(row, score, priority)
        else:
            score, priority, explanation = None, None, None

        scores.append(score)
        priorities.append(priority)
        explanations.append(explanation)

    df["recovery_score"] = scores
    df["priority"] = priorities
    df["priority_explanation"] = explanations
    return df
