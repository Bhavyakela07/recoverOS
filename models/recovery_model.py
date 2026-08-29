"""
recovery_model.py
------------------
A small, explainable Scikit-learn model that predicts the probability
that a FAILED transaction will be successfully recovered if retried /
followed up on.

Why this model exists (and why it's not "ML for ML's sake"):
    The rule-based recovery_score in agents/analyzer.py tells us WHICH
    transactions matter most (priority). This model complements it by
    estimating HOW LIKELY a retry actually is to succeed, learned from
    historical outcomes (the `recovered_after_retry` column that was
    simulated for past failed transactions in data/generate_data.py).
    The AI Decision Agent (agents/decision_agent.py) combines both
    signals to pick an action.

Model: RandomForestClassifier
    - Chosen because it's easy to explain (feature importances), handles
      a mix of categorical/numeric features well after encoding, and
      does not require feature scaling.

Features used:
    - amount                (numeric)
    - retry_count            (numeric)
    - payment_method         (one-hot encoded)
    - failure_reason         (one-hot encoded)
    - customer_segment       (one-hot encoded)
    - customer_history       (one-hot encoded)

Target:
    - recovered_after_retry (1 = eventually recovered, 0 = not recovered)
      Only failed transactions with a known outcome are used for training,
      to avoid leaking information from transactions that never failed.
"""

from __future__ import annotations

import os

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split

CATEGORICAL_FEATURES = ["payment_method", "failure_reason", "customer_segment", "customer_history"]
NUMERIC_FEATURES = ["amount", "retry_count"]
TARGET = "recovered_after_retry"

DEFAULT_MODEL_PATH = os.path.join(os.path.dirname(__file__), "recovery_model.pkl")


class RecoveryModel:
    """Wraps feature engineering + a RandomForestClassifier for reuse."""

    def __init__(self):
        self.model = RandomForestClassifier(
            n_estimators=200,
            max_depth=6,
            min_samples_leaf=5,
            random_state=42,
            class_weight="balanced",
        )
        self.feature_columns_: list[str] | None = None

    # ------------------------------------------------------------------
    # Feature engineering
    # ------------------------------------------------------------------
    def build_features(self, df: pd.DataFrame, fit_columns: bool = False) -> pd.DataFrame:
        """
        One-hot encode categorical columns and combine with numeric columns.
        If fit_columns=True, remembers the resulting column set (training time).
        Otherwise, aligns incoming data to the columns seen during training
        (inference time) so the model never sees a mismatched feature set.
        """
        working = df[NUMERIC_FEATURES + CATEGORICAL_FEATURES].copy()
        encoded = pd.get_dummies(working, columns=CATEGORICAL_FEATURES)

        if fit_columns:
            self.feature_columns_ = list(encoded.columns)
            return encoded

        if self.feature_columns_ is None:
            raise RuntimeError("Model has not been trained/loaded yet - feature columns unknown.")

        # Add any missing columns (categories not present in this batch) as 0,
        # and drop/reorder to exactly match the training-time columns.
        for col in self.feature_columns_:
            if col not in encoded.columns:
                encoded[col] = 0
        encoded = encoded[self.feature_columns_]
        return encoded

    # ------------------------------------------------------------------
    # Training
    # ------------------------------------------------------------------
    def train(self, df: pd.DataFrame) -> dict:
        """
        Train on historical FAILED transactions that have a known
        recovery outcome. Returns a dict of evaluation metrics.
        """
        labeled = df[df["payment_status"] == "Failed"].dropna(subset=[TARGET]).copy()
        if len(labeled) < 20:
            raise ValueError("Not enough labeled failed transactions to train a reliable model.")

        X = self.build_features(labeled, fit_columns=True)
        y = labeled[TARGET].astype(int)

        # Stratified train/test split so both classes are represented in
        # both sets - avoids an unrealistically easy or skewed evaluation.
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.25, random_state=42, stratify=y
        )

        self.model.fit(X_train, y_train)

        y_pred = self.model.predict(X_test)
        y_proba = self.model.predict_proba(X_test)[:, 1]

        metrics = {
            "accuracy": round(accuracy_score(y_test, y_pred), 3),
            "precision": round(precision_score(y_test, y_pred, zero_division=0), 3),
            "recall": round(recall_score(y_test, y_pred, zero_division=0), 3),
            "f1_score": round(f1_score(y_test, y_pred, zero_division=0), 3),
            "roc_auc": round(roc_auc_score(y_test, y_proba), 3) if len(set(y_test)) > 1 else None,
            "train_size": len(X_train),
            "test_size": len(X_test),
        }
        return metrics

    # ------------------------------------------------------------------
    # Inference
    # ------------------------------------------------------------------
    def predict_proba(self, df: pd.DataFrame) -> np.ndarray:
        """Return the probability of successful recovery for each row in df."""
        X = self.build_features(df, fit_columns=False)
        return self.model.predict_proba(X)[:, 1]

    def feature_importances(self) -> pd.Series:
        """Return feature importances sorted descending - useful for explainability."""
        if self.feature_columns_ is None:
            raise RuntimeError("Model has not been trained/loaded yet.")
        importances = pd.Series(self.model.feature_importances_, index=self.feature_columns_)
        return importances.sort_values(ascending=False)

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------
    def save(self, path: str = DEFAULT_MODEL_PATH) -> None:
        joblib.dump({"model": self.model, "feature_columns": self.feature_columns_}, path)

    @classmethod
    def load(cls, path: str = DEFAULT_MODEL_PATH) -> "RecoveryModel":
        payload = joblib.load(path)
        instance = cls()
        instance.model = payload["model"]
        instance.feature_columns_ = payload["feature_columns"]
        return instance

    @staticmethod
    def model_exists(path: str = DEFAULT_MODEL_PATH) -> bool:
        return os.path.exists(path)
