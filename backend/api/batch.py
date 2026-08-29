"""
Batch Recovery API Router — RecoverOS
Handles BatchRecoveryRun simulation with holdout group assignment and uplift report.
"""

import uuid
import random
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db.database import get_db
try:
    from backend.models.schemas import (
        DemoInjectRequest, BatchRecoveryReport,
        RecoveryAction, LeakSource, FailureCategory
    )
except ImportError:
    from models.schemas import (
        DemoInjectRequest, BatchRecoveryReport,
        RecoveryAction, LeakSource, FailureCategory
    )
from services.policy_engine import PolicyEngine, build_policy_input, POLICY_VERSION, calculate_priority_score
from services.recovery_tools import create_recovery_tools_for_skeleton
from services.interfaces import FakePredictionService, FakeAIService, FakeStrategySimulator
from services.ml_engine import get_ml_engine
from services.ai_engine import get_ai_engine
from api.cases import set_cases_cache

router = APIRouter(prefix="/batch", tags=["Batch Recovery"])

prediction_svc = FakePredictionService()
ai_svc = FakeAIService()
strategy_svc = FakeStrategySimulator()
tools = create_recovery_tools_for_skeleton()
policy_engine = PolicyEngine()

_LATEST_BATCH_REPORT = None


@router.post("/recovery", response_model=BatchRecoveryReport)
def run_batch_recovery(req: DemoInjectRequest, db: Session = Depends(get_db)):
    """
    Executes a BatchRecoveryRun with random holdout control assignment.
    Calculates measured money recovered, incremental revenue, and guardrail metrics across the batch.
    """
    global _LATEST_BATCH_REPORT
    
    random.seed(req.seed)
    
    cases_dict = {}
    treatment_cases = []
    control_cases = []
    
    total_revenue_at_risk = Decimal("0.00")
    treatment_recovered = Decimal("0.00")
    control_recovered = Decimal("0.00")
    
    suppressed_count = 0
    human_review_count = 0
    denied_count = 0
    
    for i in range(req.case_count):
        case_id = f"case_{uuid.uuid4().hex[:8]}"
        amount = Decimal(str(round(random.uniform(500, 25000), 2)))
        total_revenue_at_risk += amount
        
        is_control = random.random() < req.holdout_ratio
        
        # Pick leak source across all 4 Track 03 directions
        leak_sources = ["payment_failure", "checkout_abandonment", "subscription_failure", "overdue_receivable"]
        leak_source = random.choice(leak_sources)

        leak_enum_map = {
            "payment_failure": LeakSource.PAYMENT_FAILURE,
            "checkout_abandonment": LeakSource.CHECKOUT_ABANDONMENT,
            "subscription_failure": LeakSource.SUBSCRIPTION_FAILURE,
            "overdue_receivable": LeakSource.OVERDUE_RECEIVABLE
        }
        
        # Build policy input & compute ML probability
        customer_ltv = Decimal(str(round(random.uniform(1000, 100000), 2)))
        contact_count = random.choice([0, 1, 1, 2, 3, 4])
        has_dispute = random.random() < 0.05
        is_quiet = random.random() < 0.10
        failure_cat = random.choice(["network_timeout", "insufficient_funds", "issuer_decline", "abandonment"])

        ml_engine = get_ml_engine()
        ai_engine = get_ai_engine()

        p_recovery, brier_score = ml_engine.predict_p_recovery(
            amount_inr=float(amount),
            customer_ltv=float(customer_ltv),
            contact_count_7d=contact_count,
            retry_count=0,
            failure_category=failure_cat,
            leak_source=leak_source,
            is_quiet_hours=is_quiet
        )

        ai_rec = ai_engine.generate_recommendation(
            leak_id=case_id,
            amount_inr=float(amount),
            failure_category=failure_cat,
            leak_source=leak_source,
            customer_name=f"Customer {i+1}",
            customer_ltv=float(customer_ltv),
            p_recovery=p_recovery
        )

        policy_input = build_policy_input(
            recovery_probability=p_recovery,
            risk_score=0.1 if not has_dispute else 0.8,
            amount=amount,
            retry_count=0,
            proposed_action=RecoveryAction.RETRY if ai_rec.recommended_action == "retry" else RecoveryAction.REMINDER,
            leak_source=leak_enum_map.get(leak_source, LeakSource.PAYMENT_FAILURE),
            failure_category=FailureCategory.NETWORK_TIMEOUT if failure_cat == "network_timeout" else FailureCategory.ABANDONMENT,
            customer_consent=True,
            customer_contact_count_24h=1 if contact_count > 0 else 0,
            customer_contact_count_7d=contact_count,
            is_current_hour_quiet=is_quiet
        )

        stop_decision = policy_engine.check_stopping_rules(policy_input)
        if stop_decision.stop:
            decision = "SUPPRESSED"
            reason_code = stop_decision.rule.value if stop_decision.rule else "STOPPING_RULE"
            policy_token = None
        else:
            policy_decision, policy_reason, details = policy_engine.evaluate(policy_input)
            decision = policy_decision.value
            reason_code = policy_reason.value
            policy_token = f"tok_{uuid.uuid4().hex[:12]}" if decision == "ALLOW" else None

        if is_control:
            decision = "CONTROL"
            reason_code = "HOLDOUT_CONTROL_GROUP"
        
        # Calculate simulated recovery
        recovered_amount = Decimal("0.00")
        if decision == "ALLOW":
            if random.random() < p_recovery:
                recovered_amount = amount
            treatment_recovered += recovered_amount
            treatment_cases.append(case_id)
        elif decision == "CONTROL":
            baseline_prob = p_recovery * 0.4  # Control group baseline recovery
            if random.random() < baseline_prob:
                recovered_amount = amount
            control_recovered += recovered_amount
            control_cases.append(case_id)
        elif decision == "SUPPRESSED":
            suppressed_count += 1
        elif decision == "HUMAN_REVIEW":
            human_review_count += 1
        elif decision == "DENY":
            denied_count += 1
            
        p_score, p_tier = calculate_priority_score(
            amount=float(amount),
            failure_category=failure_cat,
            customer_segment="Premium" if customer_ltv > 50000 else "Regular",
            customer_ltv=float(customer_ltv),
            retry_count=0
        )

        cases_dict[case_id] = {
            "case_id": case_id,
            "leak_source": leak_source,
            "amount_inr": float(amount),
            "customer_id": f"cust_{i+100}",
            "customer_ltv": float(customer_ltv),
            "contact_history_count": contact_count,
            "p_recovery": p_recovery,
            "priority_score": p_score,
            "priority_tier": p_tier,
            "diagnosis": ai_rec.leak_diagnosis,
            "recommended_action": str(ai_rec.recommended_action.value if hasattr(ai_rec.recommended_action, 'value') else ai_rec.recommended_action),
            "draft_message": ai_rec.customer_message_draft,
            "decision": decision,
            "reason_code": reason_code,
            "policy_token": policy_token,
            "policy_version": POLICY_VERSION,
            "is_control": is_control,
            "recovered_amount": float(recovered_amount),
            "created_at": datetime.utcnow().isoformat() + "Z"
        }
        
    set_cases_cache(cases_dict)
    
    t_count = len(treatment_cases) or 1
    c_count = len(control_cases) or 1
    
    t_rate = (len([c for c in treatment_cases if cases_dict[c]["recovered_amount"] > 0]) / t_count) * 100
    c_rate = (len([c for c in control_cases if cases_dict[c]["recovered_amount"] > 0]) / c_count) * 100
    uplift_pp = t_rate - c_rate
    
    measured_money = treatment_recovered + control_recovered
    incremental_rev = treatment_recovered - (control_recovered * Decimal(str(t_count / c_count)))
    if incremental_rev < Decimal("0"):
        incremental_rev = Decimal("0.00")
        
    cost = Decimal(str(round(t_count * 5.0, 2)))  # ₹5 per intervention
    net_rec = measured_money - cost
    
    cost_per_rupee = (cost / measured_money) if measured_money > 0 else Decimal("0.00")

    report = BatchRecoveryReport(
        cases_detected=req.case_count,
        revenue_at_risk=total_revenue_at_risk,
        treatment_count=len(treatment_cases),
        control_count=len(control_cases),
        recovery_rate_treatment=round(t_rate, 2),
        recovery_rate_control=round(c_rate, 2),
        incremental_recovery_rate_pp=round(uplift_pp, 2),
        measured_money_recovered=measured_money,
        incremental_revenue=incremental_rev,
        intervention_cost=cost,
        net_recovered=net_rec,
        cost_per_rupee_recovered=round(cost_per_rupee, 4),
        guardrail_metrics={
            "suppression_rate": f"{(suppressed_count / req.case_count)*100:.1f}%",
            "human_review_rate": f"{(human_review_count / req.case_count)*100:.1f}%",
            "policy_block_rate": f"{(denied_count / req.case_count)*100:.1f}%",
            "opt_out_rate": "0.0%",
            "repeat_contact_rate": "0.0%"
        }
    )
    
    _LATEST_BATCH_REPORT = report
    return report


@router.get("/reports")
def get_batch_reports():
    """Retrieve the latest batch recovery performance report."""
    if not _LATEST_BATCH_REPORT:
        return {"message": "No batch recovery run executed yet. Run POST /batch/recovery first."}
    return _LATEST_BATCH_REPORT
