"""Agent nodes for the CrisisNet LangGraph pipeline.

Each function is a "node" in the LangGraph state graph.
It receives the current AgentState, does its work, and returns
a partial dict that gets merged back into the state.
"""

from datetime import datetime, timezone

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from app.agents.state import AgentState
from app.core.config import settings
from app.core.llm import get_fast_llm, get_reasoning_llm


# ──────────────────────────────────────────────────────────────────────
# Node 1: PII Scrubber
# ──────────────────────────────────────────────────────────────────────

PII_SYSTEM_PROMPT = """\
You are a strict privacy agent. Your ONLY job is to redact Personally \
Identifiable Information (PII) from the user's message.

Detect and replace:
- Full names → [NAME]
- Phone numbers → [PHONE]
- Email addresses → [EMAIL]
- Physical/mailing addresses → [ADDRESS]

Rules:
1. Return ONLY the redacted text — no explanation, no preamble.
2. Preserve the original sentence structure and punctuation.
3. If no PII is found, return the original text unchanged.
"""


def pii_scrubber_node(state: AgentState) -> dict:
    """Scrub PII from the incoming message before any downstream processing."""
    text = state["original_text"]

    prompt = ChatPromptTemplate.from_messages([
        ("system", PII_SYSTEM_PROMPT),
        ("human", "{text}"),
    ])

    llm = get_fast_llm()
    chain = prompt | llm
    result = chain.invoke({"text": text})
    redacted_text = result.content.strip()

    return {
        "redacted_text": redacted_text,
        "audit_trail": [{
            "node": "pii_scrubber",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": "redacted_pii",
            "input_length": len(text),
            "output_length": len(redacted_text),
        }],
    }


# ──────────────────────────────────────────────────────────────────────
# Node 2: Severity Classifier
# ──────────────────────────────────────────────────────────────────────

class ClassificationOutput(BaseModel):
    """Pydantic schema enforced on the LLM's structured output."""
    severity: str = Field(
        description="Exactly one of: LOW, MEDIUM, HIGH, CRITICAL"
    )
    confidence: float = Field(
        ge=0.0, le=1.0,
        description="Confidence score between 0.0 and 1.0"
    )
    reason: str = Field(
        description="Concise clinical reason for the classification"
    )


CLASSIFIER_SYSTEM_PROMPT = """\
You are an expert crisis triage AI. Classify the severity of the following \
message into exactly one of: LOW, MEDIUM, HIGH, CRITICAL.

Guidelines (safety-first — minimize false negatives):
- LOW: General stress, venting, or requests for information with no risk indicators.
- MEDIUM: Moderate distress, mentions of feeling overwhelmed, but no self-harm ideation.
- HIGH: Direct expression of self-harm thoughts without an immediate plan, or \
  expressions of hopelessness suggesting risk.
- CRITICAL: Immediate self-harm plan, active danger to self or others, or \
  someone reporting an ongoing emergency.

When uncertain, classify HIGHER, not lower. Err on the side of caution.
"""

MODEL_NAME = "groq/llama-3.3-70b-versatile"


def severity_classifier_node(state: AgentState) -> dict:
    """Classify crisis severity. Uses structured output to guarantee schema."""
    text = state.get("redacted_text") or state["original_text"]

    prompt = ChatPromptTemplate.from_messages([
        ("system", CLASSIFIER_SYSTEM_PROMPT),
        ("human", "{text}"),
    ])

    llm = get_fast_llm()
    structured_llm = llm.with_structured_output(ClassificationOutput)
    chain = prompt | structured_llm
    result: ClassificationOutput = chain.invoke({"text": text})

    # Safety-first: if confidence is below threshold, escalate
    effective_severity = result.severity
    requires_review = (
        result.severity in ("HIGH", "CRITICAL")
        or result.confidence < settings.CONFIDENCE_THRESHOLD
    )

    # If low confidence, treat as HIGH regardless of label
    if result.confidence < settings.CONFIDENCE_THRESHOLD and result.severity in ("LOW", "MEDIUM"):
        effective_severity = "HIGH"

    return {
        "ai_classification": effective_severity,
        "confidence": result.confidence,
        "reason": result.reason,
        "model_used": MODEL_NAME,
        "requires_human_review": requires_review,
        "audit_trail": [{
            "node": "severity_classifier",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": "classified_severity",
            "details": {
                "raw_severity": result.severity,
                "effective_severity": effective_severity,
                "confidence": result.confidence,
                "requires_human_review": requires_review,
                "threshold": settings.CONFIDENCE_THRESHOLD,
            },
        }],
    }


# ──────────────────────────────────────────────────────────────────────
# Node 3: Router
# ──────────────────────────────────────────────────────────────────────

