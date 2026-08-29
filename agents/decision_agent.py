"""
decision_agent.py
------------------
The AI Decision Agent. Given a failed transaction (with its computed
recovery_score/priority and, optionally, an ML-predicted recovery
probability), this module decides the single best recovery action and
produces a plain-language explanation for that decision.

This is intentionally a transparent RULE-BASED agent (not a black-box
model) so every recommendation can be justified in a demo/interview.
The ML model's probability is used as one input signal that nudges the
decision, not as an opaque final answer.

Possible actions:
    - "Retry Payment"
    - "Ask Customer to Update Payment Method"
    - "Send Payment Reminder"
    - "Send Personalized Recovery Message"
    - "Offer Customer Support"
    - "Do Not Retry Immediately"
"""

from __future__ import annotations

import pandas as pd

RETRY_FRIENDLY_REASONS = {"Network Failure", "Bank Server Issue"}
PAYMENT_METHOD_ISSUE_REASONS = {"Expired Card", "Card Declined"}
AUTH_REASONS = {"Authentication Failure"}
FUNDS_REASONS = {"Insufficient Funds"}


def decide_action(row: pd.Series, recovery_probability: float | None = None) -> tuple[str, str]:
    """
    Decide the best recovery action for a single failed transaction.

    Parameters
    ----------
    row : pd.Series
        A row from the analyzed dataframe. Expected to contain:
        failure_reason, priority, retry_count, amount, customer_segment,
        customer_history.
    recovery_probability : float | None
        The ML model's predicted probability (0-1) that this transaction
        would be recovered if retried/followed-up-on. Optional - if the
        model hasn't been trained yet, the agent still works using the
        rule-based priority alone.

    Returns
    -------
    (action, explanation) : tuple[str, str]
    """
    reason = row.get("failure_reason")
    priority = row.get("priority", "Medium Priority")
    retries = int(row.get("retry_count", 0))
    amount = row.get("amount", 0)

    prob_note = ""
    if recovery_probability is not None:
        prob_pct = round(recovery_probability * 100, 1)
        prob_note = f" The ML model estimates a {prob_pct}% chance of successful recovery."

    # Rule 1: too many retries already -> stop hammering the customer
    if retries >= 3:
        action = "Do Not Retry Immediately"
        explanation = (
            f"There have already been {retries} failed attempts, so retrying again risks "
            f"frustrating the customer with diminishing returns.{prob_note} "
            "A short cooling-off period followed by manual outreach is recommended instead."
        )
        return action, explanation

    # Rule 2: technical/infrastructure failures are usually fixed by a simple retry
    if reason in RETRY_FRIENDLY_REASONS and retries < 2:
        action = "Retry Payment"
        explanation = (
            f"'{reason}' is typically a temporary technical issue on the bank/network side, "
            f"not a customer-side problem, so a straightforward retry is likely to succeed.{prob_note}"
        )
        return action, explanation

    # Rule 3: payment instrument problems need the customer to act
    if reason in PAYMENT_METHOD_ISSUE_REASONS:
        action = "Ask Customer to Update Payment Method"
        explanation = (
            f"'{reason}' means the payment instrument itself is the problem, so simply retrying "
            f"the same method will fail again. The customer needs to add a new/valid payment method.{prob_note}"
        )
        return action, explanation

    # Rule 4: authentication/OTP issues usually just need a reminder to complete the step
    if reason in AUTH_REASONS:
        action = "Send Payment Reminder"
        explanation = (
            f"'{reason}' often means the customer didn't complete OTP/authentication in time. "
            f"A reminder nudging them to finish the payment step is usually enough.{prob_note}"
        )
        return action, explanation

    # Rule 5: insufficient funds + high value + good customer -> a warmer, personal touch
    if reason in FUNDS_REASONS:
        if priority == "High Priority":
            action = "Send Personalized Recovery Message"
            explanation = (
                f"'{reason}' on a high-value, high-priority transaction (₹{amount:,.0f}) benefits from a "
                f"personalized, empathetic message rather than a generic retry, since the customer likely "
                f"needs a bit more time or a flexible option.{prob_note}"
            )
        else:
            action = "Send Payment Reminder"
            explanation = (
                f"'{reason}' suggests the customer may simply need more time before funds are available; "
                f"a gentle reminder is a lower-friction first step than a personalized message.{prob_note}"
            )
        return action, explanation

    # Rule 6: high priority catch-all -> personalized outreach
    if priority == "High Priority":
        action = "Send Personalized Recovery Message"
        explanation = (
            f"This is a High Priority case (high value and/or a reliable customer), so a tailored, "
            f"personal message is worth the effort to recover the revenue.{prob_note}"
        )
        return action, explanation

    # Rule 7: medium priority, unclear reason -> customer support is safest
    if priority == "Medium Priority":
        action = "Offer Customer Support"
        explanation = (
            f"The failure reason ('{reason}') doesn't point to one obvious fix, so routing the customer "
            f"to support ensures the actual blocker gets diagnosed instead of guessing.{prob_note}"
        )
        return action, explanation

    # Rule 8: low priority fallback
    action = "Do Not Retry Immediately"
    explanation = (
        f"This is a Low Priority case (small amount and/or limited customer history), so it's more "
        f"efficient to deprioritize it rather than spend recovery effort here.{prob_note}"
    )
    return action, explanation


def decide_for_dataframe(df: pd.DataFrame, recovery_probabilities: "pd.Series | None" = None) -> pd.DataFrame:
    """
    Apply decide_action() to every FAILED row in df. Returns a copy of df
    with `recommended_action` and `action_explanation` columns added.
    """
    df = df.copy()
    actions, explanations = [], []

    for idx, row in df.iterrows():
        if row["payment_status"] == "Failed":
            prob = None
            if recovery_probabilities is not None and idx in recovery_probabilities.index:
                prob = recovery_probabilities.loc[idx]
            action, explanation = decide_action(row, prob)
        else:
            action, explanation = None, None

        actions.append(action)
        explanations.append(explanation)

    df["recommended_action"] = actions
    df["action_explanation"] = explanations
    return df
