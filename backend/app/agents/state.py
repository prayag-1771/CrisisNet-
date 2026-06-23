"""LangGraph State Schema for the CrisisNet triage pipeline.

This TypedDict is the "shared memory" passed from node to node in the graph.
Every field a node needs to read or write must be declared here.
"""

from typing import Annotated, Any, Dict, List, Optional, TypedDict
from operator import add


class AgentState(TypedDict):
    """
    Immutable schema for the LangGraph state.

    Fields use Annotated[..., add] where we need to *append* rather than
    overwrite — specifically the audit_trail, which every node appends to.
    """

    # ── Message ──
    message_id: int
    original_text: str
    redacted_text: Optional[str]

    # ── Classification ──
    ai_classification: Optional[str]  # LOW | MEDIUM | HIGH | CRITICAL
    confidence: Optional[float]  # 0.0 – 1.0
    reason: Optional[str]
    model_used: Optional[str]  # e.g. "groq/llama3-70b-8192"

    # ── Human Review ──
    human_classification: Optional[str]  # Set only if a human overrides
    human_action: Optional[str]  # Approve | Escalate | Reject | Reclassify
    requires_human_review: bool  # True if confidence < threshold or severity >= HIGH

    # ── Routing ──
    routing_decision: Optional[str]  # self_help | counselor_queue | priority_counselor | human_review

    # ── Response ──
    response_text: Optional[str]
    validator_passed: bool
    response_retries: int  # How many times response_generator has been retried

    # ── Audit Trail (append-only) ──
    audit_trail: Annotated[List[Dict[str, Any]], add]
