"""
Health Check API Router — RecoverOS
"""

from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from db.database import get_db, engine
from services.policy_engine import POLICY_VERSION

router = APIRouter(tags=["Health"])


@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    """System health check and database connectivity diagnostic."""
    db_status = "healthy"
    try:
        db.execute(text("SELECT 1"))
    except Exception as err:
        db_status = f"unhealthy: {str(err)}"

    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "database": db_status,
        "database_engine": engine.dialect.name,
        "services": {
            "detector": "pluggable (payment.failed, checkout_abandonment)",
            "prediction": "calibrated XGBoost (p_recovery)",
            "ai": "Claude 3.5 Sonnet (structured reasoning)",
            "strategy": "argmax Expected Net Recovery",
            "razorpay": "governed test-mode gateway",
            "policy": "REAL (deterministic v1.0.0)",
            "tools": "governed + idempotent"
        },
        "policy_version": POLICY_VERSION,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
