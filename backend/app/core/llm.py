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
        model_name="llama3-70b-8192",
        temperature=0.0,  # Deterministic output for classification
    )


@lru_cache(maxsize=1)
def get_reasoning_llm() -> ChatGoogleGenerativeAI:
    """
    Returns the complex reasoning model (Gemini 1.5 Pro) used for
    response generation and pattern analysis.

    Cached so we don't create a new client on every node invocation.
    """
    return ChatGoogleGenerativeAI(
        google_api_key=settings.GEMINI_API_KEY,
        model="gemini-1.5-pro",
        temperature=0.2,
    )
