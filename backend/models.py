# models.py
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field

# ==========================================
# 1. CORE DATA ENITIES
# ==========================================

class CustomerProfile(BaseModel):
    """Stores the raw customer data collected so far."""
    name: Optional[str] = None
    pan: Optional[str] = None
    monthly_income: Optional[float] = None
    existing_emi: Optional[float] = None
    loan_amount: Optional[float] = None
    tenure_months: Optional[int] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    
    # System Generated / Verified Data
    approved_amount: Optional[float] = None
    max_eligible_amount: Optional[float] = None
    monthly_emi: Optional[float] = None
    cibil_score: Optional[int] = None
    verified_name: Optional[str] = None

class RiskFlags(BaseModel):
    """Tracks fraud and risk signals."""
    income_discrepancy: bool = False
    fake_data_detected: bool = False
    bureau_mismatch: bool = False
    high_foir: bool = False
    policy_rejection: bool = False
    rejection_reason: Optional[str] = None

class SessionState(BaseModel):
    """The Single Source of Truth for the Master Agent."""
    session_id: str
    stage: str = "INIT"  # INIT, DETAILS, ELIGIBILITY, KYC, SANCTION, REJECTED
    profile: CustomerProfile = Field(default_factory=CustomerProfile)
    risk: RiskFlags = Field(default_factory=RiskFlags)
    conversation_history: List[Dict[str, str]] = Field(default_factory=list)
    
    # Internal flags to track worker execution
    eligibility_run: bool = False
    kyc_verified: bool = False
    credit_bureau_checked: bool = False
    sanction_generated: bool = False
    sanction_url: Optional[str] = None

# ==========================================
# 2. AGENT COMMUNICATION SCHEMAS
# ==========================================

class AgentAction(BaseModel):
    """
    STRICT CONTRACT: The Master Agent MUST output this structure.
    """
    type: Literal["CALL_WORKER", "ASK_USER", "TERMINATE", "RECALCULATE", "RESET"]
    worker_name: Optional[Literal[
        "EligibilityAgent", 
        "CreditBureauAgent", 
        "KYCAgent", 
        "StateReconciliationAgent", 
        "DocumentAgent"
    ]] = None
    worker_inputs: Optional[Dict[str, Any]] = None
    user_message: Optional[str] = None
    reasoning: str = Field(..., description="Why did you choose this action?")
    
    # Constraints for safety
    next_constraints: List[str] = Field(default_factory=list)

class WorkerResponse(BaseModel):
    """Standardized output from any Worker Agent."""
    success: bool
    data: Optional[Dict[str, Any]] = None
    risk_score: int = 0  # 0-100 (0 = Safe, 100 = Fraud)
    error_message: Optional[str] = None
    system_instruction: Optional[str] = None  # Instruction to Master Agent (e.g. "Reject User")
