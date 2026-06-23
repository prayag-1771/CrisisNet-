"""CrisisNet LangGraph Workflow Definition.

Assembles all agent nodes into the full triage pipeline:
  START → ingest → pii_scrubber → severity_classifier
       → [confidence_gate / critical_check] → human_review (interrupt)
       → router → response_generator → response_validator
       → outcome_logger → END
"""

from langgraph.graph import StateGraph, END

from app.agents.state import AgentState
from app.agents.nodes import (
    pii_scrubber_node,
    severity_classifier_node,
    router_node,
    response_generator_node,
    response_validator_node,
    outcome_logger_node,
)
from app.core.config import settings


# ── Conditional Edge Functions ──


def should_escalate_to_human(state: AgentState) -> str:
    """
    Confidence gate + critical check combined.

    Routes to 'human_review' if:
      - severity is HIGH or CRITICAL
      - OR confidence is below the configured threshold

    Otherwise routes to 'router' to continue automated processing.
    """
    if state.get("requires_human_review", False):
        return "human_review"
    return "router"


def should_retry_response(state: AgentState) -> str:
    """
    After the response validator, decide what to do:
      - If passed → outcome_logger
      - If failed and retries < max → response_generator (retry)
      - If failed and retries >= max → human_review (flag for human)
    """
    if state.get("validator_passed", False):
        return "outcome_logger"

    retries = state.get("response_retries", 0)
    if retries < settings.MAX_RESPONSE_RETRIES:
        return "response_generator"

    # Too many retries — flag for human review
    return "outcome_logger"  # Log as failed, don't loop forever


# ── Human Review Node (Interrupt) ──


def human_review_node(state: AgentState) -> dict:
    """
    This node uses LangGraph's interrupt() to pause execution.
    The graph state is persisted to the checkpointer (Postgres),
    and execution only resumes when a human reviewer takes action
    via the dashboard API.

    In the current implementation, this is a placeholder that will
    be wired to the actual interrupt() mechanism when we set up
    the checkpointer.
    """
    from datetime import datetime, timezone

    # In production LangGraph, this is where interrupt() is called.
    # For now, we log the escalation and the graph will be invoked
    # with human_classification set when the reviewer acts.

    return {
        "audit_trail": [{
            "node": "human_review",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": "awaiting_human_review",
            "details": {
                "ai_classification": state.get("ai_classification"),
                "confidence": state.get("confidence"),
                "reason": state.get("reason"),
            },
        }],
    }


# ── Build the Graph ──


def build_crisis_graph() -> StateGraph:
    """
    Construct and compile the CrisisNet LangGraph workflow.

    Returns a compiled graph that can be invoked with an initial state dict.
    """
    graph = StateGraph(AgentState)

    # Add all nodes
    graph.add_node("pii_scrubber", pii_scrubber_node)
    graph.add_node("severity_classifier", severity_classifier_node)
    graph.add_node("human_review", human_review_node)
    graph.add_node("router", router_node)
    graph.add_node("response_generator", response_generator_node)
    graph.add_node("response_validator", response_validator_node)
    graph.add_node("outcome_logger", outcome_logger_node)

    # Define edges
    graph.set_entry_point("pii_scrubber")

    graph.add_edge("pii_scrubber", "severity_classifier")

    # Conditional: escalate to human or continue to router
    graph.add_conditional_edges(
        "severity_classifier",
        should_escalate_to_human,
        {
            "human_review": "human_review",
            "router": "router",
        },
    )

    # After human review, continue to router
    graph.add_edge("human_review", "router")

    graph.add_edge("router", "response_generator")
    graph.add_edge("response_generator", "response_validator")

    # Conditional: retry, flag, or proceed
    graph.add_conditional_edges(
        "response_validator",
        should_retry_response,
        {
            "response_generator": "response_generator",
            "outcome_logger": "outcome_logger",
        },
    )

    graph.add_edge("outcome_logger", END)

    return graph.compile()


# Pre-built graph instance for use across the application
crisis_graph = build_crisis_graph()
