"""Human Review Queue API endpoints.

Handles listing pending reviews, taking review actions, and
tracking human override metrics.
"""

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.api.schemas import HumanReviewAction, HumanReviewOut, QueueItem
from app.core.security import get_current_user, require_role
from app.db.database import get_db
from app.models.models import (
    Classification,
    HumanReview,
    Message,
    Escalation,
    AuditLog,
)
from app.api.websockets import manager

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1/reviews", tags=["Human Review Queue"])


@router.get("/queue", response_model=List[QueueItem])
async def get_review_queue(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("admin", "human_reviewer")),
):
    """
    Get all cases pending human review.

    Cases enter this queue when:
    - Severity is HIGH or CRITICAL
    - Classification confidence is below the threshold (< 0.75)
    """
    # Find classifications that need review but haven't been reviewed yet
    reviewed_subquery = (
        select(HumanReview.classification_id)
        .distinct()
    )

    query = (
        select(Classification, Message)
        .join(Message, Message.id == Classification.message_id)
        .where(
            Classification.id.notin_(reviewed_subquery),
            Classification.severity.in_(["HIGH", "CRITICAL"]) |
            (Classification.confidence < 0.75)
        )
        .order_by(desc(Classification.created_at))
    )

    result = await db.execute(query)
    rows = result.all()

    queue_items = []
    for classification, message in rows:
        queue_items.append(QueueItem(
            message_id=message.id,
            redacted_text=message.redacted_text or "[Pending PII redaction]",
            ai_severity=classification.severity.value if hasattr(classification.severity, 'value') else classification.severity,
            confidence=classification.confidence,
            reason=classification.reason,
            submitted_at=message.submitted_at,
            classification_id=classification.id,
        ))

    return queue_items


@router.post("/{classification_id}", response_model=HumanReviewOut)
async def submit_review(
    classification_id: int,
    payload: HumanReviewAction,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("admin", "human_reviewer")),
):
    """
    Submit a human review action on a classification.

    Actions:
    - Approve: Accept the AI classification as-is
    - Escalate: Escalate to a higher priority
    - Reject: Reject the classification entirely
    - Reclassify: Change the severity level (must provide final_severity)
    """
    # Find the classification
    result = await db.execute(
        select(Classification).where(Classification.id == classification_id)
    )
    classification = result.scalar_one_or_none()
    if not classification:
        raise HTTPException(status_code=404, detail="Classification not found")

    # Check if already reviewed
    existing = await db.execute(
        select(HumanReview).where(HumanReview.classification_id == classification_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This classification has already been reviewed",
        )

    # Create the review
    review = HumanReview(
        classification_id=classification_id,
        reviewer_id=current_user.id,
        action=payload.action,
        original_severity=classification.severity,
        final_severity=payload.final_severity,
        reason=payload.reason,
    )
    db.add(review)

    # Create escalation record if needed
    if payload.action in ("Escalate", "Reclassify"):
        escalation = Escalation(
            message_id=classification.message_id,
            escalated_to="priority_counselor_queue",
            status="pending",
        )
        db.add(escalation)

    # Audit log — captures the delta between AI and human decision
    audit = AuditLog(
        actor_id=current_user.id,
        action="human_review_submitted",
        resource_type="classification",
        resource_id=str(classification_id),
        details={
            "action": payload.action,
            "ai_severity": classification.severity.value if hasattr(classification.severity, 'value') else classification.severity,
            "human_severity": payload.final_severity,
            "is_override": classification.severity.value != payload.final_severity if hasattr(classification.severity, 'value') else classification.severity != payload.final_severity,
            "reason": payload.reason,
        },
    )
    db.add(audit)
    await db.commit()
    await db.refresh(review)

    # Broadcast queue update to dashboard
    await manager.broadcast("queue_update", {
        "classification_id": classification_id,
        "action": payload.action,
        "final_severity": payload.final_severity,
        "reviewer_id": current_user.id,
    })

    logger.info(
        "human_review_submitted",
        classification_id=classification_id,
        action=payload.action,
        original=classification.severity.value if hasattr(classification.severity, 'value') else classification.severity,
        final=payload.final_severity,
    )

    return review
