"""
generate_data.py
-----------------
Generates a realistic, SYNTHETIC dataset of Indian payment transactions
for the AI Revenue Recovery Agent project.

This dataset is explicitly labelled as SYNTHETIC for mechanism validation and demo purposes.
No real customer or payment data is used anywhere in this project.
"""

import os
import random
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

random.seed(42)
np.random.seed(42)

FIRST_NAMES = [
    "Rahul", "Priya", "Amit", "Sneha", "Vikram", "Ananya", "Rohan", "Kavya",
    "Arjun", "Divya", "Karthik", "Neha", "Siddharth", "Pooja", "Aditya",
    "Ishita", "Manish", "Riya", "Suresh", "Meera", "Varun", "Nisha",
    "Gaurav", "Shreya", "Rajesh", "Anjali", "Kunal", "Swati", "Deepak",
    "Tanvi", "Harsh", "Simran", "Nikhil", "Preeti", "Sanjay", "Kiran",
    "Abhishek", "Lakshmi", "Vivek", "Radhika",
]

LAST_NAMES = [
    "Sharma", "Verma", "Patel", "Reddy", "Nair", "Gupta", "Iyer", "Singh",
    "Menon", "Rao", "Kapoor", "Joshi", "Chowdhury", "Malhotra", "Pillai",
    "Agarwal", "Bose", "Desai", "Kulkarni", "Mehta",
]

PAYMENT_METHODS = ["UPI", "Credit Card", "Debit Card", "Netbanking", "Wallet"]
PAYMENT_METHOD_WEIGHTS = [0.42, 0.20, 0.20, 0.10, 0.08]

# Method-conditioned valid failure reasons
FAILURE_REASONS_BY_METHOD = {
    "Credit Card": [
        ("Card Declined", 0.35),
        ("Insufficient Funds", 0.25),
        ("Expired Card", 0.15),
        ("Network Failure", 0.15),
        ("Authentication Failure", 0.10),
    ],
    "Debit Card": [
        ("Card Declined", 0.30),
        ("Insufficient Funds", 0.35),
        ("Expired Card", 0.10),
        ("Network Failure", 0.15),
        ("Authentication Failure", 0.10),
    ],
    "UPI": [
        ("Insufficient Funds", 0.30),
        ("Network Failure", 0.30),
        ("Bank Server Issue", 0.25),
        ("Authentication Failure", 0.15),
    ],
    "Netbanking": [
        ("Bank Server Issue", 0.40),
        ("Network Failure", 0.30),
        ("Insufficient Funds", 0.20),
        ("Authentication Failure", 0.10),
    ],
    "Wallet": [
        ("Insufficient Funds", 0.50),
        ("Network Failure", 0.30),
        ("Authentication Failure", 0.20),
    ],
}

CUSTOMER_HISTORY_LEVELS = ["New Customer", "Occasional Buyer", "Regular Customer", "Loyal Customer"]
CUSTOMER_SEGMENTS = ["New", "Regular", "Premium"]

N_CUSTOMERS = 220
N_TRANSACTIONS = 650


def build_customers(n_customers: int):
    customers = []
    for i in range(1, n_customers + 1):
        segment = random.choices(CUSTOMER_SEGMENTS, weights=[0.35, 0.45, 0.20])[0]
        if segment == "Premium":
            history = random.choices(CUSTOMER_HISTORY_LEVELS, weights=[0.05, 0.15, 0.35, 0.45])[0]
        elif segment == "Regular":
            history = random.choices(CUSTOMER_HISTORY_LEVELS, weights=[0.10, 0.30, 0.40, 0.20])[0]
        else:
            history = random.choices(CUSTOMER_HISTORY_LEVELS, weights=[0.55, 0.30, 0.10, 0.05])[0]

        name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        customers.append({
            "customer_id": f"CUST{i:04d}",
            "customer_name": name,
            "customer_segment": segment,
            "customer_history": history,
        })
    return customers


