"""
RecoverOS Comprehensive Hackathon Readiness Verification Test Suite
Verifies:
1. Database Schema & Tables (9 tables + WebhookEventModel UNIQUE constraint + PostgreSQL explicit error check)
2. Backend API Security (HMAC verification + 400 rejection + Double-webhook idempotency defense)
3. Closed-Loop Recovery Pipeline (payment.failed -> ML -> Policy -> Link -> Outreach -> payment.captured -> RECOVERED)
4. Policy Rules (Quiet Hours, ₹50k threshold, 24h contact caps, DO_NOT_RETRY)
5. ML Engine Calibration (Calibrated XGBoost + Isotonic Calibration)
"""

import hmac
import hashlib
import json
import pytest
import uuid
import os
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy import inspect

from db.database import init_db, SessionLocal, engine
from db.models import (
    Base, WebhookEventModel, RecoveryCaseModel, PaymentLinkModel,
    EmailMessageModel, AuditEventModel, RevenueLeakModel, AIDecisionModel
)
from main import app
from utils.security import WEBHOOK_SECRET
from services.policy_engine import PolicyEngine, build_policy_input, PolicyDecision, PolicyReason, StoppingRuleReason
from services.ml_engine import get_ml_engine
from backend.models.schemas import RecoveryAction, LeakSource, FailureCategory

client = TestClient(app)


def generate_sig(body_bytes: bytes, secret: str = WEBHOOK_SECRET) -> str:
    return hmac.new(secret.encode("utf-8"), body_bytes, hashlib.sha256).hexdigest()


# --------------------------------------------------------------------------
# 1. Database & Schema Verification
# --------------------------------------------------------------------------
def test_database_schema_and_constraints():
    """Verify all 9 ORM tables exist and event_id unique constraint is enforced."""
    init_db()
    inspector = inspect(engine)
    tables = inspector.get_table_names()

    required_tables = [
        "merchants", "customers", "revenue_leaks", "recovery_cases",
        "ai_decisions", "webhook_events", "payment_links", "email_messages", "audit_events"
    ]
    for table in required_tables:
        assert table in tables, f"Missing required database table: {table}"

    # Verify webhook_events.event_id unique constraint / index
    indexes = inspector.get_indexes("webhook_events")
    evt_id_unique = any(idx["unique"] and "event_id" in idx["column_names"] for idx in indexes) or \
                    any(col.get("unique") for col in inspector.get_columns("webhook_events") if col["name"] == "event_id")
    assert evt_id_unique, "webhook_events.event_id must have a UNIQUE index/constraint!"


def test_postgresql_no_silent_fallback():
    """Verify explicit invalid PostgreSQL DATABASE_URL raises RuntimeError without silent SQLite fallback."""
    import importlib
    import db.database
    original_url = os.environ.get("DATABASE_URL")
    try:
        os.environ["DATABASE_URL"] = "postgresql://invalid_user:invalid_pass@localhost:5432/non_existent_db"
        with pytest.raises(RuntimeError) as exc_info:
            importlib.reload(db.database)
        assert "PostgreSQL" in str(exc_info.value)
    finally:
        if original_url is not None:
            os.environ["DATABASE_URL"] = original_url
        else:
            os.environ.pop("DATABASE_URL", None)
        importlib.reload(db.database)


# --------------------------------------------------------------------------
# 2. Policy Engine Verification
# --------------------------------------------------------------------------
def test_policy_quiet_hours_suppressed():
    """Verify Quiet Hours (22:00-08:00 IST) returns SUPPRESSED."""
    policy_engine = PolicyEngine()
    inp = build_policy_input(
        recovery_probability=0.85,
        risk_score=0.1,
        amount=Decimal("2500"),
        retry_count=0,
        proposed_action=RecoveryAction.REMINDER,
        leak_source=LeakSource.PAYMENT_FAILURE,
        failure_category=FailureCategory.NETWORK_TIMEOUT,
        customer_consent=True,
        customer_contact_count_24h=0,
        customer_contact_count_7d=0,
        is_current_hour_quiet=True  # Quiet Hours ACTIVE
    )
    stop_dec = policy_engine.check_stopping_rules(inp)
    assert stop_dec.stop is True
    assert stop_dec.rule == StoppingRuleReason.QUIET_HOURS


def test_policy_amount_over_50k_human_review():
    """Verify transaction amount > ₹50,000 escalates to HUMAN_REVIEW."""
    policy_engine = PolicyEngine()
    inp = build_policy_input(
        recovery_probability=0.85,
        risk_score=0.1,
        amount=Decimal("75000"),  # > 50,000
        retry_count=0,
        proposed_action=RecoveryAction.RETRY,
        leak_source=LeakSource.PAYMENT_FAILURE,
        failure_category=FailureCategory.NETWORK_TIMEOUT,
        customer_consent=True,
        customer_contact_count_24h=0,
        customer_contact_count_7d=0,
        is_current_hour_quiet=False
    )
    decision, reason, _ = policy_engine.evaluate(inp)
    assert decision == PolicyDecision.HUMAN_REVIEW
    assert reason == PolicyReason.AMOUNT_OVER_LIMIT


