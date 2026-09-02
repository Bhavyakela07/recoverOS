"""
tests/test_domain_payment_failures.py
--------------------------------------
Tests canonical payment failure taxonomy, deterministic mapping layer,
and fail-closed handling for unknown/security/fraud error categories.
"""

import pytest
from backend.domain.payment_failures import (
    CanonicalPaymentFailure,
    classify_payment_failure,
    PaymentMethod,
    RecoveryClass,
    SafetyClassification
)


def test_network_failure_classification():
    failure = CanonicalPaymentFailure(
        payment_method=PaymentMethod.UPI,
        error_code="GATEWAY_TIMEOUT",
        error_source="gateway",
        error_step="payment_authorization",
        error_reason="network_timeout"
    )
    res = classify_payment_failure(failure)
    assert res.recovery_class == RecoveryClass.RETRY_FAST
    assert res.retry_recommendation is True
    assert res.safety_classification == SafetyClassification.SAFE_TO_RETRY


def test_issuer_decline_classification():
    failure = CanonicalPaymentFailure(
        payment_method=PaymentMethod.CARD,
        error_code="BAD_REQUEST",
        error_source="bank",
        error_step="payment_authorization",
        error_reason="issuer_decline"
    )
    res = classify_payment_failure(failure)
    assert res.recovery_class == RecoveryClass.RETRY_WHEN_BANK_UP
    assert res.retry_recommendation is True
    assert res.safety_classification == SafetyClassification.SAFE_TO_RETRY


def test_expired_card_classification():
    failure = CanonicalPaymentFailure(
        payment_method=PaymentMethod.CARD,
        error_code="EXPIRED_CARD",
        error_source="customer",
        error_step="payment_authentication",
        error_reason="card_expired"
    )
    res = classify_payment_failure(failure)
    assert res.recovery_class == RecoveryClass.NEVER_SAME_CREDENTIAL
    assert res.retry_recommendation is False
    assert res.safety_classification == SafetyClassification.UNSAFE_STOP


def test_fraud_risk_classification_fail_closed():
    failure = CanonicalPaymentFailure(
        payment_method=PaymentMethod.CARD,
        error_code="RISK_CHECK_FAILED",
        error_source="risk",
        error_step="payment_authorization",
        error_reason="payment_risk_check_failed"
    )
    res = classify_payment_failure(failure)
    assert res.recovery_class == RecoveryClass.NEVER_FRAUD
    assert res.retry_recommendation is False
    assert res.safety_classification == SafetyClassification.UNSAFE_STOP


def test_unknown_error_fail_closed_to_human_review():
    failure = CanonicalPaymentFailure(
        payment_method=PaymentMethod.UNKNOWN,
        error_code="CUSTOM_999_ERR",
        error_source="gateway",
        error_step="unknown",
        error_reason="some_ambiguous_unrecognized_reason"
    )
    res = classify_payment_failure(failure)
    assert res.recovery_class == RecoveryClass.UNKNOWN_HUMAN_REVIEW
    assert res.retry_recommendation is False
    assert res.safety_classification == SafetyClassification.HUMAN_REVIEW_REQUIRED
