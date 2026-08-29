"""
Governed, idempotent recovery tools for RecoverOS.

CRITICAL: These tools ONLY execute when:
1. Provided with a valid PolicyResult token proving PolicyDecision.ALLOW
2. Provided with an idempotency key
3. The tool itself validates these before execution

They are the ONLY place financial actions can occur - never called directly by LLM.
"""

from typing import Optional, Dict, Any
import asyncio
import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum

try:
    from backend.models.schemas import (
        RecoveryAction, RecoveryActionResult,
        CustomerProfile
    )
except ImportError:
    from models.schemas import (
        RecoveryAction, RecoveryActionResult,
        CustomerProfile
    )
from services.interfaces import RazorpayGateway


# =============================================================================
# IDEMPOTENCY MANAGER
# =============================================================================

class IdempotencyManager:
    """Tracks idempotency keys to prevent duplicate executions."""

    def __init__(self):
        self._processed: set = set()
        # In production, this would be Redis or DB table with TTL

    async def is_processed(self, key: str) -> bool:
        return key in self._processed

    async def mark_processed(self, key: str):
        self._processed.add(key)

    def clear(self):
        self._processed.clear()


# Global idempotency manager (in prod: use Redis with TTL)
_idempotency_manager = IdempotencyManager()


# =============================================================================
# POLICY TOKEN VALIDATOR
# =============================================================================

def validate_policy_token(token: str, expected_case_id: str) -> bool:
    """
    Validates that the token is a proof of PolicyResult.ALLOW for the given case.
    In reality, this would be a signed JWT or HMAC.
    For walking skeleton: token format: "allow:{case_id}:{timestamp}:{signature}"
    """
    if not token or not token.startswith("allow:"):
        return False

    parts = token.split(":")
    if len(parts) < 3:
        return False

    case_id = parts[1]
    return case_id == expected_case_id


# =============================================================================
# RECOVERY TOOLS
# =============================================================================

class RecoveryTools:
    """Governed recovery tools - stateless, idempotent, gated."""

    def __init__(
        self,
        razorpay_gateway: RazorpayGateway,
        idempotency_manager: Optional[IdempotencyManager] = None
    ):
        self.razorpay = razorpay_gateway
        self.idempotency = idempotency_manager or _idempotency_manager

    async def _check_gate(
        self,
        case_id: str,
        idempotency_key: str,
        policy_token: str
    ) -> None:
        """Validate governance requirements - raises if not met."""

        # 1. Idempotency check
        if await self.idempotency.is_processed(idempotency_key):
            raise ValueError(f"Idempotency key already processed: {idempotency_key}")

        # 2. Policy token validation
        if not validate_policy_token(policy_token, case_id):
            raise ValueError(f"Invalid or missing policy token for case {case_id}")

    async def retry_payment(
        self,
        case_id: str,
        payment_id: str,
        idempotency_key: str,
        policy_token: str
    ) -> RecoveryActionResult:
        """
        Execute payment retry - ONLY if policy allows and idempotent.
        This tool refuses to run without proof of ALLOW.
        """
        await self._check_gate(case_id, idempotency_key, policy_token)

        # Mark as processed BEFORE execution to prevent race conditions
        await self.idempotency.mark_processed(idempotency_key)

        try:
            result = await self.razorpay.retry_payment(payment_id, idempotency_key)

            success = result.get("status") == "captured"
            outcome_amount = Decimal(result.get("outcome_amount", "0")) if success else Decimal("0")

            return RecoveryActionResult(
                success=success,
                action_taken=RecoveryAction.RETRY,
                outcome_amount=outcome_amount,
                razorpay_response=result
            )

        except Exception as e:
            # Still count as processed to prevent retry loops on same key
            return RecoveryActionResult(
                success=False,
                action_taken=RecoveryAction.RETRY,
                error=str(e)
            )

    async def send_recovery_message(
        self,
        case_id: str,
        customer_id: str,
        message: str,
        idempotency_key: str,
        policy_token: str
    ) -> RecoveryActionResult:
        """Send recovery message (SMS/WhatsApp/email) - governed & idempotent."""
        await self._check_gate(case_id, idempotency_key, policy_token)

        await self.idempotency.mark_processed(idempotency_key)

        try:
            result = await self.razorpay.send_message(customer_id, message, idempotency_key)

            return RecoveryActionResult(
                success=True,
                action_taken=RecoveryAction.REMINDER,
                razorpay_response=result
            )

        except Exception as e:
            return RecoveryActionResult(
                success=False,
                action_taken=RecoveryAction.REMINDER,
                error=str(e)
            )

    async def follow_up(
        self,
        case_id: str,
        customer_id: str,
        follow_up_type: str,
        idempotency_key: str,
        policy_token: str
    ) -> RecoveryActionResult:
        """Schedule follow-up call or action."""
        await self._check_gate(case_id, idempotency_key, policy_token)

        await self.idempotency.mark_processed(idempotency_key)

        # Simulate follow-up scheduling
        await asyncio.sleep(0.01)  # Simulate work

        return RecoveryActionResult(
            success=True,
            action_taken=RecoveryAction.FOLLOW_UP,
            razorpay_response={
                "follow_up_type": follow_up_type,
                "customer_id": customer_id,
                "scheduled_for": datetime.utcnow().isoformat()
            }
        )

    async def escalate_to_human(
        self,
        case_id: str,
        reason: str,
        idempotency_key: str,
        policy_token: str
    ) -> RecoveryActionResult:
        """Escalate case to human review queue."""
        await self._check_gate(case_id, idempotency_key, policy_token)

        await self.idempotency.mark_processed(idempotency_key)

        # Simulate creating human review ticket
        await asyncio.sleep(0.01)

        return RecoveryActionResult(
            success=True,
            action_taken=RecoveryAction.ESCALATE,
            razorpay_response={
                "escalation_id": f"esc_{uuid.uuid4().hex[:8]}",
                "case_id": case_id,
                "reason": reason,
                "created_at": datetime.utcnow().isoformat(),
                "queue": "high_priority"
            }
        )

    async def record_audit_event(
        self,
        case_id: str,
        event_type: str,
        details: Dict[str, Any],
        idempotency_key: str,
        policy_token: str
    ) -> RecoveryActionResult:
        """Record an audit event - idempotent write."""
        await self._check_gate(case_id, idempotency_key, policy_token)

        await self.idempotency.mark_processed(idempotency_key)

        # In reality: write to audit_events table
        audit_record = {
            "case_id": case_id,
            "event_type": event_type,
            "details": details,
            "timestamp": datetime.utcnow().isoformat(),
            "idempotency_key": idempotency_key
        }

        return RecoveryActionResult(
            success=True,
            action_taken=RecoveryAction.NONE,  # Audit is not a financial action
            razorpay_response=audit_record
        )


# =============================================================================
# FACTORY FOR WALKING SKELETON
# =============================================================================

def create_recovery_tools_for_skeleton() -> RecoveryTools:
    """Factory for walking skeleton - uses fake Razorpay gateway."""
    from .interfaces import FakeRazorpayGateway
    gateway = FakeRazorpayGateway(seed=42)
    return RecoveryTools(razorpay_gateway=gateway)