"""
Service interfaces for RecoverOS - all external dependencies behind one seam.
Each interface has a fake implementation for testing/demos.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
import asyncio
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
import random
import json

try:
    from backend.models.schemas import (
        RevenueLeak, CustomerProfile, PredictionResult,
        AIRecommendation, StrategyOption, PolicyResult, StopDecision,
        LeakSource, FailureCategory, RecoveryAction, PolicyDecision,
        PolicyReason, StoppingRuleReason, ReasonCode, RecoveryActionResult
    )
except ImportError:
    from models.schemas import (
        RevenueLeak, CustomerProfile, PredictionResult,
        AIRecommendation, StrategyOption, PolicyResult, StopDecision,
        LeakSource, FailureCategory, RecoveryAction, PolicyDecision,
        PolicyReason, StoppingRuleReason, ReasonCode, RecoveryActionResult
    )


# =============================================================================
# LEAK DETECTOR INTERFACE
# =============================================================================

class LeakDetector(ABC):
    """Detector interface - normalizes everything into ONE entity: RevenueLeak."""

    @abstractmethod
    async def detect(self) -> List[RevenueLeak]:
        pass


class FakeDetector(LeakDetector):
    """Fake detector for walking skeleton."""

    def __init__(self, seed: int = 42, count: int = 10):
        self.rng = random.Random(seed)
        self.count = count

    async def detect(self) -> List[RevenueLeak]:
        """Generate deterministic fake revenue leaks."""
        leaks = []
        for i in range(self.count):
            leak = RevenueLeak(
                id=f"leak_{uuid.uuid4().hex[:12]}",
                leak_source=self.rng.choice(list(LeakSource)),
                customer_id=f"cust_{self.rng.randint(1, 1000)}",
                payment_id=f"pay_{self.rng.randint(100000, 999999)}" if self.rng.choice([True, False]) else None,
                order_id=f"order_{self.rng.randint(10000, 99999)}" if self.rng.choice([True, False]) else None,
                amount=Decimal(str(round(self.rng.uniform(100, 50000), 2))),
                failure_category=self.rng.choice(list(FailureCategory)),
                failure_reason=self.rng.choice(["insufficient_funds", "issuer_declined", "card_expired", "timeout", "abandoned"]),
                retry_count=self.rng.randint(0, 3),
                detected_at=datetime.utcnow() - timedelta(minutes=self.rng.randint(5, 120)),
                created_at=datetime.utcnow()
            )
            leaks.append(leak)
        return leaks


# =============================================================================
# PREDICTION SERVICE INTERFACE (ML)
# =============================================================================

class PredictionService(ABC):
    """ML service interface with calibration."""

    @abstractmethod
    async def predict(self, features: Dict[str, Any]) -> PredictionResult:
        pass


class FakePredictionService(PredictionService):
    """Fake ML service for walking skeleton - calibrated probabilities."""

    def __init__(self, seed: int = 42):
        self.rng = random.Random(seed)
        self.model_version = "synthetic-v1.0-calibrated"

    async def predict(self, features: Dict[str, Any]) -> PredictionResult:
        """Return calibrated probability based on input features."""
        # Simple heuristic for skeleton - higher success history = higher prob
        base_prob = 0.1

        if "customer_history_success_rate" in features:
            success_rate = features["customer_history_success_rate"]
            base_prob = base_prob + (success_rate * 0.4)

        if "retry_count" in features and features["retry_count"] > 2:
            base_prob *= 0.5  # Too many retries

        if "amount" in features and features["amount"] > 10000:
            base_prob *= 0.7  # High value = lower prob

        # Add some noise but keep calibrated
        calibrated = min(1.0, max(0.0, base_prob + self.rng.gauss(0, 0.1)))
        risk_score = 1.0 - calibrated + self.rng.gauss(0, 0.05)
        risk_score = max(0.0, min(1.0, risk_score))

        return PredictionResult(
            recovery_probability=round(calibrated, 4),
            risk_score=round(risk_score, 4),
            model_version=self.model_version,
            calibrated=True
        )


# =============================================================================
# AI RECOMMENDATION SERVICE INTERFACE
# =============================================================================

class AIService(ABC):
    """LLM reasoning layer - understands leak, recommends action."""

    @abstractmethod
    async def analyze(self, context: Dict[str, Any]) -> AIRecommendation:
        pass


class FakeAIService(AIService):
    """Fake AI service for walking skeleton - simulates Claude reasoning."""

    def __init__(self, seed: int = 42):
        self.rng = random.Random(seed)

    async def analyze(self, context: Dict[str, Any]) -> AIRecommendation:
        """Simulate structured, grounded AI recommendation."""

        # Extract context
        leak = context.get("leak")
        prediction = context.get("prediction")
        customer = context.get("customer")

        # Determine recommendation based on context
        failure_cat = leak.failure_category if leak else FailureCategory.UNKNOWN
        failure_reason = leak.failure_reason if leak else "unknown"
        retry_count = leak.retry_count if leak else 0
        recovery_prob = prediction.recovery_probability if prediction else 0.5
        is_control = context.get("is_control", False)

        # Logic for fake AI
        if is_control:
            recommended_action = RecoveryAction.NONE
            reason_codes = [ReasonCode.LOW_PROBABILITY_SUPPRESS]
            diagnosis = "Control group case - no active intervention"
        elif retry_count >= 3:
            recommended_action = RecoveryAction.ESCALATE
            reason_codes = [ReasonCode.REPEAT_FAILURE_ESCALATE]
            diagnosis = "Multiple retries exhausted - escalation recommended"
        elif recovery_prob < 0.3:
            recommended_action = RecoveryAction.NONE
            reason_codes = [ReasonCode.LOW_PROBABILITY_SUPPRESS]
            diagnosis = "Low recovery probability - suppression optimal"
        elif failure_reason == "insufficient_funds":
            recommended_action = RecoveryAction.RETRY
            reason_codes = [ReasonCode.INSUFFICIENT_FUNDS_DELAYED_RETRY]
            diagnosis = "Insufficient funds - delayed retry with reminder"
        elif failure_reason == "card_expired":
            recommended_action = RecoveryAction.FOLLOW_UP
            reason_codes = [ReasonCode.EXPIRED_CARD_REQUEST_UPDATE]
            diagnosis = "Expired card - request card update via SMS"
        elif recovery_prob > 0.7 and not is_control:
            recommended_action = RecoveryAction.RETRY
            reason_codes = [ReasonCode.TRANSIENT_ERROR_FAST_RETRY]
            diagnosis = "High probability - fast retry likely successful"
        else:
            recommended_action = RecoveryAction.REMINDER
            reason_codes = [ReasonCode.ABANDONMENT_SEND_LINK]
            diagnosis = f"{failure_reason or 'issue'} - send reminder/link"

        confidence = min(0.95, max(0.5, recovery_prob + self.rng.gauss(0.1, 0.15)))

        # Generate confidence based on data quality
        if not leak or not customer:
            confidence = 0.3
            diagnosis = "Incomplete data - conservative recommendation"

        # Generate message draft
        message_draft = None
        if recommended_action != RecoveryAction.NONE:
            language = context.get("message_language", "en")
            if language == "hinglish":
                message_draft = f"Hi {customer.customer_id if customer else 'friend'}, payment issue. Try again?"
            else:
                message_draft = f"Payment recovery: {failure_reason}. Action: {recommended_action}"

        # Determine if human review needed
        requires_human = (
            (leak.amount and leak.amount > Decimal("10000")) or
            (recovery_prob < 0.4 and recovery_prob > 0.1) or
            (not customer or not customer.consent_status)
        )

        evidence = []
        if leak:
            evidence.append({"signal": "leak.amount", "value": str(leak.amount)})
            evidence.append({"signal": "leak.failure_reason", "value": leak.failure_reason})
        if prediction:
            evidence.append({"signal": "prediction.recovery_probability", "value": prediction.recovery_probability})
        if customer:
            evidence.append({"signal": "customer.history.success_rate", "value": customer.historical_success_rate})

        return AIRecommendation(
            leak_diagnosis=diagnosis,
            failure_category=failure_cat,
            recommended_action=recommended_action,
            confidence=round(confidence, 4),
            reason_codes=reason_codes,
            evidence=evidence,
            customer_message_draft=message_draft,
            message_language=context.get("message_language", "en"),
            requires_human_review=requires_human
        )


# =============================================================================
# STRATEGY SIMULATOR INTERFACE
# =============================================================================

class StrategySimulator(ABC):
    """Compares strategies by expected NET recovery."""

    @abstractmethod
    async def rank(self, context: Dict[str, Any]) -> List[StrategyOption]:
        pass


class FakeStrategySimulator(StrategySimulator):
    """Fake simulator for walking skeleton."""

    def __init__(self, seed: int = 42):
        self.rng = random.Random(seed)
        self.action_costs = {
            RecoveryAction.RETRY: Decimal("0.5"),
            RecoveryAction.REMINDER: Decimal("1.0"),
            RecoveryAction.INCENTIVE: Decimal("50.0"),
            RecoveryAction.FOLLOW_UP: Decimal("5.0"),
            RecoveryAction.ESCALATE: Decimal("100.0"),
            RecoveryAction.NONE: Decimal("0.0")
        }

    async def rank(self, context: Dict[str, Any]) -> List[StrategyOption]:
        """Rank strategies by expected net recovery."""
        ai_rec = context.get("ai_recommendation")
        if not ai_rec:
            return []

        amount = context.get("amount", Decimal("1000"))
        base_prob = context.get("probability", 0.5)

        # Simulate different actions
        strategies = []

        for action in RecoveryAction:
            # Different probabilities per action
            if action == ai_rec.recommended_action:
                prob_mult = 1.0
            elif action == RecoveryAction.RETRY:
                prob_mult = 0.9
            elif action == RecoveryAction.REMINDER:
                prob_mult = 0.8
            elif action == RecoveryAction.INCENTIVE:
                prob_mult = 0.95
            elif action == RecoveryAction.ESCALATE:
                prob_mult = 0.98
            else:
                prob_mult = 0.1  # NONE

            expected_recovery = amount * Decimal(str(base_prob * prob_mult))
            intervention_cost = self.action_costs.get(action, Decimal("10"))
            expected_net = expected_recovery - intervention_cost

            strategies.append(StrategyOption(
                action=action,
                expected_recovery=expected_recovery,
                intervention_cost=intervention_cost,
                expected_net_recovery=expected_net,
                probability_weighted=expected_net,
                policy_allowed=True,  # Will be set by policy engine
                simulated=True
            ))

        # Sort by expected net recovery (descending)
        strategies.sort(key=lambda x: x.expected_net_recovery, reverse=True)
        return strategies


# =============================================================================
# RAZORPAY GATEWAY INTERFACE (Test Mode)
# =============================================================================

class RazorpayGateway(ABC):
    """Razorpay API wrapper - only Razorpay caller, test mode only."""

    @abstractmethod
    async def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        pass

    @abstractmethod
    async def retry_payment(self, payment_id: str, idempotency_key: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def send_message(self, customer_id: str, message: str, idempotency_key: str) -> Dict[str, Any]:
        pass


class FakeRazorpayGateway(RazorpayGateway):
    """Fake Razorpay gateway for demo/testing."""

    def __init__(self, seed: int = 42):
        self.rng = random.Random(seed)
        self._processed_ids = set()
        self.webhook_secret = "test_webhook_secret"

    async def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """Verify webhook signature (HMAC-SHA256 in real impl)."""
        import hashlib
        import hmac
        expected = hmac.new(
            self.webhook_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(signature, expected)

    async def retry_payment(self, payment_id: str, idempotency_key: str) -> Dict[str, Any]:
        """Simulate payment retry in test mode."""
        if idempotency_key in self._processed_ids:
            return {"status": "idempotent", "payment_id": payment_id}

        self._processed_ids.add(idempotency_key)

        # Simulate outcome
        success = self.rng.random() < 0.6
        amount = Decimal(str(self.rng.uniform(100, 10000)))

        return {
            "status": "captured" if success else "failed",
            "payment_id": payment_id,
            "amount": str(amount),
            "currency": "INR",
            "outcome_amount": str(amount) if success else "0"
        }

    async def send_message(self, customer_id: str, message: str, idempotency_key: str) -> Dict[str, Any]:
        """Simulate sending recovery message."""
        if idempotency_key in self._processed_ids:
            return {"status": "idempotent", "customer_id": customer_id}

        self._processed_ids.add(idempotency_key)
        return {
            "status": "sent",
            "customer_id": customer_id,
            "message_length": len(message)
        }