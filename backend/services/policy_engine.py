"""
Deterministic Policy Engine + Stopping Rules for RecoverOS.

CRITICAL: These are PURE functions with NO I/O, NO network calls, NO LLM.
They are versioned, unit-tested, and the policy_version is recorded on every decision.
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum
from decimal import Decimal

def is_ist_quiet_hours() -> bool:
    """Evaluates whether current time in India Standard Time (IST UTC+5:30) is within quiet hours (22:00 to 08:00)."""
    ist_tz = timezone(timedelta(hours=5, minutes=30))
    now_ist = datetime.now(ist_tz)
    hour = now_ist.hour
    return hour >= 22 or hour < 8

def calculate_priority_score(
    amount: float,
    failure_category: str = "network_timeout",
    customer_segment: str = "Regular",
    customer_ltv: float = 15000.0,
    retry_count: int = 0
) -> Tuple[int, str]:
    """
    Calculates transparent Priority Recovery Score (0-100) and Priority Tier (HIGH, MEDIUM, LOW)
    using the 5-factor weighted formula:
      1. Transaction Amount (40% weight)
      2. Failure Reason Recoverability (25% weight)
      3. Customer Segment (15% weight)
      4. Customer History / LTV (10% weight)
      5. Retry Count (10% weight)
    Buckets:
      High Priority >= 65
      Medium Priority 40-64
      Low Priority < 40
    """
    # Factor 1: Transaction Amount (40%)
    amount_score = min(1.0, max(0.0, amount / 50000.0)) * 40.0

    # Factor 2: Failure Reason Recoverability (25%)
    reason_map = {
        "network_timeout": 0.90,
        "abandonment": 0.80,
        "expired_card": 0.60,
        "insufficient_funds": 0.50,
        "issuer_decline": 0.40
    }
    recoverability = reason_map.get(failure_category, 0.50)
    reason_score = recoverability * 25.0

    # Factor 3: Customer Segment (15%)
    segment_map = {
        "Premium": 1.00,
        "Regular": 0.65,
        "New": 0.35
    }
    segment_score = segment_map.get(customer_segment, 0.65) * 15.0

    # Factor 4: Customer History / LTV (10%)
    if customer_ltv >= 50000:
        history_mult = 1.00
    elif customer_ltv >= 20000:
        history_mult = 0.75
    elif customer_ltv >= 5000:
        history_mult = 0.45
    else:
        history_mult = 0.20
    history_score = history_mult * 10.0

    # Factor 5: Retry Count (10%)
    if retry_count == 0:
        retry_mult = 1.00
    elif retry_count == 1:
        retry_mult = 0.70
    elif retry_count == 2:
        retry_mult = 0.40
    else:
        retry_mult = 0.20
    retry_score = retry_mult * 10.0

    total = amount_score + reason_score + segment_score + history_score + retry_score
    final_score = int(min(max(round(total), 0), 100))

    if final_score >= 65:
        tier = "HIGH"
    elif final_score >= 40:
        tier = "MEDIUM"
    else:
        tier = "LOW"

    return final_score, tier

try:
    from backend.models.schemas import (
        PolicyDecision, PolicyReason, StoppingRuleReason,
        RecoveryAction, LeakSource, FailureCategory
    )
except ImportError:
    from models.schemas import (
        PolicyDecision, PolicyReason, StoppingRuleReason,
        RecoveryAction, LeakSource, FailureCategory
    )


# =============================================================================
# POLICY CONFIGURATION (versioned)
# =============================================================================

POLICY_VERSION = "v1.0.0"

# Policy configuration - these are merchant-configurable thresholds
POLICY_CONFIG = {
    "min_recovery_probability": 0.15,
    "max_risk_score": 0.85,
    "max_retry_count": 3,
    "max_amount_limit": Decimal("50000"),
    "min_expected_net_recovery": Decimal("10.0"),
    "allowed_actions": [a.value for a in RecoveryAction],
    "quiet_hours_start": 21,  # 9 PM
    "quiet_hours_end": 8,     # 8 AM
    "max_contacts_per_day": 3,
    "max_contacts_per_week": 10,
    "cooldown_minutes": 60,
    "action_budget_per_run": 1000,
    "require_consent": True,
    "mandate_limits": {
        "max_recurring_retries": 3,
        "max_amount_per_mandate": Decimal("15000")
    }
}


# =============================================================================
# POLICY ENGINE
# =============================================================================

@dataclass(frozen=True)
class PolicyInput:
    """Immutable input to policy engine."""
    recovery_probability: float
    risk_score: float
    amount: Decimal
    retry_count: int
    proposed_action: RecoveryAction
    leak_source: LeakSource
    failure_category: FailureCategory
    customer_consent: bool
    customer_contact_count_24h: int
    customer_contact_count_7d: int
    is_current_hour_quiet: bool
    mandate_count: int = 0
    mandate_amount: Decimal = Decimal("0")
    global_action_count_this_run: int = 0


def evaluate_policy(inp: PolicyInput) -> Tuple[PolicyDecision, PolicyReason, Dict[str, Any]]:
    """
    Pure policy evaluation - deterministic, no I/O.
    Returns (decision, reason, details_dict)
    """

    details = {}
    config = POLICY_CONFIG

    # 1. Stopping rule checks first (SUPPRESS is terminal)
    stop_decision = evaluate_stopping_rules(inp)
    if stop_decision.stop:
        details["stopping_rule"] = stop_decision.rule.value
        details["stopping_explanation"] = stop_decision.explanation
        return PolicyDecision.SUPPRESS, PolicyReason.STOPPING_RULE, details

    # 2. Consent check
    if config["require_consent"] and not inp.customer_consent:
        return PolicyDecision.DENY, PolicyReason.NO_CONSENT, {"reason": "customer_opt_out"}

    # 3. Action permitted for merchant
    if inp.proposed_action.value not in config["allowed_actions"]:
        return PolicyDecision.DENY, PolicyReason.ACTION_NOT_PERMITTED, {"action": inp.proposed_action.value}

    # 4. Amount limit
    if inp.amount > config["max_amount_limit"]:
        return PolicyDecision.HUMAN_REVIEW, PolicyReason.AMOUNT_OVER_LIMIT, {"amount": str(inp.amount), "limit": str(config["max_amount_limit"])}

    # 5. Recovery probability threshold
    if inp.recovery_probability < config["min_recovery_probability"]:
        return PolicyDecision.DENY, PolicyReason.LOW_PROBABILITY, {"probability": inp.recovery_probability, "threshold": config["min_recovery_probability"]}

    # 6. Risk score ceiling
    if inp.risk_score > config["max_risk_score"]:
        return PolicyDecision.DENY, PolicyReason.LOW_PROBABILITY, {"risk_score": inp.risk_score, "threshold": config["max_risk_score"]}

    # 7. Retry count limit
    if inp.retry_count >= config["max_retry_count"]:
        return PolicyDecision.HUMAN_REVIEW, PolicyReason.RETRIES_EXHAUSTED, {"retry_count": inp.retry_count, "max": config["max_retry_count"]}

    # 8. Contact caps
    if inp.customer_contact_count_24h >= config["max_contacts_per_day"]:
        return PolicyDecision.DENY, PolicyReason.CONTACT_CAP_REACHED, {"window": "24h", "count": inp.customer_contact_count_24h, "max": config["max_contacts_per_day"]}

    if inp.customer_contact_count_7d >= config["max_contacts_per_week"]:
        return PolicyDecision.DENY, PolicyReason.CONTACT_CAP_REACHED, {"window": "7d", "count": inp.customer_contact_count_7d, "max": config["max_contacts_per_week"]}

    # 9. Quiet hours
    if inp.is_current_hour_quiet:
        return PolicyDecision.DENY, PolicyReason.OUTSIDE_QUIET_HOURS, {"hour": inp.is_current_hour_quiet}

    # 10. Mandate limits (for subscription failures)
    if inp.leak_source == LeakSource.SUBSCRIPTION_FAILURE:
        if inp.mandate_count >= config["mandate_limits"]["max_recurring_retries"]:
            return PolicyDecision.DENY, PolicyReason.MANDATE_LIMIT_EXCEEDED, {"mandate_count": inp.mandate_count}
        if inp.mandate_amount > config["mandate_limits"]["max_amount_per_mandate"]:
            return PolicyDecision.HUMAN_REVIEW, PolicyReason.MANDATE_LIMIT_EXCEEDED, {"mandate_amount": str(inp.mandate_amount)}

    # 11. Action budget (blast radius limit)
    if inp.global_action_count_this_run >= config["action_budget_per_run"]:
        return PolicyDecision.DENY, PolicyReason.ACTION_NOT_PERMITTED, {"action_budget_exceeded": config["action_budget_per_run"]}

    # All checks passed
    return PolicyDecision.ALLOW, PolicyReason.ACTION_NOT_PERMITTED, {"checks": "all_passed"}


# =============================================================================
# STOPPING RULES (First-class module - named, versioned, tested)
# =============================================================================

@dataclass(frozen=True)
class StopDecision:
    stop: bool
    rule: Optional[StoppingRuleReason]
    explanation: str


def evaluate_stopping_rules(inp: PolicyInput) -> StopDecision:
    """
    Pure stopping rules evaluation - NO I/O.
    Returns StopDecision with rule name and explanation.
    """

    config = POLICY_CONFIG

    # 1. Max retries per leak
    if inp.retry_count >= config["max_retry_count"]:
        return StopDecision(
            stop=True,
            rule=StoppingRuleReason.MAX_RETRIES,
            explanation=f"Retry count {inp.retry_count} >= max {config['max_retry_count']}"
        )

    # 2. Contact caps
    if inp.customer_contact_count_24h >= config["max_contacts_per_day"]:
        return StopDecision(
            stop=True,
            rule=StoppingRuleReason.CONTACT_CAP,
            explanation=f"24h contact cap reached: {inp.customer_contact_count_24h}/{config['max_contacts_per_day']}"
        )

    if inp.customer_contact_count_7d >= config["max_contacts_per_week"]:
        return StopDecision(
            stop=True,
            rule=StoppingRuleReason.CONTACT_CAP,
            explanation=f"7d contact cap reached: {inp.customer_contact_count_7d}/{config['max_contacts_per_week']}"
        )

    # 3. Quiet hours
    if inp.is_current_hour_quiet:
        return StopDecision(
            stop=True,
            rule=StoppingRuleReason.QUIET_HOURS,
            explanation=f"Current hour is within quiet hours ({config['quiet_hours_start']}:00-{config['quiet_hours_end']}:00)"
        )

    # 4. Minimum expected net recovery (economic suppression)
    # Note: Expected net recovery should be passed via context
    # This is checked in strategy simulator + policy combined

    # 5. Minimum recovery probability (hopeless case)
    if inp.recovery_probability < config["min_recovery_probability"]:
        return StopDecision(
            stop=True,
            rule=StoppingRuleReason.MIN_PROBABILITY,
            explanation=f"Recovery probability {inp.recovery_probability:.2%} below threshold {config['min_recovery_probability']:.0%}"
        )

    # 6. Hard stop on opt-out / consent withdrawal
    if not inp.customer_consent:
        return StopDecision(
            stop=True,
            rule=StoppingRuleReason.OPT_OUT,
            explanation="Customer has withdrawn consent / opted out"
        )

    # 7. Fraud signal (from risk score)
    if inp.risk_score >= config["max_risk_score"]:
        return StopDecision(
            stop=True,
            rule=StoppingRuleReason.FRAUD_SIGNAL,
            explanation=f"Risk score {inp.risk_score:.2%} indicates potential fraud"
        )

    # 8. Cool-down period
    # This would check last_contact_time in real impl - stubbed for now
    # if time_since_last_contact < config["cooldown_minutes"]:
    #     return StopDecision(True, StoppingRuleReason.COOLDOWN, f"Cooldown not elapsed")

    # 9. Global action budget
    if inp.global_action_count_this_run >= config["action_budget_per_run"]:
        return StopDecision(
            stop=True,
            rule=StoppingRuleReason.ACTION_BUDGET,
            explanation=f"Global action budget exceeded: {inp.global_action_count_this_run}/{config['action_budget_per_run']}"
        )

    # No stopping rule triggered
    return StopDecision(stop=False, rule=None, explanation="No stopping rules triggered")


# =============================================================================
# POLICY ENGINE CLASS (for dependency injection)
# =============================================================================

class PolicyEngine:
    """Stateless policy engine - pure logic, versioned."""

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or POLICY_CONFIG
        self.version = POLICY_VERSION

    def evaluate(self, inp: PolicyInput) -> Tuple[PolicyDecision, PolicyReason, Dict[str, Any]]:
        """Evaluate policy with current config."""
        return evaluate_policy(inp)

    def check_stopping_rules(self, inp: PolicyInput) -> StopDecision:
        """Check stopping rules with current config."""
        return evaluate_stopping_rules(inp)


# =============================================================================
# HELPER: Build PolicyInput from context
# =============================================================================

def build_policy_input(
    *,
    recovery_probability: float,
    risk_score: float,
    amount: Decimal,
    retry_count: int,
    proposed_action: RecoveryAction,
    leak_source: LeakSource,
    failure_category: FailureCategory,
    customer_consent: bool,
    customer_contact_count_24h: int,
    customer_contact_count_7d: int,
    is_current_hour_quiet: bool,
    mandate_count: int = 0,
    mandate_amount: Decimal = Decimal("0"),
    global_action_count_this_run: int = 0
) -> PolicyInput:
    """Helper to construct PolicyInput from scattered context."""
    return PolicyInput(
        recovery_probability=recovery_probability,
        risk_score=risk_score,
        amount=amount,
        retry_count=retry_count,
        proposed_action=proposed_action,
        leak_source=leak_source,
        failure_category=failure_category,
        customer_consent=customer_consent,
        customer_contact_count_24h=customer_contact_count_24h,
        customer_contact_count_7d=customer_contact_count_7d,
        is_current_hour_quiet=is_current_hour_quiet,
        mandate_count=mandate_count,
        mandate_amount=mandate_amount,
        global_action_count_this_run=global_action_count_this_run
    )