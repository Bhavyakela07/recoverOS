"""
RecoverOS Database Models — ORM Mapping for Minimum Coherent 9-Table Schema
"""

from datetime import datetime
from decimal import Decimal
from sqlalchemy import Column, String, Float, Numeric, DateTime, Boolean, ForeignKey, Text, JSON, Integer
from sqlalchemy.orm import relationship

from db.database import Base


class MerchantModel(Base):
    __tablename__ = "merchants"

    id = Column(String(64), primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    razorpay_key_id = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    leaks = relationship("RevenueLeakModel", back_populates="merchant")


class CustomerModel(Base):
    __tablename__ = "customers"

    id = Column(String(64), primary_key=True, index=True)
    merchant_id = Column(String(64), ForeignKey("merchants.id"), nullable=True)
    email = Column(String(255), nullable=True, index=True)
    phone = Column(String(50), nullable=True)
    ltv_inr = Column(Numeric(12, 2), default=0.00)
    risk_tier = Column(String(50), default="LOW")
    has_dispute_history = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    leaks = relationship("RevenueLeakModel", back_populates="customer")


class RevenueLeakModel(Base):
    __tablename__ = "revenue_leaks"

    id = Column(String(64), primary_key=True, index=True)
    event_id = Column(String(255), unique=True, index=True, nullable=False)
    merchant_id = Column(String(64), ForeignKey("merchants.id"), nullable=True)
    customer_id = Column(String(64), ForeignKey("customers.id"), nullable=True)
    leak_source = Column(String(64), nullable=False)
    failure_category = Column(String(64), nullable=False)
    amount_inr = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(10), default="INR")
    status = Column(String(50), default="FAILED", index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    merchant = relationship("MerchantModel", back_populates="leaks")
    customer = relationship("CustomerModel", back_populates="leaks")
    case = relationship("RecoveryCaseModel", back_populates="leak", uselist=False)


class RecoveryCaseModel(Base):
    __tablename__ = "recovery_cases"

    id = Column(String(64), primary_key=True, index=True)
    leak_id = Column(String(64), ForeignKey("revenue_leaks.id"), nullable=False, unique=True)
    customer_id = Column(String(64), ForeignKey("customers.id"), nullable=True)
    decision = Column(String(50), nullable=False)  # ALLOW, HUMAN_REVIEW, DENY, SUPPRESSED, CONTROL, DO_NOT_RETRY
    reason_code = Column(String(100), nullable=False)
    p_recovery = Column(Float, nullable=False)
    expected_net_recovery = Column(Numeric(12, 2), default=0.00)
    action_type = Column(String(64), nullable=True)
    policy_token = Column(String(255), nullable=True)
    policy_version = Column(String(20), default="v1.0.0")
    is_control = Column(Boolean, default=False)
    
    # State Machine: FAILED, ANALYZING, RECOVERY_RECOMMENDED, DO_NOT_RETRY, SUPPRESSED, RECOVERY_LINK_CREATED, CUSTOMER_CONTACTED, PAYMENT_RETRIED, RECOVERED, EXPIRED
    lifecycle_status = Column(String(50), default="FAILED", index=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    leak = relationship("RevenueLeakModel", back_populates="case")
    ai_decision = relationship("AIDecisionModel", back_populates="case", uselist=False)
    payment_links = relationship("PaymentLinkModel", back_populates="case")
    email_messages = relationship("EmailMessageModel", back_populates="case")
    audit_events = relationship("AuditEventModel", back_populates="case")


class AIDecisionModel(Base):
    __tablename__ = "ai_decisions"

    id = Column(String(64), primary_key=True, index=True)
    case_id = Column(String(64), ForeignKey("recovery_cases.id"), nullable=False, unique=True)
    diagnosis = Column(Text, nullable=False)
    recommended_action = Column(String(64), nullable=False)
    rationale = Column(Text, nullable=False)
    confidence_score = Column(Float, default=1.0)
    draft_message_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    case = relationship("RecoveryCaseModel", back_populates="ai_decision")


class WebhookEventModel(Base):
    """Authoritative DB Store for Webhook Idempotency & Raw Event Logs."""
    __tablename__ = "webhook_events"

    id = Column(String(64), primary_key=True, index=True)
    event_id = Column(String(255), unique=True, index=True, nullable=False)
    event_type = Column(String(100), nullable=False, index=True)
    processing_status = Column(String(50), default="PROCESSING", index=True) # PROCESSING, PROCESSED, FAILED, IGNORED
    raw_payload_hash = Column(String(64), nullable=True)
    received_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)


class PaymentLinkModel(Base):
    """Stores official Razorpay Test Mode Payment Links (plink_...)."""
    __tablename__ = "payment_links"

    id = Column(String(64), primary_key=True, index=True)
    case_id = Column(String(64), ForeignKey("recovery_cases.id"), nullable=False)
    razorpay_link_id = Column(String(255), unique=True, index=True, nullable=False)
    short_url = Column(String(255), nullable=False)
    amount_inr = Column(Numeric(12, 2), nullable=False)
    status = Column(String(50), default="CREATED")  # CREATED, PAID, EXPIRED, CANCELLED
    expire_by = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    case = relationship("RecoveryCaseModel", back_populates="payment_links")
    email_messages = relationship("EmailMessageModel", back_populates="payment_link")


class EmailMessageModel(Base):
    """Tracks customer recovery email dispatches."""
    __tablename__ = "email_messages"

    id = Column(String(64), primary_key=True, index=True)
    case_id = Column(String(64), ForeignKey("recovery_cases.id"), nullable=False)
    recipient_email = Column(String(255), nullable=False)
    subject = Column(String(255), nullable=False)
    payment_link_id = Column(String(64), ForeignKey("payment_links.id"), nullable=True)
    dispatch_id = Column(String(255), nullable=True)
    status = Column(String(50), default="DELIVERED")  # PENDING, DELIVERED, FAILED
    sent_at = Column(DateTime, default=datetime.utcnow)

    case = relationship("RecoveryCaseModel", back_populates="email_messages")
    payment_link = relationship("PaymentLinkModel", back_populates="email_messages")


class AuditEventModel(Base):
    """Immutable audit trail with cryptographic signature seals."""
    __tablename__ = "audit_events"

    id = Column(String(64), primary_key=True, index=True)
    case_id = Column(String(64), ForeignKey("recovery_cases.id"), nullable=True)
    event_type = Column(String(100), nullable=False)
    payload_json = Column(JSON, nullable=False)
    sha256_signature = Column(String(64), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    case = relationship("RecoveryCaseModel", back_populates="audit_events")


class BatchRunModel(Base):
    __tablename__ = "batch_runs"

    id = Column(String(64), primary_key=True, index=True)
    seed = Column(String(50), default="42")
    cases_detected = Column(Numeric(10, 0), default=0)
    revenue_at_risk = Column(Numeric(12, 2), default=0.00)
    treatment_count = Column(Numeric(10, 0), default=0)
    control_count = Column(Numeric(10, 0), default=0)
    measured_money_recovered = Column(Numeric(12, 2), default=0.00)
    incremental_revenue = Column(Numeric(12, 2), default=0.00)
    net_recovered = Column(Numeric(12, 2), default=0.00)
    created_at = Column(DateTime, default=datetime.utcnow)
