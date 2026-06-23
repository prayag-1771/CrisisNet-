from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.config import settings

def get_fast_llm():
    """
    Returns the fast inference model (Groq) used for classification, 
    routing, and latency-sensitive steps.
    """
    return ChatGroq(
        api_key=settings.GROQ_API_KEY,
        model_name="llama3-70b-8192",
        temperature=0.0 # Deterministic output for classification
    )

def get_reasoning_llm():
    """
    Returns the complex reasoning model (Gemini) used for 
    response generation and pattern analysis.
    """
    return ChatGoogleGenerativeAI(
        google_api_key=settings.GEMINI_API_KEY,
        model="gemini-1.5-pro",
        temperature=0.2 
    )
