"""
Razorpay Webhook Receiver API Router — RecoverOS
Consumes signature-verified webhooks for payment.failed, payment.captured, order.paid.
Enforces double-webhook idempotency so duplicate deliveries produce zero duplicate actions.
"""

import json
import logging
from typing import Dict, Any
from fastapi import APIRouter, Request, HTTPException, Header, Depends
from sqlalchemy.orm import Session

from db.database import get_db
from utils.security import verify_razorpay_webhook_signature
try:
    from backend.models.schemas import RevenueLeak, LeakSource, FailureCategory, RecoveryAction
except ImportError:
    from models.schemas import RevenueLeak, LeakSource, FailureCategory, RecoveryAction
from services.policy_engine import PolicyEngine, build_policy_input, POLICY_VERSION
from services.ml_engine import get_ml_engine
from services.ai_engine import get_ai_engine
from services.recovery_tools import _idempotency_manager

logger = logging.getLogger("recoveros.webhooks")

router = APIRouter(prefix="/webhook", tags=["Webhooks"])
policy_engine = PolicyEngine()


@router.post("/razorpay")
async def receive_razorpay_webhook(
    request: Request,
    x_razorpay_signature: str = Header(None, alias="X-Razorpay-Signature"),
    db: Session = Depends(get_db)
):
    """
    Consumes Razorpay Webhooks (payment.failed, payment.captured, order.paid).
    Verifies HMAC-SHA256 signature and enforces event idempotency.
    """
    raw_body = await request.body()

    # 1. Verify Signature
    if not x_razorpay_signature or not verify_razorpay_webhook_signature(raw_body, x_razorpay_signature):
        logger.warning("Rejected Razorpay webhook due to invalid HMAC signature.")
        raise HTTPException(status_code=400, detail="Invalid webhook signature.")

    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except Exception as err:
        raise HTTPException(status_code=400, detail=f"Invalid JSON body: {err}")

    event_name = payload.get("event")
    event_id = payload.get("event_id") or payload.get("payload", {}).get("payment", {}).get("entity", {}).get("id")

    if not event_id:
        event_id = f"evt_{hash(raw_body)}"

    logger.info(f"Received Razorpay Webhook Event: '{event_name}' (ID: {event_id})")

    # 2. Idempotency Check (Double-Webhook Defense)
    if await _idempotency_manager.is_processed(event_id):
        logger.info(f"Duplicate webhook event '{event_id}' detected. Skipping duplicate execution.")
        return {
            "status": "ignored",
            "message": f"Duplicate event '{event_id}' already processed.",
            "event": event_name
        }

    # Record idempotency key
    await _idempotency_manager.mark_processed(event_id)

    # 3. Handle payment.failed event
    if event_name == "payment.failed":
        payment_entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
        
        amount_inr = float(payment_entity.get("amount", 0)) / 100.0
        error_code = payment_entity.get("error_code", "network_timeout")
        error_reason = payment_entity.get("error_reason", "technical_error")
        payment_id = payment_entity.get("id", "pay_unknown")
        customer_email = payment_entity.get("email", "customer@example.com")
        customer_contact = payment_entity.get("contact", "+919876543210")

        # Normalize failure category
        failure_cat = "network_timeout"
        if "insufficient" in error_reason.lower():
            failure_cat = "insufficient_funds"
        elif "decline" in error_reason.lower() or "card" in error_reason.lower():
            failure_cat = "issuer_decline"

        # Compute ML Probability & AI Reasoning
        ml_engine = get_ml_engine()
        ai_engine = get_ai_engine()

        p_recovery, brier = ml_engine.predict_p_recovery(
            amount_inr=amount_inr,
            customer_ltv=10000.0,
            contact_count_7d=0,
            retry_count=0,
            failure_category=failure_cat,
            leak_source="payment_failed",
            is_quiet_hours=False
        )

        ai_rec = ai_engine.generate_recommendation(
            leak_id=event_id,
            amount_inr=amount_inr,
            failure_category=failure_cat,
            leak_source="payment_failed",
            customer_email=customer_email,
            customer_name="Valued Customer",
            customer_ltv=10000.0,
            p_recovery=p_recovery
        )

        # Build Policy Input
        policy_input = build_policy_input(
            recovery_probability=p_recovery,
            risk_score=0.1,
            amount=amount_inr,
            retry_count=0,
            proposed_action=RecoveryAction.RETRY if ai_rec.recommended_action == "retry" else RecoveryAction.REMINDER,
            leak_source=LeakSource.PAYMENT_FAILURE,
            failure_category=FailureCategory.NETWORK_TIMEOUT if failure_cat == "network_timeout" else FailureCategory.ISSUER_DECLINE,
            customer_consent=True,
            customer_contact_count_24h=0,
            customer_contact_count_7d=0,
            is_current_hour_quiet=False
        )

        stop_decision = policy_engine.check_stopping_rules(policy_input)
        if stop_decision.stop:
            decision = "SUPPRESSED"
            reason_code = stop_decision.rule.value if stop_decision.rule else "STOPPING_RULE"
        else:
            p_dec, p_reas, _ = policy_engine.evaluate(policy_input)
            decision = p_dec.value
            reason_code = p_reas.value

        return {
            "status": "processed",
            "event_id": event_id,
            "payment_id": payment_id,
            "amount_inr": amount_inr,
            "p_recovery": p_recovery,
            "decision": decision,
            "reason_code": reason_code,
            "ai_diagnosis": ai_rec.leak_diagnosis,
            "draft_message": ai_rec.customer_message_draft
        }

    return {
        "status": "acknowledged",
        "event_id": event_id,
        "event": event_name,
        "message": "Event recorded."
    }
