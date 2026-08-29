"""
Pydantic schemas for RecoverOS - all domain models in one place.
These are the single source of truth for API contracts and DB serialization.
"""

from enum import Enum
from typing import Optional, List, Literal
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from decimal import Decimal


# =============================================================================
# ENUMS (vocabulary discipline - use track's exact words)
# =============================================================================

class LeakSource(str, Enum):
    """Revenue leak sources - exactly the four from the track."""
    PAYMENT_FAILURE = "payment_failure"
    CHECKOUT_ABANDONMENT = "checkout_abandonment"
    SUBSCRIPTION_FAILURE = "subscription_failure"
    OVERDUE_RECEIVABLE = "overdue_receivable"


class FailureCategory(str, Enum):
    """Payment failure categories for strategy hints."""
    INSUFFICIENT_FUNDS = "insufficient_funds"
    ISSUER_DECLINE = "issuer_decline"
    EXPIRED_CARD = "expired_card"
    NETWORK_TIMEOUT = "network_timeout"
    ABANDONMENT = "abandonment"
    FRAUD_SIGNAL = "fraud_signal"
    UNKNOWN = "unknown"


class RecoveryAction(str, Enum):
    """Possible recovery interventions."""
    RETRY = "retry"
    REMINDER = "reminder"
    INCENTIVE = "incentive"
    FOLLOW_UP = "follow_up"
    ESCALATE = "escalate"
    NONE = "none"


class PolicyDecision(str, Enum):
    """Policy engine outcomes."""
    ALLOW = "allow"
    DENY = "deny"
    HUMAN_REVIEW = "human_review"
    SUPPRESS = "suppress"


class PolicyReason(str, Enum):
    """Machine-readable policy decision reasons."""
    AMOUNT_OVER_LIMIT = "amount_over_limit"
    RETRIES_EXHAUSTED = "retries_exhausted"
    LOW_PROBABILITY = "low_probability"
    NO_CONSENT = "no_consent"
    CONTACT_CAP_REACHED = "contact_cap_reached"
    MANDATE_LIMIT_EXCEEDED = "mandate_limit_exceeded"
    OUTSIDE_QUIET_HOURS = "outside_quiet_hours"
    ACTION_NOT_PERMITTED = "action_not_permitted"
    STOPPING_RULE = "stopping_rule"


class StoppingRuleReason(str, Enum):
    """Stopping rule triggers."""
    MAX_RETRIES = "max_retries"
    CONTACT_CAP = "contact_cap"
    QUIET_HOURS = "quiet_hours"
    MIN_NET_RECOVERY = "min_net_recovery"
    MIN_PROBABILITY = "min_probability"
    OPT_OUT = "opt_out"
    FRAUD_SIGNAL = "fraud_signal"
    COOLDOWN = "cooldown"
    ACTION_BUDGET = "action_budget"


class ReasonCode(str, Enum):
    """Fixed enum for AI reasoning - auditable and testable."""
    INSUFFICIENT_FUNDS_DELAYED_RETRY = "insufficient_funds_delayed_retry"
    ISSUER_DECLINE_SWITCH_METHOD = "issuer_decline_switch_method"
    EXPIRED_CARD_REQUEST_UPDATE = "expired_card_request_update"
    TRANSIENT_ERROR_FAST_RETRY = "transient_error_fast_retry"
    ABANDONMENT_SEND_LINK = "abandonment_send_link"
    HIGH_VALUE_MANUAL_REVIEW = "high_value_manual_review"
    REPEAT_FAILURE_ESCALATE = "repeat_failure_escalate"
    FRAUD_SIGNAL_BLOCK = "fraud_signal_block"
    LOW_PROBABILITY_SUPPRESS = "low_probability_suppress"
    CONTACT_CAP_SUPPRESS = "contact_cap_suppress"
    NO_CONSENT_SUPPRESS = "no_consent_suppress"


# =============================================================================
# CORE ENTITIES
# =============================================================================

