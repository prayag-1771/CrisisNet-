"""Database models for CrisisNet.

All PII-bearing fields (original_text) are stored encrypted.
Schema matches the specification:
  users, messages, redacted_messages, classifications, human_reviews,
  escalations, routing_history, responses, outcomes, analytics_events, audit_log
"""

import enum

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base


# ── Enums ──


class RoleEnum(str, enum.Enum):
    admin = "admin"
    human_reviewer = "human_reviewer"
    viewer = "viewer"


class SeverityEnum(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class MessageSourceEnum(str, enum.Enum):
    synthetic_seed = "synthetic_seed"
    demo_simulator = "demo_simulator"


# ── Models ──


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(RoleEnum), default=RoleEnum.viewer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    reviews = relationship("HumanReview", back_populates="reviewer")
    audit_actions = relationship("AuditLog", back_populates="actor")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(Enum(MessageSourceEnum), nullable=False)
    original_text_encrypted = Column(Text, nullable=False)
    redacted_text = Column(Text, nullable=True)
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())

    redacted_messages = relationship("RedactedMessage", back_populates="message")
    classifications = relationship("Classification", back_populates="message")
    routing_history = relationship("RoutingHistory", back_populates="message")
    responses = relationship("Response", back_populates="message")
    escalations = relationship("Escalation", back_populates="message")
    outcome = relationship("Outcome", back_populates="message", uselist=False)


class RedactedMessage(Base):
    """Stores the redaction mapping so original PII can be restored by admins."""
    __tablename__ = "redacted_messages"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=False)
    redaction_map = Column(JSONB, nullable=False)  # e.g. {"[NAME]": "John Doe", "[PHONE]": "555-1234"}
    redaction_method = Column(String(50), default="llm+regex")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    message = relationship("Message", back_populates="redacted_messages")


class Classification(Base):
    __tablename__ = "classifications"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=False)
    severity = Column(Enum(SeverityEnum), nullable=False)
    confidence = Column(Float, nullable=False)
    reason = Column(Text)
    model_used = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    message = relationship("Message", back_populates="classifications")
    human_reviews = relationship("HumanReview", back_populates="classification")


class HumanReview(Base):
    __tablename__ = "human_reviews"

    id = Column(Integer, primary_key=True, index=True)
    classification_id = Column(Integer, ForeignKey("classifications.id"), nullable=False)
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String(50), nullable=False)  # Approve, Escalate, Reject, Reclassify
    original_severity = Column(Enum(SeverityEnum), nullable=False)
    final_severity = Column(Enum(SeverityEnum), nullable=False)
    reason = Column(Text, nullable=False)  # No silent overrides — reason is mandatory
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    classification = relationship("Classification", back_populates="human_reviews")
    reviewer = relationship("User", back_populates="reviews")


class Escalation(Base):
    __tablename__ = "escalations"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=False)
    escalated_at = Column(DateTime(timezone=True), server_default=func.now())
    escalated_to = Column(String(100), nullable=False)  # e.g. "human_review_queue"
    status = Column(String(50), default="pending")  # pending, resolved, dismissed

    message = relationship("Message", back_populates="escalations")


class RoutingHistory(Base):
    __tablename__ = "routing_history"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=False)
    severity = Column(Enum(SeverityEnum), nullable=False)
    route = Column(String(100), nullable=False)
    routed_at = Column(DateTime(timezone=True), server_default=func.now())

    message = relationship("Message", back_populates="routing_history")


class Response(Base):
    __tablename__ = "responses"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=False)
    response_text = Column(Text, nullable=False)
    validator_passed = Column(Boolean, default=False, nullable=False)
    retry_count = Column(Integer, default=0)
    delivered_at = Column(DateTime(timezone=True), server_default=func.now())

    message = relationship("Message", back_populates="responses")


class Outcome(Base):
    __tablename__ = "outcomes"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("messages.id"), unique=True, nullable=False)
    resolution_status = Column(String(50), nullable=False)  # resolved, escalated, dismissed
    resolution_time_seconds = Column(Integer)
    final_classification = Column(Enum(SeverityEnum))
    graph_trace = Column(JSONB)  # Full node-by-node trace of the LangGraph execution
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    message = relationship("Message", back_populates="outcome")


class AnalyticsEvent(Base):
    __tablename__ = "analytics_events"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(100), nullable=False)
    payload = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, index=True)
    actor_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(200), nullable=False)
    resource_type = Column(String(100), nullable=False)
    resource_id = Column(String(100))
    details = Column(JSONB)  # Additional context for the audit entry
    ip_address = Column(String(45))  # IPv6 max length
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    actor = relationship("User", back_populates="audit_actions")
