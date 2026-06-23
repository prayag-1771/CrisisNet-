from app.agents.state import AgentState
from app.core.llm import get_fast_llm
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
import datetime

fast_llm = get_fast_llm()

def pii_scrubber_node(state: AgentState) -> dict:
    """
    Node 1: Scub PII from the incoming message.
    """
    text = state["original_text"]
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a strict privacy agent. Your ONLY job is to redact Names, Phone Numbers, Emails, and Physical Addresses from the user's message. Replace them with [NAME], [PHONE], [EMAIL], [ADDRESS]. Return ONLY the redacted text, without any conversational filler or explanation."),
        ("human", "{text}")
    ])
    
    chain = prompt | fast_llm
    result = chain.invoke({"text": text})
    redacted_text = result.content.strip()
    
    audit_entry = {
        "node": "pii_scrubber",
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "action": "redacted_pii"
    }
    
    return {"redacted_text": redacted_text, "audit_trail": [audit_entry]}


class ClassificationOutput(BaseModel):
    severity: str = Field(description="Must be exactly one of: LOW, MEDIUM, HIGH, CRITICAL")
    confidence: float = Field(description="Confidence score between 0.0 and 1.0")
    reason: str = Field(description="Concise reason for the classification")

def severity_classifier_node(state: AgentState) -> dict:
    """
    Node 2: Classify the severity of the crisis.
    """
    text = state.get("redacted_text") or state["original_text"]
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert crisis triage AI. Classify the severity of the following message into LOW, MEDIUM, HIGH, or CRITICAL. Be conservative and prioritize safety over minimizing false alarms. A direct expression of self-harm without an immediate plan is HIGH. An immediate plan is CRITICAL."),
        ("human", "{text}")
    ])
    
    # We use structured output to ensure we get a JSON matching our schema
    structured_llm = fast_llm.with_structured_output(ClassificationOutput)
    chain = prompt | structured_llm
    result: ClassificationOutput = chain.invoke({"text": text})
    
    audit_entry = {
        "node": "severity_classifier",
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "action": "classified_severity",
        "details": {"severity": result.severity, "confidence": result.confidence}
    }
    
    return {
        "ai_classification": result.severity,
        "confidence": result.confidence,
        "reason": result.reason,
        "audit_trail": [audit_entry]
    }
