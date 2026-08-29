"""
RecoverOS Database Models — ORM Mapping for Persistence Layer
"""

from datetime import datetime
from decimal import Decimal
from sqlalchemy import Column, String, Float, Numeric, DateTime, Boolean, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship

from db.database import Base


class MerchantModel(Base):
    __tablename__ = "merchants"

    id = Column(String(64), primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    razorpay_key_id = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    leaks = relationship("RevenueLeakModel", back_populates="merchant")


class CustomerModel(Base):
    __tablename__ = "customers"

    id = Column(String(64), primary_key=True, index=True)
    merchant_id = Column(String(64), ForeignKey("merchants.id"), nullable=True)
    email = Column(String(255), nullable=True)
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
    leak_source = Column(String(64), nullable=False)  # payment_failed, checkout_abandonment, etc.
    failure_category = Column(String(64), nullable=False)
    amount_inr = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(10), default="INR")
    status = Column(String(50), default="DETECTED")
    created_at = Column(DateTime, default=datetime.utcnow)

    merchant = relationship("MerchantModel", back_populates="leaks")
    customer = relationship("CustomerModel", back_populates="leaks")
    case = relationship("RecoveryCaseModel", back_populates="leak", uselist=False)


class RecoveryCaseModel(Base):
    __tablename__ = "recovery_cases"

    id = Column(String(64), primary_key=True, index=True)
    leak_id = Column(String(64), ForeignKey("revenue_leaks.id"), nullable=False, unique=True)
    customer_id = Column(String(64), ForeignKey("customers.id"), nullable=True)
    decision = Column(String(50), nullable=False)  # ALLOW, HUMAN_REVIEW, DENY, SUPPRESSED, CONTROL
    reason_code = Column(String(100), nullable=False)
    p_recovery = Column(Float, nullable=False)
    expected_net_recovery = Column(Numeric(12, 2), default=0.00)
    action_type = Column(String(64), nullable=True)
    policy_token = Column(String(255), nullable=True)
    policy_version = Column(String(20), default="v1.0.0")
    is_control = Column(Boolean, default=False)
    status = Column(String(50), default="OPEN")  # OPEN, ACTIONED, RECOVERED, CLOSED
    created_at = Column(DateTime, default=datetime.utcnow)

    leak = relationship("RevenueLeakModel", back_populates="case")
    ai_decision = relationship("AIDecisionModel", back_populates="case", uselist=False)
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


class AuditEventModel(Base):
    __tablename__ = "audit_events"

    id = Column(String(64), primary_key=True, index=True)
    case_id = Column(String(64), ForeignKey("recovery_cases.id"), nullable=True)
    event_type = Column(String(100), nullable=False)
    payload_json = Column(JSON, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    case = relationship("RecoveryCaseModel", back_populates="audit_events")


class BatchRunModel(Base):
    __tablename__ = "batch_runs"

    id = Column(String(64), primary_key=True, index=True)
    seed = Column(Integer if False else String(50), default="42")
    cases_detected = Column(Numeric(10, 0), default=0)
    revenue_at_risk = Column(Numeric(12, 2), default=0.00)
    treatment_count = Column(Numeric(10, 0), default=0)
    control_count = Column(Numeric(10, 0), default=0)
    measured_money_recovered = Column(Numeric(12, 2), default=0.00)
    incremental_revenue = Column(Numeric(12, 2), default=0.00)
    net_recovered = Column(Numeric(12, 2), default=0.00)
    created_at = Column(DateTime, default=datetime.utcnow)
