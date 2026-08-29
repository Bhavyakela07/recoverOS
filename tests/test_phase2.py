"""
RecoverOS Phase 2 Automated QA Test Suite
Verifies Calibrated ML Engine, Claude AI Structured Reasoning, PII Masking, and Fallbacks.
"""

import pytest
import os
import sys

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from services.ml_engine import RecoveryMLEngine, get_ml_engine, extract_features
from services.ai_engine import redact_pii, ClaudeAIEngine, get_ai_engine
try:
    from backend.models.schemas import AIRecommendation
except ImportError:
    from models.schemas import AIRecommendation


def test_pii_redaction():
    """Verify email, phone, and card numbers are cleanly redacted before sending to LLM."""
    raw_text = "Customer email rahul.sharma@gmail.com phone +919876543210 card 4111-2222-3333-4444 failed transaction."
    redacted = redact_pii(raw_text)

    assert "rahul.sharma@gmail.com" not in redacted
    assert "user_***@domain.com" in redacted
    assert "+919876543210" not in redacted
    assert "+91-XXXXXX1234" in redacted
    assert "4111-2222-3333-4444" not in redacted
    assert "XXXX-XXXX-XXXX-4321" in redacted
    print("[QA TEST PASS] PII Redaction masks email, phone, and card digits cleanly.")


def test_ml_model_calibration_and_prediction():
    """Verify ML Engine predictions are within valid probability bounds (0.05 <= p <= 0.95)."""
    ml_engine = RecoveryMLEngine(seed=42)
    
    # Test network timeout (high probability failure)
    p_high, brier_1 = ml_engine.predict_p_recovery(
        amount_inr=1500.0,
        customer_ltv=25000.0,
        contact_count_7d=0,
        retry_count=0,
        failure_category="network_timeout",
        leak_source="payment_failed",
        is_quiet_hours=False
    )
    
    assert 0.05 <= p_high <= 0.95
    assert brier_1 <= 0.08
    
    # Test frequent contacts during quiet hours (low probability)
    p_low, brier_2 = ml_engine.predict_p_recovery(
        amount_inr=45000.0,
        customer_ltv=1000.0,
        contact_count_7d=4,
        retry_count=2,
        failure_category="insufficient_funds",
        leak_source="payment_failed",
        is_quiet_hours=True
    )
    
    assert 0.05 <= p_low <= 0.95
    assert p_high > p_low, "Technical transient failure should have higher p_recovery than frequent contact quiet hours failure"
    print(f"[QA TEST PASS] Calibrated ML Engine probability predictions: High={p_high}, Low={p_low}")


def test_ai_reasoning_and_fallback():
    """Verify AI Engine generates valid structured output recommendations."""
    ai_engine = ClaudeAIEngine()
    
    rec = ai_engine.generate_recommendation(
        leak_id="leak_test_101",
        amount_inr=2499.0,
        failure_category="network_timeout",
        leak_source="payment_failed",
        customer_email="test.user@razorpay.com",
        customer_name="Aarav",
        customer_ltv=15000.0,
        p_recovery=0.82
    )

    assert isinstance(rec, AIRecommendation)
    assert rec.leak_diagnosis is not None
    assert rec.recommended_action in ["retry", "reminder", "incentive", "follow_up", "escalate", "none"]
    assert rec.confidence > 0.0
    assert rec.customer_message_draft is not None
    assert rec.message_language == "hinglish"
    print("[QA TEST PASS] AI Reasoning Engine produces grounded, schema-validated output.")


if __name__ == "__main__":
    pytest.main(["-v", __file__])
