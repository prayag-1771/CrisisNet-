"""CrisisNet LangGraph Workflow Definition.

Assembles all agent nodes into the full triage pipeline:
  START → pii_scrubber → severity_classifier
       → [confidence_gate] → human_review (interrupt)
       → router → response_generator → response_validator
       → outcome_logger → END

The graph uses a PostgreSQL-backed checkpointer so that
interrupt() genuinely halts execution and serializes state
to the database. Resume is triggered via Command(resume=...).
"""

from datetime import datetime, timezone

from langgraph.graph import StateGraph, END
from langgraph.types import interrupt, Command
from langgraph.checkpoint.postgres import PostgresSaver

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
      - If failed and retries >= max → outcome_logger (log as failed)
    """
    if state.get("validator_passed", False):
        return "outcome_logger"

    retries = state.get("response_retries", 0)
    if retries < settings.MAX_RESPONSE_RETRIES:
        return "response_generator"

    # Too many retries — log as failed, don't loop forever
    return "outcome_logger"


# ── Human Review Node (Genuine Interrupt) ──


def human_review_node(state: AgentState) -> dict:
    """
    This node calls LangGraph's interrupt() to GENUINELY pause execution.

    When this node is reached:
    1. The current AgentState is serialized to the PostgreSQL checkpointer.
    2. The graph.invoke() call returns immediately with an __interrupt__ status.
    3. Execution is fully halted — the Python process is free.
    4. Later, when a human reviewer acts via the dashboard API, we call
       graph.invoke(Command(resume=human_decision), config=...) to resume
       from this exact point with the human's decision injected.

    The interrupt() call returns the value passed by Command(resume=...).
    """
    # Log the escalation in the audit trail BEFORE interrupting
    audit_entry = {
        "node": "human_review",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": "awaiting_human_review",
        "details": {
            "ai_classification": state.get("ai_classification"),
            "confidence": state.get("confidence"),
            "reason": state.get("reason"),
        },
    }

    # ── THIS IS THE REAL INTERRUPT ──
    # Execution halts here. The graph state is checkpointed to Postgres.
    # When a reviewer resumes, `human_decision` will be the dict they pass.
    human_decision = interrupt({
        "message": "Awaiting human review",
        "ai_classification": state.get("ai_classification"),
        "confidence": state.get("confidence"),
        "reason": state.get("reason"),
        "message_id": state.get("message_id"),
    })

    # ── Execution resumes here after a human calls Command(resume=...) ──
    # human_decision is the dict passed by the reviewer, e.g.:
    # {"action": "Reclassify", "final_severity": "CRITICAL", "reason": "..."}

    final_severity = human_decision.get("final_severity", state.get("ai_classification"))
    action = human_decision.get("action", "Approve")

    return {
        "human_classification": final_severity,
        "human_action": action,
        "audit_trail": [
            audit_entry,
            {
                "node": "human_review",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "action": "human_review_completed",
                "details": {
                    "human_action": action,
                    "human_severity": final_severity,
                    "reviewer_reason": human_decision.get("reason"),
                },
            },
        ],
    }


# ── Checkpointer Factory ──


def get_checkpointer() -> PostgresSaver:
    """
    Create a PostgresSaver checkpointer using the sync database URL.
    LangGraph's checkpointer uses psycopg (sync), not asyncpg.
    """
    checkpointer = PostgresSaver.from_conn_string(settings.DATABASE_SYNC_URL)
    checkpointer.setup()  # Creates the checkpoint tables if they don't exist
    return checkpointer


# ── Build the Graph ──


def build_crisis_graph(checkpointer=None):
    """
    Construct and compile the CrisisNet LangGraph workflow.

    Args:
        checkpointer: A LangGraph checkpointer for state persistence.
                      If None, uses PostgresSaver (required for interrupt()).

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

    # Use provided checkpointer or create one
    if checkpointer is None:
        try:
            checkpointer = get_checkpointer()
        except Exception:
            # If DB is not available (e.g., during import/tests), compile without checkpointer
            pass

    return graph.compile(checkpointer=checkpointer)
