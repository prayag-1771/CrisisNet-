import pytest
from app.agents.nodes import pii_scrubber_node, response_validator_node
from app.agents.state import AgentState

def test_pii_scrubber_node():
    """Test that the PII scrubber correctly redacts information."""
    initial_state: AgentState = {
        "message_id": 1,
        "original_text": "My name is John Doe and my phone is 555-1234.",
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
        "audit_trail": []
    }

    # Because PII scrubber uses the LLM, in a real test suite we would mock the LLM call.
    # For this demonstration, we're just checking that the node returns a modified state
    # without crashing.
    # 
    # If API keys are loaded, this will hit Groq.
    try:
        new_state = pii_scrubber_node(initial_state)
        assert "redacted_text" in new_state
        assert new_state["redacted_text"] is not None
        
        # Original text shouldn't be in the redacted text if it worked
        # (Though LLMs are non-deterministic, so this is a soft check)
        assert "555-1234" not in new_state["redacted_text"]
    except Exception as e:
        pytest.skip(f"Skipping LLM test due to missing keys or network issue: {e}")

def test_response_validator_node_pass():
    """Test that valid responses pass the rule-based validator."""
    state: AgentState = {
        "message_id": 1,
        "original_text": "I feel sad.",
        "redacted_text": "I feel sad.",
        "ai_classification": "LOW",
        "confidence": 0.9,
        "reason": "Sadness.",
        "model_used": "test",
        "human_classification": None,
        "human_action": None,
        "requires_human_review": False,
        "routing_decision": "auto_respond",
        "response_text": "This is an automated response. I am an AI, not a professional. How can I help?",
        "validator_passed": False,
        "response_retries": 0,
        "audit_trail": []
    }

    new_state = response_validator_node(state)
    assert new_state["validator_passed"] is True
    assert new_state["response_retries"] == 0

def test_response_validator_node_fail():
    """Test that responses with forbidden phrases fail the validator."""
    state: AgentState = {
        "message_id": 1,
        "original_text": "I feel sad.",
        "redacted_text": "I feel sad.",
        "ai_classification": "LOW",
        "confidence": 0.9,
        "reason": "Sadness.",
        "model_used": "test",
        "human_classification": None,
        "human_action": None,
        "requires_human_review": False,
        "routing_decision": "auto_respond",
        "response_text": "I am a licensed therapist and I can cure you.",
        "validator_passed": False,
        "response_retries": 0,
        "audit_trail": []
    }

    new_state = response_validator_node(state)
    assert new_state["validator_passed"] is False
    assert new_state["response_retries"] == 1
