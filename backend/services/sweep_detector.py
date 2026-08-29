"""
RecoverOS Checkout Abandonment Sweep Detector
Runs scheduled background sweeps to identify unpaid abandoned checkout sessions (> N minutes old).
Normalizes abandoned checkouts into RevenueLeak entities and triggers the decision engine.
"""

import uuid
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any

try:
    from backend.models.schemas import RevenueLeak, LeakSource, FailureCategory, RecoveryAction
except ImportError:
    from models.schemas import RevenueLeak, LeakSource, FailureCategory, RecoveryAction
from services.policy_engine import PolicyEngine, build_policy_input
from services.ml_engine import get_ml_engine
from services.ai_engine import get_ai_engine

logger = logging.getLogger("recoveros.sweep_detector")


class CheckoutAbandonmentSweepDetector:
    """Scheduled background worker detecting unpaid abandoned checkout sessions."""

    def __init__(self, abandonment_threshold_minutes: int = 30):
        self.threshold_minutes = abandonment_threshold_minutes
        self.policy_engine = PolicyEngine()

    def run_sweep(self, active_checkouts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Processes list of active checkouts.
        Flags sessions created > threshold_minutes ago with no completed payment.
        """
        now = datetime.utcnow()
        abandoned_cases = []

        for checkout in active_checkouts:
            created_at = checkout.get("created_at")
            if isinstance(created_at, str):
                created_at = datetime.fromisoformat(created_at.replace("Z", ""))
                
            elapsed_minutes = (now - created_at).total_seconds() / 60.0
            
            # Check if checkout is abandoned (> 30 mins unpaid)
            if elapsed_minutes >= self.threshold_minutes and not checkout.get("is_paid", False):
                case_id = f"leak_abnd_{checkout.get('order_id', uuid.uuid4().hex[:8])}"
                amount = float(checkout.get("amount_inr", 1500.0))

                # Compute ML & AI predictions
                ml_engine = get_ml_engine()
                ai_engine = get_ai_engine()

                p_recovery, _ = ml_engine.predict_p_recovery(
                    amount_inr=amount,
                    customer_ltv=checkout.get("customer_ltv", 5000.0),
                    contact_count_7d=checkout.get("contact_count_7d", 0),
                    retry_count=0,
                    failure_category="abandonment",
                    leak_source="checkout_abandonment",
                    is_quiet_hours=False
                )

                ai_rec = ai_engine.generate_recommendation(
                    leak_id=case_id,
                    amount_inr=amount,
                    failure_category="abandonment",
                    leak_source="checkout_abandonment",
                    customer_name=checkout.get("customer_name", "Customer"),
                    p_recovery=p_recovery
                )

                # Policy Engine Evaluation
                policy_input = build_policy_input(
                    recovery_probability=p_recovery,
                    risk_score=0.05,
                    amount=amount,
                    retry_count=0,
                    proposed_action=RecoveryAction.REMINDER,
                    leak_source=LeakSource.CHECKOUT_ABANDONMENT,
                    failure_category=FailureCategory.ABANDONMENT,
                    customer_consent=True,
                    customer_contact_count_24h=0,
                    customer_contact_count_7d=checkout.get("contact_count_7d", 0),
                    is_current_hour_quiet=False
                )

                p_dec, p_reas, _ = self.policy_engine.evaluate(policy_input)

                abandoned_case = {
                    "case_id": case_id,
                    "order_id": checkout.get("order_id"),
                    "amount_inr": amount,
                    "elapsed_minutes": round(elapsed_minutes, 1),
                    "p_recovery": p_recovery,
                    "decision": p_dec.value,
                    "reason_code": p_reas.value,
                    "ai_diagnosis": ai_rec.leak_diagnosis,
                    "draft_message": ai_rec.customer_message_draft
                }

                abandoned_cases.append(abandoned_case)
                logger.info(f"Sweep detected abandoned checkout '{case_id}' (elapsed: {elapsed_minutes:.1f} mins).")

        return abandoned_cases


_sweep_detector = CheckoutAbandonmentSweepDetector()


def get_sweep_detector() -> CheckoutAbandonmentSweepDetector:
    return _sweep_detector