def sample_amount(segment: str) -> float:
    if segment == "Premium":
        amount = np.random.lognormal(mean=8.6, sigma=0.5)
    elif segment == "Regular":
        amount = np.random.lognormal(mean=7.6, sigma=0.55)
    else:
        amount = np.random.lognormal(mean=6.8, sigma=0.6)

    return round(max(149.0, min(amount, 49999.0)), 2)


def sample_transaction_date() -> datetime:
    days_ago = random.randint(0, 89)
    seconds_offset = random.randint(0, 86399)
    return datetime.now() - timedelta(days=days_ago, seconds=-seconds_offset)


def build_transactions(customers):
    rows = []
    txn_counter = 1

    for _ in range(N_TRANSACTIONS):
        customer = random.choice(customers)
        segment = customer["customer_segment"]
        history = customer["customer_history"]

        amount = sample_amount(segment)
        payment_method = random.choices(PAYMENT_METHODS, weights=PAYMENT_METHOD_WEIGHTS)[0]
        txn_date = sample_transaction_date()

        base_fail_prob = 0.30
        if history == "Loyal Customer":
            base_fail_prob -= 0.12
        elif history == "New Customer":
            base_fail_prob += 0.10

        if segment == "Premium":
            base_fail_prob -= 0.04
        elif segment == "New":
            base_fail_prob += 0.05

        base_fail_prob = min(max(base_fail_prob, 0.05), 0.65)
        is_failed = random.random() < base_fail_prob

        if is_failed:
            payment_status = "Failed"
            # Method-conditioned failure reason selection
            reasons_spec = FAILURE_REASONS_BY_METHOD[payment_method]
            reasons, weights = zip(*reasons_spec)
            failure_reason = random.choices(reasons, weights=weights)[0]
            retry_count = random.choices([0, 1, 2, 3], weights=[0.35, 0.30, 0.22, 0.13])[0]

            recovery_base = {
                "Network Failure": 0.75,
                "Bank Server Issue": 0.68,
                "Authentication Failure": 0.55,
                "Card Declined": 0.45,
                "Insufficient Funds": 0.35,
                "Expired Card": 0.30,
                "Unknown Error": 0.25,
            }.get(failure_reason, 0.30)

            if history == "Loyal Customer":
                recovery_base += 0.12
            elif history == "New Customer":
                recovery_base -= 0.10

            if segment == "Premium":
                recovery_base += 0.08

            recovery_base -= 0.06 * retry_count
            recovery_prob = min(max(recovery_base, 0.03), 0.95)
            recovered_after_retry = int(random.random() < recovery_prob)
        else:
            payment_status = "Success"
            failure_reason = None
            retry_count = 0
            recovered_after_retry = None

        rows.append({
            "transaction_id": f"TXN{txn_counter:05d}",
            "customer_id": customer["customer_id"],
            "customer_name": customer["customer_name"],
            "amount": amount,
            "currency": "INR",
            "payment_method": payment_method,
            "transaction_date": txn_date.strftime("%Y-%m-%d %H:%M:%S"),
            "payment_status": payment_status,
            "failure_reason": failure_reason,
            "customer_history": history,
            "retry_count": retry_count,
            "customer_segment": segment,
            "recovered_after_retry": recovered_after_retry,
            "data_source": "SYNTHETIC_SIMULATION"
        })
        txn_counter += 1

    return rows


def main():
    customers = build_customers(N_CUSTOMERS)
    rows = build_transactions(customers)
    df = pd.DataFrame(rows)
    df = df.sort_values("transaction_date").reset_index(drop=True)

    output_path = "data/payments.csv"
    os.makedirs("data", exist_ok=True)
    df.to_csv(output_path, index=False)

    print(f"Generated {len(df)} synthetic transactions -> {output_path}")
    print(df["payment_status"].value_counts())


if __name__ == "__main__":
    main()
