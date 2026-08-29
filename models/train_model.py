"""
train_model.py
---------------
Trains the RecoveryModel on data/payments.csv and saves it to
models/recovery_model.pkl.

Run:
    python models/train_model.py

This must be run once before the Streamlit app can show ML-based
recovery probabilities. If the model file is missing, app.py will
detect this and prompt the user to run this script (the app will
still work using the rule-based score alone in the meantime).
"""

import os
import sys

import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.recovery_model import RecoveryModel  # noqa: E402

DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "payments.csv")


def main():
    if not os.path.exists(DATA_PATH):
        print(f"Dataset not found at {DATA_PATH}.")
        print("Run 'python data/generate_data.py' first.")
        return

    df = pd.read_csv(DATA_PATH)

    print("Training Recovery Likelihood model...")
    print(f"Total rows: {len(df)} | Failed rows: {(df['payment_status'] == 'Failed').sum()}")

    model = RecoveryModel()
    metrics = model.train(df)

    print("\nEvaluation metrics (on held-out test split):")
    for key, value in metrics.items():
        print(f"  {key}: {value}")

    print("\nTop feature importances:")
    print(model.feature_importances().head(8).round(3))

    model.save()
    print(f"\nModel saved -> {model.__class__.__module__}")
    print("Saved to models/recovery_model.pkl")


if __name__ == "__main__":
    main()
