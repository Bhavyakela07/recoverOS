"""
RecoverOS Claude AI Structured Reasoning Engine
Handles PII Redaction, Anthropic Claude 3.5 Sonnet structured JSON recommendations,
Hinglish customer outreach message drafting, and deterministic fallback reasoning.
"""

import os
import re
import json
import logging
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

try:
    from backend.models.schemas import AIRecommendation, RecoveryAction
except ImportError:
    from models.schemas import AIRecommendation, RecoveryAction

logger = logging.getLogger("recoveros.ai_engine")

# Try importing Anthropic SDK
try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False
    logger.info("anthropic SDK not installed. Using structured fallback reasoning engine.")


# =============================================================================
# PII MASKING / REDACTION UTILITY
# =============================================================================

def redact_pii(text: str) -> str:
    """Masks email addresses, phone numbers, and card numbers before sending to LLM."""
    if not text:
        return text

    # Redact Emails
    text = re.sub(
        r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+',
        r'user_***@domain.com',
        text
    )

    # Redact Indian Phone Numbers (+91-XXXXXXXXXX or 10 digit)
    text = re.sub(
        r'(\+91[\-\s]?)?[6789]\d{9}',
        r'+91-XXXXXX1234',
        text
    )

    # Redact Card Numbers (16 digits or 4x4 format)
    text = re.sub(
        r'\b(?:\d[ -]*?){13,16}\b',
        r'XXXX-XXXX-XXXX-4321',
        text
    )

    return text


# =============================================================================
# CLAUDE AI REASONING ENGINE
# =============================================================================

