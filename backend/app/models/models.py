import enum
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, JSON, Enum, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base

class RoleEnum(str, enum.Enum):
    admin = "admin"
    human_reviewer = "human_reviewer"
    viewer = "viewer"

class SeverityEnum(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(Enum(RoleEnum), default=RoleEnum.viewer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    source = Column(String, nullable=False) # e.g., synthetic_seed, demo_simulator
    original_text_encrypted = Column(Text, nullable=False)
    redacted_text = Column(Text, nullable=True)
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())
    
    classifications = relationship("Classification", back_populates="message")
    responses = relationship("Response", back_populates="message")

class Classification(Base):
    __tablename__ = "classifications"
    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("messages.id"))
    severity = Column(Enum(SeverityEnum))
    confidence = Column(Float)
    reason = Column(Text)
    model_used = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    message = relationship("Message", back_populates="classifications")
    human_reviews = relationship("HumanReview", back_populates="classification")

class HumanReview(Base):
    __tablename__ = "human_reviews"
    id = Column(Integer, primary_key=True, index=True)
    classification_id = Column(Integer, ForeignKey("classifications.id"))
    reviewer_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String) # Approve, Escalate, Reject, Reclassify
    original_severity = Column(Enum(SeverityEnum))
    final_severity = Column(Enum(SeverityEnum))
    reason = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    classification = relationship("Classification", back_populates="human_reviews")

class RoutingHistory(Base):
    __tablename__ = "routing_history"
    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("messages.id"))
    severity = Column(Enum(SeverityEnum))
    route = Column(String)
    routed_at = Column(DateTime(timezone=True), server_default=func.now())

class Response(Base):
    __tablename__ = "responses"
    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("messages.id"))
    response_text = Column(Text)
    validator_passed = Column(Boolean, default=False)
    delivered_at = Column(DateTime(timezone=True), server_default=func.now())
    
    message = relationship("Message", back_populates="responses")

class Outcome(Base):
    __tablename__ = "outcomes"
    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("messages.id"))
    resolution_status = Column(String)
    resolution_time = Column(Integer) # in seconds
    final_classification = Column(Enum(SeverityEnum))

class AuditLog(Base):
    __tablename__ = "audit_log"
    id = Column(Integer, primary_key=True, index=True)
    actor_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String)
    resource_type = Column(String)
    resource_id = Column(String)
    ip_address = Column(String)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
