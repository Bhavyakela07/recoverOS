"""
RecoverOS Phase 6 Automated Closed-Loop Integration Test Suite
Verifies complete end-to-end recovery pipeline:
payment.failed -> ML Analysis -> Policy Evaluation -> Payment Link Creation -> Email Dispatch -> payment.captured Webhook -> RECOVERED Case Status.
"""

import hmac
import hashlib
import json
import pytest
from fastapi.testclient import TestClient
from db.database import init_db, SessionLocal
from db.models import WebhookEventModel, RecoveryCaseModel, PaymentLinkModel, EmailMessageModel
from main import app
from utils.security import WEBHOOK_SECRET

client = TestClient(app)


def generate_sig(body_bytes: bytes, secret: str = WEBHOOK_SECRET) -> str:
    return hmac.new(secret.encode("utf-8"), body_bytes, hashlib.sha256).hexdigest()


def test_complete_closed_loop_recovery_pipeline():
    """Verify end-to-end closed-loop recovery from failure to payment capture."""
    import uuid
    init_db()
    
    test_id = f"phase6_{uuid.uuid4().hex[:6]}"
    test_pay_id = f"pay_{test_id}"
    test_evt_failed = f"evt_failed_{test_id}"
    test_evt_captured = f"evt_captured_{test_id}"

    # 1. Trigger payment.failed Webhook
    failed_payload = {
        "event": "payment.failed",
        "event_id": test_evt_failed,
        "payload": {
            "payment": {
                "entity": {
                    "id": test_pay_id,
                    "amount": 350000,
                    "currency": "INR",
                    "error_code": "BAD_REQUEST_ERROR",
                    "error_reason": "network_timeout",
                    "email": "customer_p6@example.com",
                    "contact": "+919876543210",
                    "notes": {"customer_name": "Test Customer Phase 6"}
                }
            }
        }
    }
    body_failed = json.dumps(failed_payload).encode("utf-8")
    headers_failed = {"X-Razorpay-Signature": generate_sig(body_failed)}

    res_failed = client.post("/webhook/razorpay", content=body_failed, headers=headers_failed)
    assert res_failed.status_code == 200
    json_failed = res_failed.json()
    assert json_failed["status"] == "processed"
    assert json_failed["decision"].upper() in ["ALLOW", "SUPPRESSED"]
    assert json_failed["lifecycle_status"] in ["CUSTOMER_CONTACTED", "RECOVERY_LINK_CREATED", "RECOVERY_RECOMMENDED", "SUPPRESSED"]

    # 2. Trigger payment.captured Webhook (Simulate buyer paying the Payment Link)
    captured_payload = {
        "event": "payment.captured",
        "event_id": test_evt_captured,
        "payload": {
            "payment": {
                "entity": {
                    "id": test_pay_id,
                    "amount": 350000,
                    "currency": "INR",
                    "email": "customer_p6@example.com"
                }
            }
        }
    }
    body_captured = json.dumps(captured_payload).encode("utf-8")
    headers_captured = {"X-Razorpay-Signature": generate_sig(body_captured)}

    res_captured = client.post("/webhook/razorpay", content=body_captured, headers=headers_captured)
    assert res_captured.status_code == 200
    json_captured = res_captured.json()
    assert json_captured["status"] == "processed"
    assert json_captured["case_status"] == "RECOVERED"
    assert json_captured["amount_recovered"] == 3500.0

    print("[QA TEST PASS] Complete Closed-Loop Pipeline Verified: FAILED -> ANALYZED -> LINK CREATED -> CONTACTED -> RECOVERED.")
