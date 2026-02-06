import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(override=True)

def get_llm_config():
    """
    Determines the best available LLM provider based on environment variables.
    Priority:
    1. Gemini (High Rate Limits, Free Tier)
    2. Groq (Fast, Free Tier)
    3. OpenAI (Standard)
    """
    
    # Check for Gemini
    if os.getenv("GEMINI_API_KEY"):
        return {
            "provider": "gemini",
            "api_key": os.getenv("GEMINI_API_KEY"),
            "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
            "model": "gemini-flash-latest", 
            "timeout": 30
        }
    
    # Check for Groq
    elif os.getenv("GROQ_API_KEY"):
        return {
            "provider": "groq",
            "api_key": os.getenv("GROQ_API_KEY"),
            "base_url": "https://api.groq.com/openai/v1",
            "model": "llama3-8b-8192", # Fast and cheap
            "timeout": 30
        }

    # Fallback to OpenAI
    else:
        return {
            "provider": "openai",
            "api_key": os.getenv("OPENAI_API_KEY"),
            "base_url": None, # Default
            "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            "timeout": int(os.getenv("OPENAI_TIMEOUT_SECONDS", "30"))
        }

# Singleton Configuration
CONFIG = get_llm_config()

print(f"🚀 LLM Provider Initialized: {CONFIG['provider'].upper()} using model {CONFIG['model']}")

def get_llm_client():
    """Returns a configured OpenAI Client (compatible with Gemini/Groq)"""
    return OpenAI(
        api_key=CONFIG["api_key"],
        base_url=CONFIG["base_url"],
        timeout=CONFIG["timeout"]
    )

LLM_MODEL = CONFIG["model"]
