"""Human Review Queue API endpoints.

Handles listing pending reviews, taking review actions, and
RESUMING the LangGraph pipeline after a human decision.

When a reviewer submits an action, we:
1. Record the review in the database
2. Resume the interrupted graph using Command(resume=human_decision)
3. The graph continues from the human_review node → router → response → end
"""

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from langgraph.types import Command

from app.api.schemas import HumanReviewAction, HumanReviewOut, QueueItem
from app.core.security import get_current_user, require_role
from app.db.database import get_db
from app.models.models import (
    Classification,
    HumanReview,
    Message,
    Escalation,
    AuditLog,
    Response as ResponseModel,
    RoutingHistory,
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

    This endpoint does TWO things:
    1. Records the human review in the database.
    2. RESUMES the halted LangGraph pipeline by passing the human's
       decision back into the graph via Command(resume=...).

    The graph then continues: router → response_generator → validator → end.
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

    # ── 1. Record the review in the database ──
    review = HumanReview(
        classification_id=classification_id,
        reviewer_id=current_user.id,
        action=payload.action,
        original_severity=classification.severity,
        final_severity=payload.final_severity,
        reason=payload.reason,
    )
    db.add(review)

    if payload.action in ("Escalate", "Reclassify"):
        escalation = Escalation(
            message_id=classification.message_id,
            escalated_to="priority_counselor_queue",
            status="pending",
        )
        db.add(escalation)

    audit = AuditLog(
        actor_id=current_user.id,
        action="human_review_submitted",
        resource_type="classification",
        resource_id=str(classification_id),
        details={
            "action": payload.action,
            "ai_severity": classification.severity.value if hasattr(classification.severity, 'value') else classification.severity,
            "human_severity": payload.final_severity,
            "is_override": (
                classification.severity.value != payload.final_severity
                if hasattr(classification.severity, 'value')
                else classification.severity != payload.final_severity
            ),
            "reason": payload.reason,
        },
    )
    db.add(audit)
    await db.commit()
    await db.refresh(review)

    # ── 2. Resume the halted LangGraph pipeline ──
    message_id = classification.message_id
    thread_config = {"configurable": {"thread_id": str(message_id)}}

    try:
        from langgraph.checkpoint.postgres import PostgresSaver
        from app.core.config import settings
        from app.agents.graph import build_crisis_graph

        with PostgresSaver.from_conn_string(settings.DATABASE_SYNC_URL) as checkpointer:
            crisis_graph = build_crisis_graph(checkpointer=checkpointer)

            # The human_decision dict is what interrupt() returns inside the node
            human_decision = {
                "action": payload.action,
                "final_severity": payload.final_severity,
                "reason": payload.reason,
                "reviewer_id": current_user.id,
            }

            # Resume the graph from the interrupt point
            final_state = crisis_graph.invoke(
                Command(resume=human_decision),
                config=thread_config,
            )

            # Persist the remaining outputs (response, routing)
            if final_state.get("response_text"):
                response = ResponseModel(
                    message_id=message_id,
                    response_text=final_state["response_text"],
                    validator_passed=final_state.get("validator_passed", False),
                    retry_count=final_state.get("response_retries", 0),
                )
                db.add(response)

            if final_state.get("routing_decision"):
                routing = RoutingHistory(
                    message_id=message_id,
                    severity=final_state.get("human_classification") or final_state.get("ai_classification"),
                    route=final_state["routing_decision"],
                )
                db.add(routing)

            await db.commit()

        logger.info(
            "pipeline_resumed_and_completed",
            message_id=message_id,
            human_action=payload.action,
            final_severity=payload.final_severity,
            routing=final_state.get("routing_decision"),
        )

    except Exception as e:
        logger.error(
            "pipeline_resume_error",
            message_id=message_id,
            error=str(e),
        )
        # The review is still recorded even if resume fails

    # Broadcast queue update to dashboard
    await manager.broadcast("queue_update", {
        "classification_id": classification_id,
        "action": payload.action,
        "final_severity": payload.final_severity,
        "reviewer_id": current_user.id,
        "message_id": message_id,
    })

    logger.info(
        "human_review_submitted",
        classification_id=classification_id,
        action=payload.action,
        original=classification.severity.value if hasattr(classification.severity, 'value') else classification.severity,
        final=payload.final_severity,
    )

    return review