class RevenueLeak(BaseModel):
    """Unified leak entity - source-agnostic revenue at risk."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    leak_source: LeakSource
    payment_id: Optional[str] = None
    order_id: Optional[str] = None
    invoice_id: Optional[str] = None
    customer_id: str
    amount: Decimal
    currency: str = "INR"
    failure_category: Optional[FailureCategory] = None
    failure_reason: Optional[str] = None
    retry_count: int = 0
    detected_at: datetime
    created_at: datetime


class CustomerProfile(BaseModel):
    """Customer context for recovery decisions (PII already redacted)."""
    model_config = ConfigDict(from_attributes=True)

    customer_id: str
    historical_success_rate: float = Field(ge=0.0, le=1.0)
    prior_successes: int = 0
    prior_failures: int = 0
    preferred_method: Optional[str] = None
    alternate_methods: List[str] = []
    consent_status: bool = True
    contact_count_7d: int = 0
    contact_count_30d: int = 0
    opt_out: bool = False


class PredictionResult(BaseModel):
    """Calibrated ML recovery probability output."""
    recovery_probability: float = Field(ge=0.0, le=1.0)
    risk_score: float = Field(ge=0.0, le=1.0)
    model_version: str
    calibrated: bool = True
    confidence_interval: Optional[tuple[float, float]] = None


class AIRecommendation(BaseModel):
    """Structured, grounded AI recommendation - LLM output."""
    leak_diagnosis: str = Field(max_length=280)
    failure_category: FailureCategory
    recommended_action: RecoveryAction
    confidence: float = Field(ge=0.0, le=1.0)
    reason_codes: List[ReasonCode]
    evidence: List[dict] = Field(default_factory=list)
    customer_message_draft: Optional[str] = None
    message_language: Literal["en", "hinglish", "regional"] = "en"
    requires_human_review: bool = False

    model_config = ConfigDict(use_enum_values=True)


class StrategyOption(BaseModel):
    """Simulated strategy with expected economics."""
    action: RecoveryAction
    expected_recovery: Decimal
    intervention_cost: Decimal
    expected_net_recovery: Decimal
    probability_weighted: Decimal
    policy_allowed: bool
    stopped_by_rule: Optional[StoppingRuleReason] = None
    simulated: bool = True


class PolicyResult(BaseModel):
    """Deterministic policy engine output - versioned."""
    decision: PolicyDecision
    reason: PolicyReason
    policy_version: str
    stopping_rule_triggered: Optional[StoppingRuleReason] = None
    details: dict = Field(default_factory=dict)


class StopDecision(BaseModel):
    """Stopping rules output - first-class terminal state."""
    stop: bool
    rule: Optional[StoppingRuleReason] = None
    explanation: str


class RecoveryActionRequest(BaseModel):
    """Governed write tool request - requires policy token."""
    case_id: str
    action: RecoveryAction
    idempotency_key: str
    policy_token: str  # Proof of PolicyResult.ALLOW
    payload: dict = Field(default_factory=dict)


class RecoveryActionResult(BaseModel):
    """Result of a governed recovery execution."""
    success: bool
    action_taken: RecoveryAction
    outcome_amount: Optional[Decimal] = None
    razorpay_response: Optional[dict] = None
    error: Optional[str] = None


class BatchRecoveryReport(BaseModel):
    """The money slide - measured incremental recovery vs control."""
    cases_detected: int
    revenue_at_risk: Decimal
    treatment_count: int
    control_count: int
    recovery_rate_treatment: float
    recovery_rate_control: float
    incremental_recovery_rate_pp: float
    measured_money_recovered: Decimal
    incremental_revenue: Decimal
    intervention_cost: Decimal
    net_recovered: Decimal
    cost_per_rupee_recovered: Decimal
    guardrail_metrics: dict


class DecisionDossier(BaseModel):
    """One-click export for any case - full audit trail."""
    case_id: str
    leak: RevenueLeak
    customer: CustomerProfile
    prediction: PredictionResult
    ai_recommendation: AIRecommendation
    strategy_options: List[StrategyOption]
    selected_strategy: StrategyOption
    stopping_rules_check: StopDecision
    policy_decision: PolicyResult
    action_result: Optional[RecoveryActionResult]
    audit_timeline: List[dict]


# =============================================================================
# API REQUEST/RESPONSE
# =============================================================================

class WebhookPayload(BaseModel):
    """Razorpay webhook envelope."""
    event: str
    payload: dict
    created_at: int


class DemoInjectRequest(BaseModel):
    """Deterministic demo population injection."""
    seed: int = 42
    case_count: int = 50
    holdout_ratio: float = 0.15
    include_suppressed: bool = True
    include_human_review: bool = True
    include_denied: bool = True


class CaseFilter(BaseModel):
    """Case list filters."""
    leak_source: Optional[LeakSource] = None
    status: Optional[str] = None
    is_control: Optional[bool] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    page: int = 1
    page_size: int = 20