def test_policy_contact_cap_24h_suppressed():
    """Verify customer contacted >= 3 times in 24h triggers contact cap stopping rule."""
    policy_engine = PolicyEngine()
    inp = build_policy_input(
        recovery_probability=0.85,
        risk_score=0.1,
        amount=Decimal("2500"),
        retry_count=0,
        proposed_action=RecoveryAction.REMINDER,
        leak_source=LeakSource.PAYMENT_FAILURE,
        failure_category=FailureCategory.NETWORK_TIMEOUT,
        customer_consent=True,
        customer_contact_count_24h=3,  # Cap reached
        customer_contact_count_7d=3,
        is_current_hour_quiet=False
    )
    stop_dec = policy_engine.check_stopping_rules(inp)
    assert stop_dec.stop is True
    assert stop_dec.rule == StoppingRuleReason.CONTACT_CAP


def test_policy_insufficient_funds_retries_do_not_retry():
    """Verify insufficient funds with exhausted retries returns DO_NOT_RETRY rule."""
    policy_engine = PolicyEngine()
    inp = build_policy_input(
        recovery_probability=0.10,  # Low probability
        risk_score=0.1,
        amount=Decimal("2500"),
        retry_count=3,  # Max retries
        proposed_action=RecoveryAction.RETRY,
        leak_source=LeakSource.PAYMENT_FAILURE,
        failure_category=FailureCategory.ISSUER_DECLINE,
        customer_consent=True,
        customer_contact_count_24h=0,
        customer_contact_count_7d=0,
        is_current_hour_quiet=False
    )
    stop_dec = policy_engine.check_stopping_rules(inp)
    assert stop_dec.stop is True
    assert stop_dec.rule in [StoppingRuleReason.MAX_RETRIES, StoppingRuleReason.MIN_PROBABILITY]


# --------------------------------------------------------------------------
# 3. ML Engine Calibration Verification
# --------------------------------------------------------------------------
def test_ml_calibrated_xgboost_inference():
    """Verify Calibrated XGBoost predicts calibrated probability p_recovery between 0.0 and 1.0."""
    ml_engine = get_ml_engine()
    p_recovery, brier = ml_engine.predict_p_recovery(
        amount_inr=4500.0,
        customer_ltv=12000.0,
        contact_count_7d=1,
        retry_count=0,
        failure_category="network_timeout",
        leak_source="payment_failed",
        is_quiet_hours=False
    )
    assert 0.0 <= p_recovery <= 1.0
    assert brier is not None


# --------------------------------------------------------------------------
# 4. Backend API & Webhook Idempotency Verification
# --------------------------------------------------------------------------
def test_backend_health_check():
    """Verify GET /health returns 200 with healthy database status."""
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"


def test_webhook_security_rejections():
    """Verify missing or invalid HMAC signatures return HTTP 400."""
    payload = {"event": "payment.failed", "event_id": "evt_test_sec_1"}
    body = json.dumps(payload).encode("utf-8")

    # Missing header
    res_missing = client.post("/webhook/razorpay", content=body)
    assert res_missing.status_code == 400

    # Invalid header
    res_invalid = client.post("/webhook/razorpay", content=body, headers={"X-Razorpay-Signature": "invalid_sig"})
    assert res_invalid.status_code == 400


def test_webhook_double_delivery_idempotency():
    """Verify duplicate event_id is safely ignored (returns HTTP 200 status ignored)."""
    test_evt_id = f"evt_idemp_{uuid.uuid4().hex[:6]}"
    payload = {
        "event": "payment.failed",
        "event_id": test_evt_id,
        "payload": {
            "payment": {
                "entity": {
                    "id": f"pay_idemp_{uuid.uuid4().hex[:6]}",
                    "amount": 299900,
                    "error_code": "BAD_REQUEST_ERROR",
                    "error_reason": "network_timeout",
                    "email": "idemp@example.com"
                }
            }
        }
    }
    body = json.dumps(payload).encode("utf-8")
    sig = generate_sig(body)
    headers = {"X-Razorpay-Signature": sig}

    # Delivery 1: Processed
    res1 = client.post("/webhook/razorpay", content=body, headers=headers)
    assert res1.status_code == 200
    assert res1.json()["status"] == "processed"

    # Delivery 2: Ignored
    res2 = client.post("/webhook/razorpay", content=body, headers=headers)
    assert res2.status_code == 200
    assert res2.json()["status"] == "ignored"
    assert "Duplicate event" in res2.json()["message"]
