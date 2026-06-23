"""Message ingestion API endpoints.

Handles submitting synthetic messages into the LangGraph pipeline
and retrieving message details.
"""

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.api.schemas import MessageSubmit, MessageOut, MessageDetail
from app.core.security import get_current_user, require_role
from app.db.database import get_db
from app.models.models import (
    Message,
    Classification,
    Response as ResponseModel,
    AuditLog,
    RoutingHistory,
)
from app.api.websockets import manager

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1/messages", tags=["Messages"])


@router.post("/", response_model=MessageOut, status_code=status.HTTP_201_CREATED)
async def submit_message(
    payload: MessageSubmit,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Submit a synthetic message to trigger the CrisisNet pipeline.

    This is a sandboxed simulator endpoint — not a real intake.
    The message is stored and then processed through the LangGraph pipeline.
    """
    # Store the message (original text is stored "encrypted" — placeholder for real encryption)
    message = Message(
        source=payload.source,
        original_text_encrypted=payload.text,  # TODO: Encrypt with AES
        redacted_text=None,  # Will be filled by PII scrubber
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)

    # Audit log
    audit = AuditLog(
        actor_id=current_user.id,
        action="message_submitted",
        resource_type="message",
        resource_id=str(message.id),
    )
    db.add(audit)
    await db.commit()

    logger.info("message_submitted", message_id=message.id, source=payload.source)

    # Run the LangGraph pipeline asynchronously
    # We import here to avoid circular imports and to keep it lazy
    from app.agents.graph import crisis_graph

    initial_state = {
        "message_id": message.id,
        "original_text": payload.text,
        "redacted_text": None,
        "ai_classification": None,
        "confidence": None,
        "reason": None,
        "model_used": None,
        "human_classification": None,
        "human_action": None,
        "requires_human_review": False,
        "routing_decision": None,
        "response_text": None,
        "validator_passed": False,
        "response_retries": 0,
        "audit_trail": [],
    }

    try:
        # Run the graph
        result = crisis_graph.invoke(initial_state)

        # Update message with redacted text
        message.redacted_text = result.get("redacted_text")
        await db.commit()

        # Store classification
        classification = Classification(
            message_id=message.id,
            severity=result.get("ai_classification"),
            confidence=result.get("confidence"),
            reason=result.get("reason"),
            model_used=result.get("model_used"),
        )
        db.add(classification)

        # Store response if generated
        if result.get("response_text"):
            response = ResponseModel(
                message_id=message.id,
                response_text=result["response_text"],
                validator_passed=result.get("validator_passed", False),
                retry_count=result.get("response_retries", 0),
            )
            db.add(response)

        # Store routing history
        if result.get("routing_decision"):
            routing = RoutingHistory(
                message_id=message.id,
                severity=result.get("human_classification") or result.get("ai_classification"),
                route=result["routing_decision"],
            )
            db.add(routing)

        await db.commit()

        # Broadcast to WebSocket clients
        await manager.broadcast("new_message", {
            "message_id": message.id,
            "severity": result.get("ai_classification"),
            "confidence": result.get("confidence"),
            "requires_review": result.get("requires_human_review", False),
        })

        logger.info(
            "pipeline_completed",
            message_id=message.id,
            severity=result.get("ai_classification"),
            confidence=result.get("confidence"),
        )

    except Exception as e:
        logger.error("pipeline_error", message_id=message.id, error=str(e))
        # Don't fail the HTTP request — the message is stored, pipeline can be retried

    return MessageOut(
        id=message.id,
        source=message.source,
        redacted_text=message.redacted_text,
        submitted_at=message.submitted_at,
    )


@router.get("/", response_model=List[MessageOut])
async def list_messages(
    skip: int = 0,
    limit: int = 50,
    severity: str = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List messages with optional severity filter. Most recent first."""
    query = select(Message).order_by(desc(Message.submitted_at))

    if severity:
        # Join with classifications to filter by severity
        query = (
            query.join(Classification, Classification.message_id == Message.id)
            .where(Classification.severity == severity)
        )

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    messages = result.scalars().all()

    # Enrich with classification data
    out = []
    for msg in messages:
        # Get latest classification
        cls_result = await db.execute(
            select(Classification)
            .where(Classification.message_id == msg.id)
            .order_by(desc(Classification.created_at))
            .limit(1)
        )
        cls = cls_result.scalar_one_or_none()

        out.append(MessageOut(
            id=msg.id,
            source=msg.source.value if hasattr(msg.source, 'value') else msg.source,
            redacted_text=msg.redacted_text,
            submitted_at=msg.submitted_at,
            severity=cls.severity.value if cls else None,
            confidence=cls.confidence if cls else None,
        ))

    return out


@router.get("/{message_id}", response_model=MessageDetail)
async def get_message(
    message_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get detailed information about a specific message."""
    result = await db.execute(select(Message).where(Message.id == message_id))
    message = result.scalar_one_or_none()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    # Get classification
    cls_result = await db.execute(
        select(Classification)
        .where(Classification.message_id == message_id)
        .order_by(desc(Classification.created_at))
        .limit(1)
    )
    cls = cls_result.scalar_one_or_none()

    # Get response
    resp_result = await db.execute(
        select(ResponseModel)
        .where(ResponseModel.message_id == message_id)
        .order_by(desc(ResponseModel.delivered_at))
        .limit(1)
    )
    resp = resp_result.scalar_one_or_none()

    # Get routing
    route_result = await db.execute(
        select(RoutingHistory)
        .where(RoutingHistory.message_id == message_id)
        .order_by(desc(RoutingHistory.routed_at))
        .limit(1)
    )
    route = route_result.scalar_one_or_none()

    # Only admin/reviewer can see original text
    original_text = None
    if current_user.role.value in ("admin", "human_reviewer"):
        original_text = message.original_text_encrypted  # TODO: Decrypt
        # Audit log access to original text
        audit = AuditLog(
            actor_id=current_user.id,
            action="viewed_original_text",
            resource_type="message",
            resource_id=str(message_id),
        )
        db.add(audit)
        await db.commit()

    return MessageDetail(
        id=message.id,
        source=message.source.value if hasattr(message.source, 'value') else message.source,
        redacted_text=message.redacted_text,
        original_text=original_text,
        submitted_at=message.submitted_at,
        classification=cls,
        response=resp,
        routing=route.route if route else None,
    )
