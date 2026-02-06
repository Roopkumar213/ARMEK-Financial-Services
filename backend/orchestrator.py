# orchestrator.py
import os
import json
import logging
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from openai import OpenAI

from models import SessionState, AgentAction, WorkerResponse, CustomerProfile
from workers import EligibilityAgent, CreditBureauAgent, KYCAgent, DocumentAgent, StateReconciliationAgent

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

# ==========================================
# SYSTEM PROMPT
# ==========================================
SYSTEM_PROMPT = """
You are the Master Agent for ARMEK Financial Services.
You orchestrate the loan application process.

# YOUR GOAL
Guide the user from application to sanction efficiently and safely.

# AVAILABLE WORKERS (TOOLS)
1. EligibilityAgent: Checks FOIR and Income rules. INPUTS: income, existing_emi, loan_amount, tenure_months.
2. CreditBureauAgent: Checks simplified Credit Score & Fraud. INPUTS: pan, stated_income, stated_emi.
3. KYCAgent: Verifies PAN format/existence. INPUTS: pan, name.
4. DocumentAgent: Generates Sanction Letter. INPUTS: customer_name, amount, tenure.
5. StateReconciliationAgent: Checks data consistency. INPUTS: old_profile, new_inputs.

# CRITICAL RULES (NON-NEGOTIABLE)
1. **EARLY ELIGIBILITY**: You MUST run `EligibilityAgent` immediately after getting Income, EMI, and Loan Amount. Do NOT ask for PAN or KYC before this check passes.
2. **FRAUD DEFENSE**: You MUST run `CreditBureauAgent` if the user is Eligible and has provided a PAN. If it flags fraud, REJECT.
3. **TRUST BOUNDARY**: You CANNOT calculate eligibility, EMI, or credit scores yourself. YOU MUST USE THE WORKERS.
4. **NO HALLUCINATIONS**: Do not make up approval numbers. Use exactly what the Worker returned.
5. **RESET**: If the user wants to restart, use action type "RESET".

# RESPONSE FORMAT
You must respond with a JSON object adhering to the AgentAction schema.
Example:
{
  "type": "CALL_WORKER",
  "worker_name": "EligibilityAgent",
  "worker_inputs": {"income": 50000, "existing_emi": 5000, "loan_amount": 100000, "tenure_months": 12},
  "reasoning": "User provided financial details, checking eligibility first as per protocol."
}
OR
{
  "type": "ASK_USER",
  "user_message": "Please provide your PAN number for verification.",
  "reasoning": "Eligibility passed, now proceeding to KYC."
}
"""

class MasterAgent:
    def __init__(self):
        self.eligibility_agent = EligibilityAgent()
        self.credit_agent = CreditBureauAgent()
        self.kyc_agent = KYCAgent()
        self.doc_agent = DocumentAgent()
        self.reconciler = StateReconciliationAgent()

    def run_step(self, session: SessionState, user_input: str) -> Dict[str, Any]:
        """
        Executes one 'turn' of the conversation.
        May involve multiple internal Agent loops (Think -> Worker -> Think).
        """
        
        # 1. Update State with obvious extractions (Simple parsing can happen here or LLM can do it)
        # For robustness, we let the LLM extract the data into 'worker_inputs' and we update the profile from there.
        
        # 2. Logic Loop
        max_steps = 5
        steps = 0
        
        while steps < max_steps:
            steps += 1
            
            # Prepare Context
            context = self._build_context(session, user_input)
            
            # ASK LLM
            try:
                action = self._chat_with_llm(context)
            except Exception as e:
                logging.error(f"LLM Error: {e}")
                return {"reply": "System Error: Brain freeze. Please try again.", "ui_action": None}

            logging.info(f"Agent Decided: {action.type} - {action.reasoning}")

            if action.type == "ASK_USER":
                return {
                    "reply": action.user_message,
                    "ui_action": "UPDATE_DASHBOARD",
                    "data": {"state": session.dict()}
                }

            elif action.type == "RESET":
                # Special Reset
                session.stage = "INIT"
                session.profile = CustomerProfile()
                session.risk = None
                return {
                    "reply": "I have reset your application. Let's start over.",
                    "ui_action": "RESET_UI",
                    "data": {"state": session.dict()}
                }
            
            elif action.type == "TERMINATE":
                 return {
                    "reply": action.user_message or "Thank you.",
                    "ui_action": "TERMINATE",
                    "data": {"state": session.dict()}
                }

            elif action.type == "CALL_WORKER":
                result = self._execute_worker(action, session)
                
                # Update State with Worker Result
                self._update_state_from_worker(session, action.worker_name, result)
                
                # ADD result to context for next loop iteration
                # We do this by appending to a temporary "scratchpad" or just relying on the updated session state
                # For this implementation, the updated session state is the memory.
                
                if not result.success and result.system_instruction == "REJECT_USER":
                     # Immediate rejection path
                     session.stage = "REJECTED"
                     return {
                         "reply": f"Application Rejected. Reason: {result.error_message}",
                         "ui_action": "SHOW_REJECTION",
                         "data": {"reason": result.error_message, "state": session.dict()}
                     }
                
                # Continue loop -> LLM sees updated state -> decides next step
                user_input = "System Note: Worker executed successfully." # Dummy input for next loop

        return {"reply": "I'm thinking too hard. Let's pause.", "ui_action": None}

    def _execute_worker(self, action: AgentAction, session: SessionState) -> WorkerResponse:
        inputs = action.worker_inputs or {}
        name = action.worker_name
        
        if name == "EligibilityAgent":
            return self.eligibility_agent.check_eligibility(
                inputs.get("income"), inputs.get("existing_emi"), 
                inputs.get("loan_amount"), inputs.get("tenure_months")
            )
        elif name == "CreditBureauAgent":
            return self.credit_agent.check_bureau(
                inputs.get("pan"), inputs.get("stated_income"), inputs.get("stated_emi")
            )
        elif name == "KYCAgent":
            return self.kyc_agent.verify_pan(inputs.get("pan"), inputs.get("name"))
        elif name == "DocumentAgent":
            return self.doc_agent.generate_sanction_letter(
                inputs.get("customer_name"), inputs.get("amount"), inputs.get("tenure")
            )
        elif name == "StateReconciliationAgent":
             return self.reconciler.reconcile(session.profile.dict(), inputs)
        
        return WorkerResponse(success=False, error_message="Unknown Worker")

    def _update_state_from_worker(self, session: SessionState, worker_name: str, result: WorkerResponse):
        # Update Profile Data if successful and relevant
        if result.success and result.data:
            # Merging logic - simplified
            if "approved_amount" in result.data:  session.profile.loan_amount = result.data["approved_amount"]
            # etc...

        # Update Flags
        if worker_name == "EligibilityAgent":
            session.eligibility_run = True
        elif worker_name == "KYCAgent" and result.success:
            session.kyc_verified = True
        elif worker_name == "CreditBureauAgent":
            session.credit_bureau_checked = True
        
        # Store Risk
        if result.risk_score > 50:
            session.risk.fake_data_detected = True

    def _build_context(self, session: SessionState, user_input: str) -> List[Dict[str, str]]:
        state_dump = session.json()
        return [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "system", "content": f"CURRENT STATE: {state_dump}"},
            {"role": "user", "content": user_input}
        ]

    def _chat_with_llm(self, messages: List[Dict[str, str]]) -> AgentAction:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        return AgentAction.parse_raw(content)
