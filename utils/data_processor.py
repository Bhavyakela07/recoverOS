"""
data_processor.py
------------------
Shared helpers for loading the payments dataset, computing revenue /
recovery metrics, and applying dashboard filters. Kept separate from
app.py so the logic is testable and reusable.
"""

from __future__ import annotations

import pandas as pd


def load_data(path: str) -> pd.DataFrame:
    """Load payments.csv and parse the transaction_date column."""
    df = pd.read_csv(path)
    df["transaction_date"] = pd.to_datetime(df["transaction_date"])
    return df


def compute_summary_metrics(df: pd.DataFrame) -> dict:
    """
    Compute the headline metrics shown on the Dashboard page.

    Definitions:
        total_transactions          - count of all transactions
        successful_transactions     - count of Success rows
        failed_transactions         - count of Failed rows
        total_value                 - sum of amount across ALL transactions
        successful_revenue          - sum of amount where status == Success
        failed_revenue              - sum of amount where status == Failed
        potential_recoverable_revenue - failed_revenue weighted by each
                                         transaction's recovery_score (if
                                         present) - i.e. not 100% of failed
                                         revenue is assumed recoverable
        high_priority_recoverable_revenue - failed_revenue for rows
                                             specifically flagged High Priority
        recovery_rate                - potential_recoverable_revenue as a
                                        % of failed_revenue
    """
    total_transactions = len(df)
    successful_transactions = int((df["payment_status"] == "Success").sum())
    failed_transactions = int((df["payment_status"] == "Failed").sum())

    total_value = float(df["amount"].sum())
    successful_revenue = float(df.loc[df["payment_status"] == "Success", "amount"].sum())
    failed_revenue = float(df.loc[df["payment_status"] == "Failed", "amount"].sum())

    failed_df = df[df["payment_status"] == "Failed"]

    if "recovery_score" in df.columns and failed_df["recovery_score"].notna().any():
        # Weight each failed transaction's amount by its recovery score (0-100 -> 0-1)
        weighted = (failed_df["amount"] * (failed_df["recovery_score"] / 100)).sum()
        potential_recoverable_revenue = float(weighted)
    else:
        # Fallback assumption if scoring hasn't been run yet
        potential_recoverable_revenue = failed_revenue * 0.5

    if "priority" in df.columns:
        high_priority_recoverable_revenue = float(
            failed_df.loc[failed_df["priority"] == "High Priority", "amount"].sum()
        )
    else:
        high_priority_recoverable_revenue = 0.0

    recovery_rate = (
        (potential_recoverable_revenue / failed_revenue * 100) if failed_revenue > 0 else 0.0
    )

    return {
        "total_transactions": total_transactions,
        "successful_transactions": successful_transactions,
        "failed_transactions": failed_transactions,
        "total_value": total_value,
        "successful_revenue": successful_revenue,
        "failed_revenue": failed_revenue,
        "potential_recoverable_revenue": potential_recoverable_revenue,
        "high_priority_recoverable_revenue": high_priority_recoverable_revenue,
        "recovery_rate": round(recovery_rate, 1),
    }


def apply_filters(
    df: pd.DataFrame,
    date_range=None,
    payment_status=None,
    payment_method=None,
    failure_reason=None,
    priority=None,
    customer_segment=None,
) -> pd.DataFrame:
    """Apply the sidebar filter selections to the dataframe."""
    filtered = df.copy()

    if date_range and len(date_range) == 2:
        start, end = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1]) + pd.Timedelta(days=1)
        filtered = filtered[(filtered["transaction_date"] >= start) & (filtered["transaction_date"] < end)]

    if payment_status and "All" not in payment_status:
        filtered = filtered[filtered["payment_status"].isin(payment_status)]

    if payment_method and "All" not in payment_method:
        filtered = filtered[filtered["payment_method"].isin(payment_method)]

    if failure_reason and "All" not in failure_reason:
        filtered = filtered[filtered["failure_reason"].isin(failure_reason)]

    if priority and "All" not in priority:
        filtered = filtered[filtered["priority"].isin(priority) | filtered["payment_status"].eq("Success")]

    if customer_segment and "All" not in customer_segment:
        filtered = filtered[filtered["customer_segment"].isin(customer_segment)]

    return filtered
