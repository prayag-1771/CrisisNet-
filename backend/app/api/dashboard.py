"""Dashboard analytics API endpoints.

Provides aggregate statistics for the dashboard:
- Severity distribution
- Escalation & override rates
- Resolution time metrics
- Trend data
"""

import structlog
from fastapi import APIRouter, Depends
from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import DashboardStats
from app.core.security import get_current_user
from app.db.database import get_db
from app.models.models import (
    Message,
    Classification,
    HumanReview,
    Outcome,
    Escalation,
)

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1/dashboard", tags=["Dashboard Analytics"])


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get aggregate dashboard statistics."""

    # Total messages
    total_result = await db.execute(select(func.count(Message.id)))
    total_messages = total_result.scalar() or 0

    # Severity distribution
    severity_result = await db.execute(
        select(Classification.severity, func.count(Classification.id))
        .group_by(Classification.severity)
    )
    severity_distribution = {}
    for row in severity_result.all():
        key = row[0].value if hasattr(row[0], 'value') else str(row[0])
        severity_distribution[key] = row[1]

    # Escalation rate: how many messages got escalated vs total
    escalation_count_result = await db.execute(
        select(func.count(func.distinct(Escalation.message_id)))
    )
    escalation_count = escalation_count_result.scalar() or 0
    escalation_rate = (escalation_count / total_messages * 100) if total_messages > 0 else 0.0

    # Human override rate: how often humans changed the AI classification
    total_reviews_result = await db.execute(select(func.count(HumanReview.id)))
    total_reviews = total_reviews_result.scalar() or 0

    override_result = await db.execute(
        select(func.count(HumanReview.id))
        .where(HumanReview.original_severity != HumanReview.final_severity)
    )
    override_count = override_result.scalar() or 0
    human_override_rate = (override_count / total_reviews * 100) if total_reviews > 0 else 0.0

    # Average resolution time
    avg_resolution_result = await db.execute(
        select(func.avg(Outcome.resolution_time_seconds))
    )
    avg_resolution_time = avg_resolution_result.scalar()

    # Pending reviews count
    reviewed_ids = select(HumanReview.classification_id).distinct()
    pending_result = await db.execute(
        select(func.count(Classification.id))
        .where(
            Classification.id.notin_(reviewed_ids),
            Classification.severity.in_(["HIGH", "CRITICAL"]) |
            (Classification.confidence < 0.75)
        )
    )
    pending_reviews = pending_result.scalar() or 0

    return DashboardStats(
        total_messages=total_messages,
        severity_distribution=severity_distribution,
        escalation_rate=round(escalation_rate, 2),
        human_override_rate=round(human_override_rate, 2),
        avg_resolution_time_seconds=round(avg_resolution_time, 1) if avg_resolution_time else None,
        pending_reviews=pending_reviews,
    )


@router.get("/severity-trend")
async def get_severity_trend(
    days: int = 7,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get daily severity counts for trend charts."""
    from datetime import datetime, timedelta, timezone

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    result = await db.execute(
        select(
            func.date(Classification.created_at).label("date"),
            Classification.severity,
            func.count(Classification.id).label("count"),
        )
        .where(Classification.created_at >= cutoff)
        .group_by(func.date(Classification.created_at), Classification.severity)
        .order_by(func.date(Classification.created_at))
    )

    trends = {}
    for row in result.all():
        date_str = str(row[0])
        severity = row[1].value if hasattr(row[1], 'value') else str(row[1])
        count = row[2]

        if date_str not in trends:
            trends[date_str] = {"date": date_str, "LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
        trends[date_str][severity] = count

    return list(trends.values())


@router.get("/false-negative-tracker")
async def get_false_negative_tracker(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Track cases initially classified as LOW/MEDIUM that a human later
    reclassified as HIGH/CRITICAL.

    This is the most important safety metric — it measures how often the
    AI underestimates severity.
    """
    result = await db.execute(
        select(
            HumanReview.id,
            HumanReview.original_severity,
            HumanReview.final_severity,
            HumanReview.reason,
            HumanReview.created_at,
        )
        .where(
            HumanReview.original_severity.in_(["LOW", "MEDIUM"]),
            HumanReview.final_severity.in_(["HIGH", "CRITICAL"]),
        )
        .order_by(desc(HumanReview.created_at))
    )

    false_negatives = []
    for row in result.all():
        false_negatives.append({
            "review_id": row[0],
            "ai_classification": row[1].value if hasattr(row[1], 'value') else str(row[1]),
            "human_classification": row[2].value if hasattr(row[2], 'value') else str(row[2]),
            "reason": row[3],
            "timestamp": row[4].isoformat() if row[4] else None,
        })

    return {
        "total_false_negatives": len(false_negatives),
        "cases": false_negatives,
    }
