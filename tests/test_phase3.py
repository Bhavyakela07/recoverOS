"""
RecoverOS Phase 3 Automated QA Test Suite
Verifies Webhook HMAC Signature Verification, Double-Webhook Idempotency Defense, and Checkout Abandonment Sweep.
"""

import pytest
import hmac
import hashlib
import json
import os
import sys
from datetime import datetime, timedelta

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from fastapi.testclient import TestClient
from main import app
from services.sweep_detector import get_sweep_detector

client = TestClient(app)
WEBHOOK_SECRET = "test_webhook_secret"


def generate_webhook_signature(payload_bytes: bytes, secret: str = WEBHOOK_SECRET) -> str:
    """Helper to compute valid HMAC-SHA256 signature for Razorpay webhook tests."""
    return hmac.new(
        secret.encode("utf-8"),
        payload_bytes,
        hashlib.sha256
    ).hexdigest()


def test_webhook_signature_security():
    """Verify invalid or missing webhook signatures are rejected with HTTP 400."""
    payload = {"event": "payment.failed", "event_id": "evt_invalid_sig_test"}
    body_bytes = json.dumps(payload).encode("utf-8")

    # Test 1: Missing signature header
    res_missing = client.post("/webhook/razorpay", content=body_bytes)
    assert res_missing.status_code == 400
    assert "Invalid webhook signature" in res_missing.json()["detail"]

    # Test 2: Invalid signature header
    res_invalid = client.post(
        "/webhook/razorpay",
        content=body_bytes,
        headers={"X-Razorpay-Signature": "invalid_signature_hash_123"}
    )
    assert res_invalid.status_code == 400
    print("[QA TEST PASS] Webhook Security rejects invalid or missing HMAC signatures.")


def test_double_webhook_idempotency():
    """Verify duplicate webhook delivery is safely ignored (Idempotency Defense)."""
    payload = {
        "event": "payment.failed",
        "event_id": "evt_idempotency_test_999",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_test_999",
                    "amount": 149900,
                    "currency": "INR",
                    "error_code": "BAD_REQUEST_ERROR",
                    "error_reason": "network_timeout",
                    "email": "aarav@razorpay.com",
                    "contact": "+919876543210"
                }
            }
        }
    }
    body_bytes = json.dumps(payload).encode("utf-8")
    valid_signature = generate_webhook_signature(body_bytes)

    headers = {"X-Razorpay-Signature": valid_signature}

    # First Delivery: Should process
    res_1 = client.post("/webhook/razorpay", content=body_bytes, headers=headers)
    assert res_1.status_code == 200
    assert res_1.json()["status"] == "processed"
    assert res_1.json()["event_id"] == "evt_idempotency_test_999"

    # Second Delivery (Duplicate): Should be IGNORED by Idempotency Manager
    res_2 = client.post("/webhook/razorpay", content=body_bytes, headers=headers)
    assert res_2.status_code == 200
    assert res_2.json()["status"] == "ignored"
    assert "Duplicate event" in res_2.json()["message"]
    print("[QA TEST PASS] Double-webhook idempotency defense prevents duplicate execution.")


def test_checkout_abandonment_sweep_detector():
    """Verify Checkout Abandonment Sweep flags sessions > 30 minutes old."""
    sweep_detector = get_sweep_detector()

    now = datetime.utcnow()
    mock_checkouts = [
        {
            "order_id": "order_abnd_101",
            "amount_inr": 2999.0,
            "customer_name": "Rohan",
            "created_at": (now - timedelta(minutes=45)).isoformat() + "Z", # Abandoned (>30m)
            "is_paid": False
        },
        {
            "order_id": "order_recent_102",
            "amount_inr": 1200.0,
            "customer_name": "Priya",
            "created_at": (now - timedelta(minutes=10)).isoformat() + "Z", # Active (<30m)
            "is_paid": False
        }
    ]

    abandoned_cases = sweep_detector.run_sweep(mock_checkouts)

    assert len(abandoned_cases) == 1
    assert abandoned_cases[0]["order_id"] == "order_abnd_101"
    assert abandoned_cases[0]["decision"] in ["allow", "human_review", "deny", "suppress", "ALLOW", "HUMAN_REVIEW", "DENY", "SUPPRESSED"]
    assert abandoned_cases[0]["ai_diagnosis"] is not None
    print("[QA TEST PASS] Checkout Abandonment Sweep successfully identified abandoned cart.")


if __name__ == "__main__":
    pytest.main(["-v", __file__])
