"""
backend/domain/payment_failures.py
----------------------------------
Canonical Payment Failure Taxonomy and Central Deterministic Mapping Layer.
Prevents scatter string comparisons and enforces fail-closed handling for unknown/security errors.
"""

from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class PaymentMethod(str, Enum):
    CARD = "card"
    UPI = "upi"
    NETBANKING = "netbanking"
    WALLET = "wallet"
    UNKNOWN = "unknown"


class RecoveryClass(str, Enum):
    RETRY_FAST = "RETRY_FAST"
    RETRY_WHEN_BANK_UP = "RETRY_WHEN_BANK_UP"
    RETRY_AFTER_USER_ACTION = "RETRY_AFTER_USER_ACTION"
    NEVER_SAME_CREDENTIAL = "NEVER_SAME_CREDENTIAL"
    NEVER_FRAUD = "NEVER_FRAUD"
    NEVER_INSUFFICIENT_FUNDS = "NEVER_INSUFFICIENT_FUNDS"
    MERCHANT_BUG = "MERCHANT_BUG"
    UNKNOWN_HUMAN_REVIEW = "UNKNOWN_HUMAN_REVIEW"


class SafetyClassification(str, Enum):
    SAFE_TO_RETRY = "SAFE_TO_RETRY"
    REQUIRES_USER_ACTION = "REQUIRES_USER_ACTION"
    UNSAFE_STOP = "UNSAFE_STOP"
    HUMAN_REVIEW_REQUIRED = "HUMAN_REVIEW_REQUIRED"


class CanonicalPaymentFailure(BaseModel):
    payment_method: PaymentMethod = PaymentMethod.UNKNOWN
    error_code: str = "unknown"
    error_source: str = "unknown"
    error_step: str = "unknown"
    error_reason: str = "unknown"


class FailureMappingResult(BaseModel):
    recovery_class: RecoveryClass
    retry_recommendation: bool
    safety_classification: SafetyClassification
    explanation: str
    canonical_category: str


def classify_payment_failure(failure: CanonicalPaymentFailure) -> FailureMappingResult:
    """
    Central deterministic mapping layer.
    Normalizes raw failure payload and returns exact recovery class and safety classification.
    Fails closed to UNKNOWN_HUMAN_REVIEW if reason is unrecognized or security/risk related.
    """
    reason = (failure.error_reason or "").lower().strip()
    code = (failure.error_code or "").lower().strip()
    source = (failure.error_source or "").lower().strip()

    # 1. Fraud / Security / Risk failures -> NEVER_FRAUD (UNSAFE_STOP)
    fraud_keywords = ["fraud", "risk", "stolen", "block", "security", "blacklist", "suspicious"]
    if any(k in reason for k in fraud_keywords) or any(k in code for k in fraud_keywords) or source == "risk":
        return FailureMappingResult(
            recovery_class=RecoveryClass.NEVER_FRAUD,
            retry_recommendation=False,
            safety_classification=SafetyClassification.UNSAFE_STOP,
            explanation="Transaction flagged for security or fraud risk. Automatic retries strictly prohibited.",
            canonical_category="fraud_signal"
        )

    # 2. Expired / Invalid Credentials -> NEVER_SAME_CREDENTIAL (UNSAFE_STOP)
    if "expired" in reason or "expired" in code or "invalid_card" in reason or "invalid_card" in code:
        return FailureMappingResult(
            recovery_class=RecoveryClass.NEVER_SAME_CREDENTIAL,
            retry_recommendation=False,
            safety_classification=SafetyClassification.UNSAFE_STOP,
            explanation="Payment credential is invalid or expired. Retrying with same credential will fail.",
            canonical_category="expired_card"
        )

    # 3. Insufficient Funds -> NEVER_INSUFFICIENT_FUNDS (REQUIRES_USER_ACTION)
    if "insufficient" in reason or "funds" in reason or "insufficient" in code:
        return FailureMappingResult(
            recovery_class=RecoveryClass.NEVER_INSUFFICIENT_FUNDS,
            retry_recommendation=False,
            safety_classification=SafetyClassification.REQUIRES_USER_ACTION,
            explanation="Insufficient funds. Requires user account top-up or alternative payment method.",
            canonical_category="insufficient_funds"
        )

    # 4. Merchant Configuration / Bug -> MERCHANT_BUG (UNSAFE_STOP)
    if "merchant" in reason or "config" in reason or "key" in code:
        return FailureMappingResult(
            recovery_class=RecoveryClass.MERCHANT_BUG,
            retry_recommendation=False,
            safety_classification=SafetyClassification.UNSAFE_STOP,
            explanation="Merchant account configuration or API integration issue.",
            canonical_category="merchant_bug"
        )

    # 5. Network / Bank Server Timeout -> RETRY_FAST / RETRY_WHEN_BANK_UP (SAFE_TO_RETRY)
    network_keywords = ["network", "timeout", "gateway", "connection", "downtime"]
    if any(k in reason for k in network_keywords) or any(k in code for k in network_keywords):
        return FailureMappingResult(
            recovery_class=RecoveryClass.RETRY_FAST,
            retry_recommendation=True,
            safety_classification=SafetyClassification.SAFE_TO_RETRY,
            explanation="Transient network drop or gateway timeout. Safe for automated retry.",
            canonical_category="network_timeout"
        )

    # 6. Issuer / Bank Server Decline -> RETRY_WHEN_BANK_UP (SAFE_TO_RETRY)
    bank_keywords = ["bank", "issuer", "server_error", "decline", "unavailable"]
    if any(k in reason for k in bank_keywords) or any(k in code for k in bank_keywords):
        return FailureMappingResult(
            recovery_class=RecoveryClass.RETRY_WHEN_BANK_UP,
            retry_recommendation=True,
            safety_classification=SafetyClassification.SAFE_TO_RETRY,
            explanation="Issuer bank decline or server unavailability. Retry recommended after bank recovery window.",
            canonical_category="issuer_decline"
        )

    # 7. User Authentication / Dropped Flow -> RETRY_AFTER_USER_ACTION (REQUIRES_USER_ACTION)
    auth_keywords = ["auth", "otp", "2fa", "drop", "abandon", "user"]
    if any(k in reason for k in auth_keywords) or any(k in code for k in auth_keywords):
        return FailureMappingResult(
            recovery_class=RecoveryClass.RETRY_AFTER_USER_ACTION,
            retry_recommendation=False,
            safety_classification=SafetyClassification.REQUIRES_USER_ACTION,
            explanation="User dropped during authentication or 2FA step. Send reminder link for user-initiated retry.",
            canonical_category="authentication_failure"
        )

    # 8. DEFAULT FAIL-CLOSED -> UNKNOWN_HUMAN_REVIEW (HUMAN_REVIEW_REQUIRED)
    return FailureMappingResult(
        recovery_class=RecoveryClass.UNKNOWN_HUMAN_REVIEW,
        retry_recommendation=False,
        safety_classification=SafetyClassification.HUMAN_REVIEW_REQUIRED,
        explanation="Unrecognized or ambiguous failure reason. Routed to human review to prevent unsafe retries.",
        canonical_category="unknown"
    )
