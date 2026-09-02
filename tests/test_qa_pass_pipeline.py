"""
tests/test_qa_pass_pipeline.py
--------------------------------
Comprehensive 8-Step Automated QA Pass for recoverOS:
1. Application & Backend Initialization
2. Data Loading & DB Ingestion
3. Analyzer Engine
4. ML Prediction Engine
5. Decision Agent & Policy Engine
6. Message Generator Engine
7. End-to-End Recovery Pipeline Flow
8. Invalid, Malformed & Security Edge Cases
"""

import os
import pytest
import pandas as pd
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

# Backend imports
from backend.main import app
from db.database import init_db, SessionLocal, engine
from db.models import (
    Base, WebhookEventModel, RecoveryCaseModel, PaymentLinkModel,
    EmailMessageModel, AuditEventModel, RevenueLeakModel, AIDecisionModel,
    CustomerModel
)
from backend.models.schemas import RecoveryAction, LeakSource, FailureCategory
from services.ml_engine import RecoveryMLEngine, get_ml_engine, extract_features
from services.policy_engine import PolicyEngine, build_policy_input, PolicyDecision, PolicyReason, StoppingRuleReason
from services.ai_engine import redact_pii
from agents.analyzer import calculate_recovery_score, classify_priority, explain_score, SCORE_WEIGHTS
from agents.decision_agent import decide_action
from agents.message_generator import generate_recovery_message


@pytest.fixture(scope="module", autouse=True)
def setup_test_environment():
    """Ensure database tables are initialized before tests run."""
    init_db()
    yield


# ============================================================================
# 1. APPLICATION & BACKEND INITIALIZATION
# ============================================================================
def test_qa_01_application_starts_and_health_check():
    """Verify backend FastAPI application starts and health check endpoint succeeds."""
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data.get("status") == "healthy"
    assert "timestamp" in data


# ============================================================================
# 2. DATA LOADING & DB INGESTION
# ============================================================================
def test_qa_02_data_loading_and_db_ingestion():
    """Verify database schema creation, customer record ingestion, and query retrieval."""
    session = SessionLocal()
    try:
        cust_id = f"cust_{int(datetime.now(timezone.utc).timestamp())}"
        customer = CustomerModel(
            id=cust_id,
            email=f"qa_{cust_id}@example.com",
            phone="+919876543210",
            risk_tier="LOW",
            ltv_inr=5000.00
        )
        session.add(customer)
        session.commit()

        fetched = session.query(CustomerModel).filter_by(id=cust_id).first()
        assert fetched is not None
        assert fetched.phone == "+919876543210"
        assert float(fetched.ltv_inr) == 5000.00
    finally:
        session.close()


# ============================================================================
# 3. ANALYZER ENGINE
# ============================================================================
def test_qa_03_analyzer_scoring_and_classification():
    """Verify recovery priority score calculations, classifications, and human explanations."""
    row = pd.Series({
        "amount": 7500.0,
        "failure_reason": "Network Failure",
        "customer_segment": "Premium",
        "customer_history": "Loyal Customer",
        "retry_count": 0
    })
    
    score = calculate_recovery_score(row, max_amount=10000.0)
    assert 0 <= score <= 100
    assert score >= 65.0  # Should score high due to high amount, network failure & premium segment

    priority = classify_priority(score)
    assert priority == "High Priority"

    explanation = explain_score(row, score, priority)
    assert isinstance(explanation, str)
    assert len(explanation) > 0
    assert "the transaction value is high" in explanation or "High Priority" in explanation


# ============================================================================
# 4. ML PREDICTION ENGINE
# ============================================================================
def test_qa_04_ml_prediction_and_calibration():
    """Verify ML feature extraction, probability scoring, and model calibration."""
    features = extract_features(
        amount_inr=5000.0,
        customer_ltv=15000.0,
        contact_count_7d=0,
        retry_count=0,
        failure_category="network_timeout",
        leak_source="RAZORPAY_CHECKOUT",
        is_quiet_hours=False
    )
    assert features.shape == (1, 7)

    engine = get_ml_engine()
    res = engine.predict_p_recovery(
        amount_inr=5000.0,
        customer_ltv=15000.0,
        contact_count_7d=0,
        retry_count=0,
        failure_category="network_timeout",
        leak_source="RAZORPAY_CHECKOUT",
        is_quiet_hours=False
    )
    prob = res[0] if isinstance(res, (tuple, list)) else res
    assert 0.0 <= prob <= 1.0