class ClaudeAIEngine:
    """Claude 3.5 Sonnet Structured Reasoning Engine with fallback."""

    def __init__(self):
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self.client = None
        
        if HAS_ANTHROPIC and self.api_key:
            try:
                self.client = anthropic.Anthropic(api_key=self.api_key)
                logger.info("Initialized Anthropic Claude client for structured reasoning.")
            except Exception as err:
                logger.warning(f"Could not initialize Anthropic client ({err}). Using fallback.")

    def generate_recommendation(
        self,
        leak_id: str,
        amount_inr: float,
        failure_category: str,
        leak_source: str,
        customer_email: str = "customer@example.com",
        customer_name: str = "Valued Customer",
        customer_ltv: float = 5000.0,
        p_recovery: float = 0.75
    ) -> AIRecommendation:
        """
        Generates structured AI diagnosis and recommended recovery strategy.
        Pulls Claude LLM structured JSON output if API key is valid, else uses structured fallback.
        """
        # Redact PII for safety
        safe_email = redact_pii(customer_email)

        if self.client:
            try:
                prompt = f"""You are RecoverOS, an elite AI Revenue Recovery Decision Engine for Razorpay merchants.
Analyze the following payment leak event and recommend the optimal governed recovery strategy.

Leak Details:
- ID: {leak_id}
- Amount: ₹{amount_inr:,.2f}
- Source: {leak_source}
- Failure Category: {failure_category}
- Customer LTV: ₹{customer_ltv:,.2f}
- Calibrated ML Recovery Prob (p_recovery): {p_recovery:.2%}
- Customer Email: {safe_email}

Respond ONLY with valid JSON matching this exact structure:
{{
  "diagnosis": "Short technical & behavioral root cause diagnosis",
  "recommended_action": "retry" | "reminder" | "incentive" | "follow_up" | "escalate" | "none",
  "rationale": "Clear reasoning why this action maximizes net recovery without spamming",
  "draft_message": {{
    "language": "Hinglish",
    "channel": "WhatsApp",
    "text": "Polite, high-converting customer outreach message including deep-link placeholder"
  }},
  "confidence_score": 0.95
}}"""

                response = self.client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=500,
                    temperature=0.2,
                    system="You are a precise revenue recovery AI. Output JSON strictly.",
                    messages=[{"role": "user", "content": prompt}]
                )

                content_text = response.content[0].text
                parsed_json = json.loads(content_text)

                from models.schemas import FailureCategory, RecoveryAction, ReasonCode

                act_str = parsed_json.get("recommended_action", "retry").lower()
                act_enum = RecoveryAction.RETRY if act_str == "retry" else (RecoveryAction.REMINDER if act_str == "reminder" else RecoveryAction.ESCALATE)

                return AIRecommendation(
                    leak_diagnosis=parsed_json.get("diagnosis", "Payment failure analyzed."),
                    failure_category=FailureCategory.NETWORK_TIMEOUT if failure_category == "network_timeout" else FailureCategory.ABANDONMENT,
                    recommended_action=act_enum,
                    confidence=float(parsed_json.get("confidence_score", 0.92)),
                    reason_codes=[ReasonCode.TRANSIENT_ERROR_FAST_RETRY],
                    evidence=[{"p_recovery": p_recovery, "rationale": parsed_json.get("rationale", "")}],
                    customer_message_draft=parsed_json.get("draft_message", {}).get("text", "Payment update"),
                    message_language="hinglish",
                    requires_human_review=(act_enum == RecoveryAction.ESCALATE)
                )
            except Exception as err:
                logger.warning(f"Claude API call failed ({err}). Using fallback engine.")

        # Structured Fallback Reasoning Engine
        return self._generate_fallback_recommendation(
            leak_id, amount_inr, failure_category, leak_source, customer_name, customer_ltv, p_recovery
        )

    def _generate_fallback_recommendation(
        self,
        leak_id: str,
        amount_inr: float,
        failure_category: str,
        leak_source: str,
        customer_name: str,
        customer_ltv: float,
        p_recovery: float
    ) -> AIRecommendation:
        """Deterministic, grounded fallback reasoning generator."""
        if leak_source == "subscription_failure":
            diagnosis = "Recurring mandate debit failure on active subscription."
            action = "retry"
            rationale = f"Mandate retry sequencer scheduled for optimal salary cycle (recovery prob: {p_recovery:.0%})."
            hinglish_msg = f"Hi {customer_name}! Your auto-renewal for subscription of ₹{amount_inr:,.2f} could not complete. Tap to update payment method: https://rzp.io/i/sub"
        elif leak_source == "overdue_receivable":
            diagnosis = "B2B invoice past due date (Overdue Receivables)."
            action = "follow_up"
            rationale = "B2B Receivables Chaser with automated Promise-to-Pay tracking link."
            hinglish_msg = f"Hello {customer_name}, invoice #INV-{leak_id[:6]} for ₹{amount_inr:,.2f} is overdue. Click here to settle or log a Promise-to-Pay date: https://rzp.io/i/invoice"
            hinglish_msg = f"Hi {customer_name}! Your payment of ₹{amount_inr:,.2f} paused due to a quick bank server hiccup. Tap here to complete securely using your 1-click Razorpay payment link."
        elif leak_source == "checkout_abandonment":
            diagnosis = "Checkout session abandoned prior to payment authorization."
            action = "reminder"
            rationale = "Customer left items in checkout. Friendly WhatsApp reminder with 1-click cart restore."
            hinglish_msg = f"Hey {customer_name}! You left items in your cart (₹{amount_inr:,.2f}). Complete your order in 30 seconds here: https://rzp.io/i/cart"
        elif amount_inr > 50000:
            diagnosis = "High-value transaction failure requiring white-glove support."
            action = "escalate"
            rationale = f"High-value order (₹{amount_inr:,.2f}) flagged for human review to prevent order cancellation."
            hinglish_msg = f"Hello {customer_name}, our support specialist is reaching out to assist with your order payment."
        else:
            diagnosis = f"Payment failure ({failure_category}) flagged for automated outreach."
            action = "retry"
            rationale = "Standard recovery path evaluated."
            hinglish_msg = f"Hi {customer_name}! We noticed an issue with your payment of ₹{amount_inr:,.2f}. Click here to retry: https://rzp.io/i/pay"

        try:
            from backend.models.schemas import FailureCategory, RecoveryAction, ReasonCode
        except ImportError:
            from models.schemas import FailureCategory, RecoveryAction, ReasonCode

        cat_enum = FailureCategory.NETWORK_TIMEOUT if failure_category == "network_timeout" else FailureCategory.ABANDONMENT
        act_enum = RecoveryAction.RETRY if action == "retry" else (RecoveryAction.REMINDER if action == "reminder" else RecoveryAction.ESCALATE)

        return AIRecommendation(
            leak_diagnosis=diagnosis,
            failure_category=cat_enum,
            recommended_action=act_enum,
            confidence=0.90,
            reason_codes=[ReasonCode.TRANSIENT_ERROR_FAST_RETRY if failure_category == "network_timeout" else ReasonCode.ABANDONMENT_SEND_LINK],
            evidence=[{"p_recovery": p_recovery, "rationale": rationale}],
            customer_message_draft=hinglish_msg,
            message_language="hinglish",
            requires_human_review=(action == "escalate")
        )


# Global singleton instance
_ai_engine = ClaudeAIEngine()


def get_ai_engine() -> ClaudeAIEngine:
    return _ai_engine
