"""
tests/smoke_test_scenarios.py
------------------------------
Final Submission Smoke Test Script.
Programmatically verifies the 4 judge scenarios against the FastAPI backend,
Canonical Failure Mapping Layer, Policy Engine, and Database.
"""

from fastapi.testclient import TestClient
from backend.main import app
from backend.domain.payment_failures import (
    CanonicalPaymentFailure,
    classify_payment_failure,
    PaymentMethod,
    RecoveryClass,
    SafetyClassification
)


def run_smoke_tests():
    print("🧪 Running Final Submission Smoke Test Suite...")

    # 1. SCENARIO 1 — SAFE RECOVERY (Network Failure)
    f1 = CanonicalPaymentFailure(
        payment_method=PaymentMethod.UPI,
        error_code="GATEWAY_TIMEOUT",
        error_source="gateway",
        error_step="payment_authorization",
        error_reason="network_timeout"
    )
    res1 = classify_payment_failure(f1)
    assert res1.recovery_class == RecoveryClass.RETRY_FAST
    assert res1.retry_recommendation is True
    assert res1.safety_classification == SafetyClassification.SAFE_TO_RETRY
    print("  ✅ SCENARIO 1 (Safe Network Failure): PASSED -> RETRY_FAST (SAFE_TO_RETRY)")

    # 2. SCENARIO 2 — SAFETY BLOCK (Fraud / Risk Failure)
    f2 = CanonicalPaymentFailure(
        payment_method=PaymentMethod.CARD,
        error_code="RISK_CHECK_FAILED",
        error_source="risk",
        error_step="payment_authorization",
        error_reason="payment_risk_check_failed"
    )
    res2 = classify_payment_failure(f2)
    assert res2.recovery_class == RecoveryClass.NEVER_FRAUD
    assert res2.retry_recommendation is False
    assert res2.safety_classification == SafetyClassification.UNSAFE_STOP
    print("  ✅ SCENARIO 2 (Fraud / Risk Failure): PASSED -> NEVER_FRAUD (UNSAFE_STOP - NO RETRY)")

    # 3. SCENARIO 3 — GUARDRAIL (Insufficient Funds)
    f3 = CanonicalPaymentFailure(
        payment_method=PaymentMethod.CARD,
        error_code="BAD_REQUEST",
        error_source="customer",
        error_step="payment_authorization",
        error_reason="insufficient_funds"
    )
    res3 = classify_payment_failure(f3)
    assert res3.recovery_class == RecoveryClass.NEVER_INSUFFICIENT_FUNDS
    assert res3.retry_recommendation is False
    assert res3.safety_classification == SafetyClassification.REQUIRES_USER_ACTION
    print("  ✅ SCENARIO 3 (Insufficient Funds Guardrail): PASSED -> NEVER_INSUFFICIENT_FUNDS (REQUIRES_USER_ACTION)")

    # 4. SCENARIO 4 — UNKNOWN ERROR (Unrecognized Reason Fail-Closed)
    f4 = CanonicalPaymentFailure(
        payment_method=PaymentMethod.UNKNOWN,
        error_code="CUSTOM_999_ERR",
        error_source="gateway",
        error_step="unknown",
        error_reason="unrecognized_custom_error_string"
    )
    res4 = classify_payment_failure(f4)
    assert res4.recovery_class == RecoveryClass.UNKNOWN_HUMAN_REVIEW
    assert res4.retry_recommendation is False
    assert res4.safety_classification == SafetyClassification.HUMAN_REVIEW_REQUIRED
    print("  ✅ SCENARIO 4 (Unknown Error Fail-Closed): PASSED -> UNKNOWN_HUMAN_REVIEW (HUMAN_REVIEW_REQUIRED)")

    # 5. Live FastAPI Endpoint Health Test (via TestClient)
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    print("  ✅ Live FastAPI Health Endpoint (/health): PASSED (200 OK)")

    print("🎉 ALL SMOKE TEST SCENARIOS PASSED WITH 100% SUCCESS!")

if __name__ == "__main__":
    run_smoke_tests()
