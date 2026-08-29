"""
Demo Showcase & Replay API Router — RecoverOS
Provides curated showcase scenarios covering ALLOW, HUMAN_REVIEW, DENY, SUPPRESSED, and CONTROL.
"""

from fastapi import APIRouter
from services.policy_engine import PolicyEngine, build_policy_input, POLICY_VERSION
from api.batch import run_batch_recovery
try:
    from backend.models.schemas import DemoInjectRequest
except ImportError:
    from models.schemas import DemoInjectRequest

router = APIRouter(prefix="/demo", tags=["Demo Showcase"])


@router.get("/replay")
def replay_curated_demo():
    """
    Executes a curated replay containing all 5 policy decision pathways:
    1. ALLOW (Standard payment failure retry)
    2. HUMAN_REVIEW (High-value transaction > ₹50,000)
    3. DENY (High dispute history)
    4. SUPPRESSED (Quiet hours / contact frequency limit)
    5. CONTROL (Holdout group case)
    """
    req = DemoInjectRequest(seed=42, case_count=20, holdout_ratio=0.20)
    report = run_batch_recovery(req)
    
    return {
        "status": "Demo Replay Executed Successfully",
        "policy_version": POLICY_VERSION,
        "showcase_outcomes": {
            "ALLOW": "Payment retry executed with valid policy token",
            "HUMAN_REVIEW": "High-value case routed to compliant escalation queue",
            "DENY": "Dispute history flagged, recovery blocked",
            "SUPPRESSED": "Quiet hours active, case suppressed",
            "CONTROL": "Assigned to holdout control group for measured uplift math"
        },
        "batch_report": report
    }
