# main.py
import logging
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Dict, Any, Optional

from orchestrator import MasterAgent
from models import SessionState, CustomerProfile

# ---------- Setup ----------
logging.basicConfig(level=logging.INFO)
app = FastAPI(title="ARMEK Agentic Loan Platform")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/generated_letters", StaticFiles(directory="generated_letters"), name="generated_letters")

# ---------- Singleton Agents ----------
master_agent = MasterAgent()
SESSIONS: Dict[str, SessionState] = {}

# ---------- API Models ----------
class ChatRequest(BaseModel):
    session_id: str
    message: str

class ChatResponse(BaseModel):
    reply: str
    ui_action: Optional[str] = None
    data: Optional[Dict[str, Any]] = None

# ---------- Endpoints ----------

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    # 1. Retrieve or Create Session
    if req.session_id not in SESSIONS:
        SESSIONS[req.session_id] = SessionState(session_id=req.session_id)
    
    session = SESSIONS[req.session_id]
    
    # 2. Run Master Agent
    # The Master Agent handles the entire Think-Act-Observe loop
    result = master_agent.run_step(session, req.message)
    
    # 3. Handle UI Actions (Reset, etc)
    if result.get("ui_action") == "RESET_UI":
        SESSIONS[req.session_id] = SessionState(session_id=req.session_id) # Hard reset
    
    # 4. Return Response
    return ChatResponse(
        reply=result.get("reply", ""),
        ui_action=result.get("ui_action"),
        data=result.get("data")
    )

@app.get("/session/{session_id}")
async def get_session_state(session_id: str):
    """Debug endpoint to see the Agent's brain."""
    if session_id not in SESSIONS:
        return {"error": "Session not found"}
    return SESSIONS[session_id].dict()

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