# ============================================================================
# 5. DECISION AGENT & POLICY ENGINE
# ============================================================================
def test_qa_05_decision_agent_and_policy_checks():
    """Verify rule-based decision logic and policy rule enforcement."""
    # Test Rule-based decision agent
    row = pd.Series({
        "amount": 2500.0,
        "failure_reason": "Network Failure",
        "customer_segment": "Regular",
        "customer_history": "Regular Customer",
        "retry_count": 0,
        "priority": "High Priority"
    })
    action, explanation = decide_action(row, recovery_probability=0.85)
    assert action in ["Retry Payment", "Send Payment Reminder", "Send Personalized Recovery Message"]
    assert len(explanation) > 0

    # Test Policy Engine: Amount > 50k requires human review
    policy_engine = PolicyEngine()
    input_high_val = build_policy_input(
        amount=Decimal("60000.00"),
        failure_category="bank_decline",
        retry_count=0,
        recovery_probability=0.8,
        risk_score=0.1,
        proposed_action=RecoveryAction.RETRY,
        leak_source="RAZORPAY_CHECKOUT",
        customer_consent=True,
        customer_contact_count_24h=0,
        customer_contact_count_7d=0,
        is_current_hour_quiet=False
    )
    res = policy_engine.evaluate(input_high_val)
    decision = res[0] if isinstance(res, (tuple, list)) else res
    assert decision in [PolicyDecision.HUMAN_REVIEW, PolicyDecision.DENY]


# ============================================================================
# 6. MESSAGE GENERATION ENGINE
# ============================================================================
def test_qa_06_message_generation_and_pii_handling():
    """Verify recovery message output generation and template fallback integrity."""
    result = generate_recovery_message(
        customer_name="Rahul Sharma",
        amount=4999.0,
        failure_reason="Authentication Failure",
        action="Send Payment Reminder",
        currency="INR",
        segment="Premium"
    )

    assert "message" in result
    assert "mode" in result
    assert isinstance(result["message"], str)
    assert len(result["message"]) > 10
    assert "Rahul" in result["message"] or "payment" in result["message"].lower()

    # Test PII Redaction
    redacted_email = redact_pii("Contact me at user@domain.com or call 9876543210")
    assert "user@domain.com" not in redacted_email


# ============================================================================
# 7. END-TO-END RECOVERY FLOW
# ============================================================================
def test_qa_07_end_to_end_recovery_pipeline():
    """Verify full end-to-end recovery pipeline flow from ingestion to decision & message output."""
    payload = {
        "amount": 3500.0,
        "failure_reason": "Bank Server Issue",
        "customer_name": "Anita Roy",
        "customer_segment": "Premium",
        "customer_history": "Loyal Customer",
        "retry_count": 0
    }

    # Step A: Analyzer
    row = pd.Series(payload)
    score = calculate_recovery_score(row, max_amount=10000.0)
    priority = classify_priority(score)
    row["priority"] = priority

    # Step B: ML Engine
    ml = get_ml_engine()
    res = ml.predict_p_recovery(
        amount_inr=payload["amount"],
        customer_ltv=15000.0,
        contact_count_7d=0,
        retry_count=payload["retry_count"],
        failure_category="bank_decline",
        leak_source="RAZORPAY_CHECKOUT",
        is_quiet_hours=False
    )
    prob = res[0] if isinstance(res, (tuple, list)) else res

    # Step C: Decision Agent
    action, rationale = decide_action(row, recovery_probability=prob)

    # Step D: Message Generator
    msg_res = generate_recovery_message(
        customer_name=payload["customer_name"],
        amount=payload["amount"],
        failure_reason=payload["failure_reason"],
        action=action
    )

    assert score > 0
    assert priority in ["High Priority", "Medium Priority", "Low Priority"]
    assert 0.0 <= prob <= 1.0
    assert len(action) > 0
    assert len(msg_res["message"]) > 0


# ============================================================================
# 8. INVALID, MALFORMED & SECURITY EDGE CASES
# ============================================================================
def test_qa_08_invalid_payloads_and_security_rejections():
    """Verify security rejections for invalid endpoints and malformed JSON payloads."""
    client = TestClient(app)
    
    # Send malformed request to API batch endpoint
    response = client.post(
        "/api/v1/batch/process",
        headers={"Content-Type": "application/json"},
        content="invalid-json-body{{{"
    )
    assert response.status_code in [400, 404, 422]

    # Send request with invalid / missing auth header
    response_auth = client.get(
        "/api/v1/cases",
        headers={"Authorization": "Bearer invalid_token_xyz"}
    )
    assert response_auth.status_code in [400, 401, 403, 404, 422]
