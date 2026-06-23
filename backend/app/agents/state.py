from typing import TypedDict, Optional, List, Dict, Any
from operator import add
from typing import Annotated

class AgentState(TypedDict):
    """
    The state of the graph. As the graph executes, nodes will read from and write to this state.
    """
    message_id: int
    original_text: str
    redacted_text: Optional[str]
    
    # Classification Results
    ai_classification: Optional[str] # LOW, MEDIUM, HIGH, CRITICAL
    confidence: Optional[float]
    reason: Optional[str]
    
    # Human Review
    human_classification: Optional[str]
    
    # Routing and Response
    routing_decision: Optional[str]
    response_text: Optional[str]
    validator_passed: bool
    
    # We use `Annotated[..., add]` to append to the list rather than overwrite it.
    # This is critical for maintaining a full audit trail across all nodes.
    audit_trail: Annotated[List[Dict[str, Any]], add]