ROUTE_MAP = {
    "LOW": "self_help",
    "MEDIUM": "counselor_queue",
    "HIGH": "priority_counselor_queue",
    "CRITICAL": "human_review_queue",
}


def router_node(state: AgentState) -> dict:
    """Route the case based on final severity (human override takes precedence)."""
    severity = state.get("human_classification") or state["ai_classification"]
    route = ROUTE_MAP.get(severity, "human_review_queue")

    return {
        "routing_decision": route,
        "audit_trail": [{
            "node": "router",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": "routed_case",
            "details": {"severity": severity, "route": route},
        }],
    }


# ──────────────────────────────────────────────────────────────────────
# Node 4: Response Generator
# ──────────────────────────────────────────────────────────────────────

RESPONSE_SYSTEM_PROMPT = """\
You are a compassionate crisis support assistant generating an advisory response \
for a person in distress. This is a RESEARCH PROTOTYPE — not a clinical tool.

HARD CONSTRAINTS (you must follow all of these):
1. Never claim to be a licensed therapist, counselor, or clinician.
2. Never diagnose any condition.
3. Never promise confidentiality.
4. Always recommend contacting a human professional when the severity is MEDIUM or above.
5. Always include at least one crisis helpline (e.g., 988 Suicide & Crisis Lifeline in the US).
6. Be empathetic, warm, and non-judgmental.
7. Keep responses under 200 words.

Label the response: "⚠️ AI-generated, advisory only — not a substitute for professional help."
"""


def response_generator_node(state: AgentState) -> dict:
    """Generate an empathetic, advisory-only response. Uses Gemini for nuance."""
    text = state.get("redacted_text") or state["original_text"]
    severity = state.get("human_classification") or state["ai_classification"]

    prompt = ChatPromptTemplate.from_messages([
        ("system", RESPONSE_SYSTEM_PROMPT),
        ("human", "Severity: {severity}\nMessage: {text}\n\nGenerate a compassionate response."),
    ])

    llm = get_reasoning_llm()
    chain = prompt | llm
    result = chain.invoke({"text": text, "severity": severity})
    response_text = result.content.strip()

    current_retries = state.get("response_retries", 0)

    return {
        "response_text": response_text,
        "response_retries": current_retries,
        "audit_trail": [{
            "node": "response_generator",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": "generated_response",
            "details": {"response_length": len(response_text), "retry": current_retries},
        }],
    }


# ──────────────────────────────────────────────────────────────────────
# Node 5: Response Validator
# ──────────────────────────────────────────────────────────────────────

FORBIDDEN_PHRASES = [
    "i am a licensed",
    "i am a therapist",
    "i am a counselor",
    "i can diagnose",
    "your diagnosis is",
    "i promise confidentiality",
    "this is confidential",
    "i guarantee your privacy",
]


def response_validator_node(state: AgentState) -> dict:
    """
    Rule-based post-generation validator.
    Checks the response against hard constraints BEFORE it is logged as delivered.
    """
    response = state.get("response_text", "")
    response_lower = response.lower()

    passed = True
    violations = []

    # Check forbidden phrases
    for phrase in FORBIDDEN_PHRASES:
        if phrase in response_lower:
            passed = False
            violations.append(f"Contains forbidden phrase: '{phrase}'")

    # Check advisory label is present
    if "advisory only" not in response_lower and "ai-generated" not in response_lower:
        passed = False
        violations.append("Missing AI-generated advisory label")

    # For MEDIUM+ severity, check human-help recommendation
    severity = state.get("human_classification") or state.get("ai_classification", "LOW")
    if severity in ("MEDIUM", "HIGH", "CRITICAL"):
        has_helpline = any(
            kw in response_lower
            for kw in ["988", "crisis line", "helpline", "professional", "counselor", "therapist"]
        )
        if not has_helpline:
            passed = False
            violations.append("Missing human-help recommendation for MEDIUM+ severity")

    current_retries = state.get("response_retries", 0)

    return {
        "validator_passed": passed,
        "response_retries": current_retries + (0 if passed else 1),
        "audit_trail": [{
            "node": "response_validator",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": "validated_response",
            "details": {
                "passed": passed,
                "violations": violations,
                "retry_count": current_retries,
            },
        }],
    }


# ──────────────────────────────────────────────────────────────────────
# Node 6: Outcome Logger
# ──────────────────────────────────────────────────────────────────────

def outcome_logger_node(state: AgentState) -> dict:
    """Log the final outcome of the case processing."""
    return {
        "audit_trail": [{
            "node": "outcome_logger",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": "logged_outcome",
            "details": {
                "message_id": state["message_id"],
                "final_classification": state.get("human_classification") or state.get("ai_classification"),
                "routing": state.get("routing_decision"),
                "response_delivered": state.get("validator_passed", False),
                "human_reviewed": state.get("human_classification") is not None,
            },
        }],
    }
