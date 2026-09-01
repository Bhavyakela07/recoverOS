"""
Razorpay Webhook Receiver API Router — RecoverOS
Consumes signature-verified webhooks for payment.failed, payment.captured, order.paid.
Enforces database-authoritative idempotency and complete payment lifecycle state transitions.
"""

import json
import logging
import uuid
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any
from fastapi import APIRouter, Request, HTTPException, Header, Depends
from sqlalchemy.orm import Session

from db.database import get_db
from db.models import (
    WebhookEventModel,
    RevenueLeakModel,
    RecoveryCaseModel,
    AIDecisionModel,
    PaymentLinkModel,
    EmailMessageModel,
    AuditEventModel
)
from utils.security import verify_razorpay_webhook_signature
try:
    from backend.models.schemas import RevenueLeak, LeakSource, FailureCategory, RecoveryAction
except ImportError:
    from models.schemas import RevenueLeak, LeakSource, FailureCategory, RecoveryAction
from services.policy_engine import PolicyEngine, build_policy_input, POLICY_VERSION
from services.ml_engine import get_ml_engine
from services.ai_engine import get_ai_engine
from services.email_dispatcher import send_direct_email_reminder
from services.razorpay_service import get_razorpay_service

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
    Enforces HMAC SHA-256 signature verification and database-authoritative idempotency.
    """
    raw_body = await request.body()

    # 1. Signature Verification
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
        raw_hash = hashlib.sha256(raw_body).hexdigest()[:16]
        event_id = f"evt_{raw_hash}"

    logger.info(f"Received Razorpay Webhook Event: '{event_name}' (ID: {event_id})")

    # 2. Database-Authoritative Idempotency Check
    existing_evt = db.query(WebhookEventModel).filter(WebhookEventModel.event_id == event_id).first()
    if existing_evt and existing_evt.processing_status in ("PROCESSED", "PROCESSING"):
        logger.info(f"Duplicate webhook event '{event_id}' detected in database. Skipping duplicate execution.")
        return {
            "status": "ignored",
            "message": f"Duplicate event '{event_id}' already processed.",
            "event": event_name
        }

    # Record webhook event in database (Authoritative Idempotency Record)
    raw_payload_hash = hashlib.sha256(raw_body).hexdigest()
    if not existing_evt:
        db_event = WebhookEventModel(
            id=f"we_{uuid.uuid4().hex[:12]}",
            event_id=event_id,
            event_type=event_name,
            processing_status="PROCESSING",
            raw_payload_hash=raw_payload_hash,
            received_at=datetime.now(timezone.utc)
        )
        db.add(db_event)
        try:
            db.commit()
        except Exception as db_err:
            db.rollback()
            logger.warning(f"Idempotency race condition caught on event_id '{event_id}': {db_err}")
            return {
                "status": "ignored",
                "message": f"Duplicate event '{event_id}' caught concurrently.",
                "event": event_name
            }
    else:
        db_event = existing_evt

    # 3. Handle payment.failed event
    if event_name == "payment.failed":
        payment_entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
        
        amount_inr = float(payment_entity.get("amount", 0)) / 100.0
        if amount_inr <= 0:
            amount_inr = 4500.0

        error_code = payment_entity.get("error_code", "network_timeout")
        error_reason = payment_entity.get("error_reason", "technical_error")
        payment_id = payment_entity.get("id", f"pay_{uuid.uuid4().hex[:8]}")
        customer_email = payment_entity.get("email", "customer@example.com")
        customer_name = payment_entity.get("notes", {}).get("customer_name") or "Valued Customer"

        failure_cat = "network_timeout"
        if "insufficient" in error_reason.lower() or "funds" in error_reason.lower():
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
            customer_name=customer_name,
            customer_ltv=10000.0,
            p_recovery=p_recovery
        )

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
            decision = "DO_NOT_RETRY" if "INSUFFICIENT" in str(stop_decision.rule) else "SUPPRESSED"
            reason_code = stop_decision.rule.value if stop_decision.rule else "STOPPING_RULE"
        else:
            p_dec, p_reas, _ = policy_engine.evaluate(policy_input)
            decision = p_dec.value
            reason_code = p_reas.value

        # Insert Database Models (Revenue Leak & Recovery Case State Machine)
        leak_db = RevenueLeakModel(
            id=f"leak_{payment_id}",
            event_id=event_id,
            leak_source="payment_failed",
            failure_category=failure_cat,
            amount_inr=amount_inr,
            status="FAILED"
        )
        db.add(leak_db)

        lifecycle_st = "RECOVERY_RECOMMENDED" if decision == "ALLOW" else ("DO_NOT_RETRY" if decision == "DO_NOT_RETRY" else "SUPPRESSED")
        case_db = RecoveryCaseModel(
            id=f"case_{payment_id}",
            leak_id=leak_db.id,
            decision=decision,
            reason_code=reason_code,
            p_recovery=p_recovery,
            lifecycle_status=lifecycle_st
        )
        db.add(case_db)

        # AIDecisionModel
        ai_dec_db = AIDecisionModel(
            id=f"aidec_{payment_id}",
            case_id=case_db.id,
            diagnosis=ai_rec.leak_diagnosis,
            recommended_action=ai_rec.recommended_action,
            rationale=reason_code,
            confidence_score=0.92,
            draft_message_json={"message": ai_rec.customer_message_draft}
        )
        db.add(ai_dec_db)

        payment_link_res = None
        email_result = None

        if decision == "ALLOW":
            order_id_clean = f"RZP-{str(payment_id).replace('pay_', '')[:5]}"
            rzp_service = get_razorpay_service()
            payment_link_res = rzp_service.create_payment_link(
                amount_inr=amount_inr,
                order_id=order_id_clean,
                customer_name=customer_name,
                customer_email=customer_email
            )

            # Insert PaymentLinkModel
            plink_db = PaymentLinkModel(
                id=f"pl_{uuid.uuid4().hex[:10]}",
                case_id=case_db.id,
                razorpay_link_id=payment_link_res["link_id"],
                short_url=payment_link_res["short_url"],
                amount_inr=amount_inr,
                status="CREATED"
            )
            db.add(plink_db)

            # Email Dispatch
            email_result = send_direct_email_reminder(
                recipient_email=customer_email,
                customer_name=customer_name,
                amount=amount_inr,
                order_id=order_id_clean,
                failure_reason=failure_cat,
                payment_link=payment_link_res["short_url"]
            )

            # Insert EmailMessageModel
            email_db = EmailMessageModel(
                id=f"em_{uuid.uuid4().hex[:10]}",
                case_id=case_db.id,
                recipient_email=customer_email,
                subject=email_result["subject"],
                payment_link_id=plink_db.id,
                dispatch_id=email_result["dispatch_id"],
                status="DELIVERED"
            )
            db.add(email_db)

            case_db.lifecycle_status = "CUSTOMER_CONTACTED"

        # Complete Webhook Processing
        db_event.processing_status = "PROCESSED"
        db_event.processed_at = datetime.now(timezone.utc)

        db.commit()

        return {
            "status": "processed",
            "event_id": event_id,
            "payment_id": payment_id,
            "amount_inr": amount_inr,
            "p_recovery": p_recovery,
            "decision": decision,
            "reason_code": reason_code,
            "lifecycle_status": case_db.lifecycle_status,
            "payment_link": payment_link_res["short_url"] if payment_link_res else None,
            "email_dispatch": email_result
        }

    # 4. Handle payment.captured / order.paid events (CLOSED-LOOP OUTCOME RECORDING)
    elif event_name in ("payment.captured", "order.paid"):
        payment_entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
        payment_id = payment_entity.get("id")
        amount_inr = float(payment_entity.get("amount", 0)) / 100.0

        # Look up matching recovery case or payment link in database
        recovered_case = None
        if payment_id:
            # Direct lookup by case_id / leak_id
            recovered_case = db.query(RecoveryCaseModel).filter(RecoveryCaseModel.id == f"case_{payment_id}").first()
            if not recovered_case:
                plink_rec = db.query(PaymentLinkModel).filter(PaymentLinkModel.razorpay_link_id == payment_id).first()
                if plink_rec:
                    recovered_case = db.query(RecoveryCaseModel).filter(RecoveryCaseModel.id == plink_rec.case_id).first()
                    plink_rec.status = "PAID"

        if not recovered_case:
            # Fallback: search open cases
            recovered_case = db.query(RecoveryCaseModel).filter(RecoveryCaseModel.lifecycle_status.in_(["CUSTOMER_CONTACTED", "RECOVERY_LINK_CREATED", "RECOVERY_RECOMMENDED"])).first()

        if recovered_case:
            recovered_case.lifecycle_status = "RECOVERED"
            recovered_case.expected_net_recovery = amount_inr or float(recovered_case.leak.amount_inr if recovered_case.leak else 4500.0)
            
            # Record Audit Event
            audit_entry = AuditEventModel(
                id=f"aud_{uuid.uuid4().hex[:10]}",
                case_id=recovered_case.id,
                event_type="PAYMENT_CAPTURED_CLOSED_LOOP",
                payload_json={"event_id": event_id, "payment_id": payment_id, "recovered_amount": amount_inr},
                sha256_signature=hashlib.sha256(f"{recovered_case.id}:{payment_id}:{amount_inr}".encode()).hexdigest()
            )
            db.add(audit_entry)

        db_event.processing_status = "PROCESSED"
        db_event.processed_at = datetime.now(timezone.utc)
        db.commit()

        return {
            "status": "processed",
            "event_id": event_id,
            "event": event_name,
            "case_status": "RECOVERED" if recovered_case else "UNMATCHED_PAYMENT_RECORDED",
            "amount_recovered": amount_inr
        }

    db_event.processing_status = "PROCESSED"
    db_event.processed_at = datetime.now(timezone.utc)
    db.commit()

    return {
        "status": "acknowledged",
        "event_id": event_id,
        "event": event_name,
        "message": "Event recorded."
    }
