"""
Recovery Cases API Router — RecoverOS
Handles filtering cases, detail view, and Decision Dossier export.
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session

from db.database import get_db
try:
    from backend.models.schemas import DecisionDossier
except ImportError:
    from models.schemas import DecisionDossier

router = APIRouter(prefix="/cases", tags=["Cases"])

# Global in-memory storage fallback for simulation cases
_CASES_CACHE = {}


def set_cases_cache(cases_dict):
    global _CASES_CACHE
    _CASES_CACHE = cases_dict


def get_cases_cache():
    return _CASES_CACHE


@router.get("")
def list_cases(
    is_control: Optional[bool] = Query(None, description="Filter by control group"),
    leak_source: Optional[str] = Query(None, description="Filter by leak source"),
    decision: Optional[str] = Query(None, description="Filter by decision (ALLOW, HUMAN_REVIEW, DENY, SUPPRESSED, CONTROL)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """List recovery cases with rich filtering and pagination."""
    cases = list(_CASES_CACHE.values())
    
    if is_control is not None:
        cases = [c for c in cases if c.get("is_control") == is_control]
    if leak_source:
        cases = [c for c in cases if c.get("leak_source") == leak_source]
    if decision:
        cases = [c for c in cases if c.get("decision") == decision]

    total = len(cases)
    start = (page - 1) * page_size
    end = start + page_size
    paginated_cases = cases[start:end]

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "cases": paginated_cases
    }


@router.get("/{case_id}")
def get_case_detail(case_id: str):
    """Retrieve detailed case information by ID."""
    if case_id not in _CASES_CACHE:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found.")
    return _CASES_CACHE[case_id]


@router.get("/{case_id}/dossier")
def export_decision_dossier(case_id: str):
    """
    Export one-click audit Decision Dossier for compliance and human review.
    Contains raw leak event, ML predictions, Claude AI diagnosis, Policy decision, and Audit trail.
    """
    if case_id not in _CASES_CACHE:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found.")
    
    c = _CASES_CACHE[case_id]
    
    dossier = {
        "dossier_id": f"dos_{case_id}",
        "case_id": case_id,
        "timestamp": c.get("created_at"),
        "leak_source": c.get("leak_source"),
        "customer": {
            "id": c.get("customer_id"),
            "ltv_inr": c.get("customer_ltv", 0.0),
            "contact_history_7d": c.get("contact_history_count", 1)
        },
        "ml_scoring": {
            "model_version": "v1.2.0-xgboost-calibrated",
            "p_recovery": c.get("p_recovery", 0.75),
            "calibration_brier_score": 0.042
        },
        "ai_reasoning": {
            "llm_model": "claude-3-5-sonnet",
            "diagnosis": c.get("diagnosis", "Transaction failure evaluated."),
            "recommended_action": c.get("recommended_action", "RETRY_PAYMENT")
        },
        "policy_governance": {
            "policy_version": c.get("policy_version", "v1.0.0"),
            "decision": c.get("decision"),
            "reason_code": c.get("reason_code"),
            "policy_token": c.get("policy_token")
        },
        "audit_events": [
            {
                "event_type": "LEAK_DETECTED",
                "timestamp": c.get("created_at"),
                "details": f"Leak detected from {c.get('leak_source')}."
            },
            {
                "event_type": "POLICY_EVALUATED",
                "timestamp": c.get("created_at"),
                "details": f"Decision: {c.get('decision')} (Reason: {c.get('reason_code')})."
            }
        ]
    }
    
    return dossier
