"""Pydantic schemas for API request/response validation.

These are separate from the SQLAlchemy models — they define the
shape of data going in and out of the API, not the database.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field


# ── Auth Schemas ──


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: str = Field(default="viewer", pattern="^(admin|human_reviewer|viewer)$")


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefresh(BaseModel):
    refresh_token: str


class UserOut(BaseModel):
    id: int
    email: str
    role: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Message Schemas ──


class MessageSubmit(BaseModel):
    """Schema for submitting a synthetic message through the simulator."""
    text: str = Field(min_length=1, max_length=5000)
    source: str = Field(
        default="demo_simulator",
        pattern="^(synthetic_seed|demo_simulator)$",
    )


class MessageOut(BaseModel):
    id: int
    source: str
    redacted_text: Optional[str]
    submitted_at: datetime
    severity: Optional[str] = None
    confidence: Optional[float] = None
    status: Optional[str] = None

    model_config = {"from_attributes": True}


class MessageDetail(BaseModel):
    id: int
    source: str
    redacted_text: Optional[str]
    original_text: Optional[str] = None  # Only populated for admin/reviewer
    submitted_at: datetime
    classification: Optional["ClassificationOut"] = None
    response: Optional["ResponseOut"] = None
    routing: Optional[str] = None
    audit_trail: Optional[list] = None

    model_config = {"from_attributes": True}


# ── Classification Schemas ──


class ClassificationOut(BaseModel):
    id: int
    severity: str
    confidence: float
    reason: Optional[str]
    model_used: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Human Review Schemas ──


class HumanReviewAction(BaseModel):
    """Schema for a human reviewer taking action on a case."""
    action: str = Field(pattern="^(Approve|Escalate|Reject|Reclassify)$")
    final_severity: str = Field(pattern="^(LOW|MEDIUM|HIGH|CRITICAL)$")
    reason: str = Field(min_length=1, max_length=1000)


class HumanReviewOut(BaseModel):
    id: int
    classification_id: int
    reviewer_id: int
    action: str
    original_severity: str
    final_severity: str
    reason: str
    created_at: datetime

    model_config = {"from_attributes": True}


class QueueItem(BaseModel):
    """A case awaiting human review, shown in the dashboard queue."""
    message_id: int
    redacted_text: str
    ai_severity: str
    confidence: float
    reason: Optional[str]
    submitted_at: datetime
    classification_id: int


# ── Response Schemas ──


class ResponseOut(BaseModel):
    id: int
    response_text: str
    validator_passed: bool
    retry_count: int
    delivered_at: datetime

    model_config = {"from_attributes": True}


# ── Dashboard / Analytics Schemas ──


class DashboardStats(BaseModel):
    total_messages: int
    severity_distribution: dict  # {"LOW": 10, "MEDIUM": 5, ...}
    escalation_rate: float
    human_override_rate: float
    avg_resolution_time_seconds: Optional[float]
    pending_reviews: int


class AnalyticsEvent(BaseModel):
    event_type: str
    payload: dict
    created_at: datetime

    model_config = {"from_attributes": True}
