"""LLM provider abstraction layer.

Models are swappable via config, not hardcoded.
- Fast LLM (Groq): classification, PII scrubbing, routing — latency-sensitive steps
- Reasoning LLM (Gemini): response generation, pattern analysis — longer-context steps
"""

from functools import lru_cache

from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI

from app.core.config import settings


@lru_cache(maxsize=1)
def get_fast_llm() -> ChatGroq:
    """
    Returns the fast inference model (Groq / Llama 3) used for classification,
    PII scrubbing, routing, and other latency-sensitive steps.

    Cached so we don't create a new client on every node invocation.
    """
    return ChatGroq(
        api_key=settings.GROQ_API_KEY,
        model_name="llama-3.3-70b-versatile",
        temperature=0.0,  # Deterministic output for classification
    )


def get_reasoning_llm() -> ChatGroq:
    """
    Returns the complex reasoning model.
    Switched to Groq (Llama 3.3) because the Gemini free-tier quota was exhausted.
    """
    return ChatGroq(
        api_key=settings.GROQ_API_KEY,
        model_name="llama-3.3-70b-versatile",
        temperature=0.2,
    )
