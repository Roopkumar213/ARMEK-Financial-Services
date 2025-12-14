# agents.py
"""
Master Agent (Language Layer Only)

Responsibilities:
- Human-like conversation
- Polite, sales-oriented phrasing
- Clarifications and soft nudges
- NO control flow
- NO business logic
- NO tool execution
- NO internal leakage

Acts as the single conversational face of the NBFC.
"""

import os
import asyncio
from typing import List, Dict, Any

from openai import OpenAI
from dotenv import load_dotenv

# ---------- Setup ----------
load_dotenv(override=True)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_TIMEOUT_SECONDS = int(os.getenv("OPENAI_TIMEOUT_SECONDS", "30"))

client = OpenAI(api_key=OPENAI_API_KEY)

# ---------- System Prompt ----------
SYSTEM_PROMPT = """
You are a professional digital sales assistant for a large NBFC in India,
specializing in personal loans.

Your role:
- Speak clearly, politely, and confidently
- Sound like a trained human loan sales executive
- Guide customers step by step
- Acknowledge inputs and ask for the next required detail

Strict rules:
- Never mention internal systems, checks, agents, tools, or logic
- Never mention words like verification, eligibility engine, FOIR, model, API, or JSON
- Never output structured data, bullet-point internals, or technical explanations
- Never contradict the system’s decisions
- If unsure, politely ask the customer to provide the requested information

Your responses are shown directly to customers.
"""

# ---------- Master Agent ----------
async def run_master_agent(
    session_id: str,
    current_stage: str,
    history: List[Dict[str, str]],
    user_message: str,
) -> Dict[str, Any]:
    """
    Generates a natural-language response only.
    Control flow and decisions are handled elsewhere.
    """

    messages: List[Dict[str, str]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "system", "content": f"Conversation stage: {current_stage}"},
    ]

    # Include recent conversational history
    for m in history[-12:]:
        if m.get("role") in ("user", "assistant") and m.get("content"):
            messages.append(
                {"role": m["role"], "content": m["content"]}
            )

    messages.append({"role": "user", "content": user_message})

    try:
        response = await asyncio.to_thread(
            lambda: client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=messages,
                temperature=0.6,
                max_tokens=220,
                timeout=OPENAI_TIMEOUT_SECONDS,
            )
        )
        reply = (response.choices[0].message.content or "").strip()
    except Exception:
        reply = ""

    # ---------- HARD SAFETY & LEAKAGE FILTER ----------
    forbidden_phrases = [
        "{", "}", "[", "]",
        "verify", "verification",
        "eligibility", "engine",
        "tool", "agent", "worker",
        "json", "api", "system",
        "foir", "risk band"
    ]

    if (
        not reply
        or any(term in reply.lower() for term in forbidden_phrases)
        or len(reply) < 5
    ):
        reply = (
            "Thank you. Please share the requested details so I can continue "
            "assisting you with your loan application."
        )

    return {
        "assistant_reply": reply
    }
