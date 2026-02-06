# orchestrator.py
import os
import json
import logging
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from llm_factory import get_llm_client, LLM_MODEL

from models import SessionState, AgentAction, WorkerResponse, CustomerProfile
from workers import EligibilityAgent, CreditBureauAgent, KYCAgent, DocumentAgent, StateReconciliationAgent

load_dotenv()
client = get_llm_client()

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
You must respond with a JSON object adhering to this EXACT schema:
{
  "type": "CALL_WORKER" | "ASK_USER" | "TERMINATE" | "RESET",
  "worker_name": "EligibilityAgent" | "CreditBureauAgent" | "KYCAgent" | ... (Required if type is CALL_WORKER),
  "worker_inputs": { ... dictionary of inputs ... },
  "user_message": "...",
  "reasoning": "..."
}

DO NOT use "action_type", "parameters", or "tool_call". Use "type", "worker_name", and "worker_inputs".

Example:
{
  "type": "CALL_WORKER",
  "worker_name": "EligibilityAgent",
  "worker_inputs": {"income": 50000, "existing_emi": 5000, "loan_amount": 100000, "tenure_months": 12},
  "reasoning": "Checking eligibility."
}
OR
{
  "type": "ASK_USER",
  "user_message": "Please provide your PAN number for verification.",
  "reasoning": "Eligibility passed, now proceeding to KYC."
}

# COMMON SCENARIOS
Input: "Start Application. My name is Foo, income 50000..."
Action:
{
  "type": "CALL_WORKER",
  "worker_name": "EligibilityAgent",
  "worker_inputs": {"income": 50000, ...},
  "reasoning": "New application detected. Checking eligibility."
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
        
        # --- PARAMETER MAPPING LAYER ---
        # Maps LLM-generated keys to Python-argument keys
        mapped_inputs = inputs.copy()
        
        # 1. Eligibility Mappings
        if "monthly_income" in inputs: mapped_inputs["income"] = inputs["monthly_income"]
        if "loan_duration_months" in inputs: mapped_inputs["tenure_months"] = inputs["loan_duration_months"]
        if "tenure" in inputs: mapped_inputs["tenure_months"] = inputs["tenure"]

        # 2. Credit/KYC Mappings
        if "pan_number" in inputs: mapped_inputs["pan"] = inputs["pan_number"]
        if "user_name" in inputs: mapped_inputs["name"] = inputs["user_name"]
        
        # 3. Document Mappings
        if "customer_name" not in inputs and "name" in inputs: mapped_inputs["customer_name"] = inputs["name"]

        # --- EXECUTION ---
        if name == "EligibilityAgent":
            return self.eligibility_agent.check_eligibility(
                mapped_inputs.get("income"), mapped_inputs.get("existing_emi"), 
                mapped_inputs.get("loan_amount"), mapped_inputs.get("tenure_months")
            )
        elif name == "CreditBureauAgent":
            return self.credit_agent.check_bureau(
                mapped_inputs.get("pan"), mapped_inputs.get("stated_income"), mapped_inputs.get("stated_emi")
            )
        elif name == "KYCAgent":
            return self.kyc_agent.verify_pan(mapped_inputs.get("pan"), mapped_inputs.get("name"))
        elif name == "DocumentAgent":
            return self.doc_agent.generate_sanction_letter(
                mapped_inputs.get("customer_name"), mapped_inputs.get("amount"), mapped_inputs.get("tenure")
            )
        elif name == "StateReconciliationAgent":
             return self.reconciler.reconcile(session.profile.dict(), mapped_inputs)
        
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
            {"role": "user", "content": user_input},
            {"role": "system", "content": "IMPORTANT: You are an agent. Respond ONLY with a valid JSON object matching the AgentAction schema. Do not output markdown. Do not echo the state."}
        ]

    def _clean_json(self, content: str) -> str:
        """Removes markdown code blocks if present."""
        content = content.strip()
        if content.startswith("```"):
            # Find the first newline to skip "```json"
            first_newline = content.find("\n")
            if first_newline != -1:
                content = content[first_newline+1:]
            # Remove trailing "```"
            if content.endswith("```"):
                content = content[:-3]
        return content.strip()

    def _chat_with_llm(self, messages: List[Dict[str, str]]) -> AgentAction:
        try:
            response = client.chat.completions.create(
                model=LLM_MODEL,
                messages=messages,
                response_format={"type": "json_object"}
            )
            content = response.choices[0].message.content
            cleaned_content = self._clean_json(content)
            logging.info(f"raw_llm_response: {cleaned_content}")

            # --- UNIVERSAL REPAIR STRATEGY ---
            try:
                data = json.loads(cleaned_content)
                normalized = {}

                # 1. SEARCH FOR TYPE/ACTION
                # We look for *any* key that looks like an action identifier
                type_candidates = ["type", "action_type", "action", "function", "tool_call", "call"]
                found_type = None
                for key in type_candidates:
                    if key in data:
                        found_type = data[key]
                        break
                
                # 2. SEARCH FOR INPUTS/ARGS
                # We look for *any* key that looks like inputs
                input_candidates = ["worker_inputs", "inputs", "parameters", "arguments", "action_arguments", "args", "data"]
                found_inputs = {}
                for key in input_candidates:
                    if key in data:
                        found_inputs = data[key]
                        break
                
                # 3. NORMALIZE VALUES
                if found_type:
                    # Map common hallucinations to internal names
                    ft_lower = str(found_type).lower()
                    if ft_lower in ["start_application", "initiate_application", "check_eligibility", "eligibility_check"]:
                        normalized["type"] = "CALL_WORKER"
                        normalized["worker_name"] = "EligibilityAgent"
                    elif "kyc" in ft_lower or "verify" in ft_lower:
                        normalized["type"] = "CALL_WORKER"
                        normalized["worker_name"] = "KYCAgent"
                    elif "credit" in ft_lower or "bureau" in ft_lower:
                        normalized["type"] = "CALL_WORKER"
                        normalized["worker_name"] = "CreditBureauAgent"
                    elif "tool_call" in ft_lower or "call_worker" in ft_lower:
                        normalized["type"] = "CALL_WORKER"
                        # Start looking for worker name in inputs if not found
                        if "action_name" in data:
                            normalized["worker_name"] = data["action_name"]
                    else:
                        normalized["type"] = found_type
                
                # 4. Fallback for "worker_name" if missing in normalization
                if normalized.get("type") == "CALL_WORKER" and "worker_name" not in normalized:
                    # Try to find it in the original data
                     if "action_name" in data:
                         normalized["worker_name"] = data["action_name"]
                     elif "worker" in data:
                         normalized["worker_name"] = data["worker"]
                     else:
                         # Ultimate fallback
                         normalized["worker_name"] = "EligibilityAgent"

                # 5. Assign Inputs
                normalized["worker_inputs"] = found_inputs

                # 6. Ensure Reasoning
                if "reasoning" in data:
                    normalized["reasoning"] = data["reasoning"]
                else:
                    normalized["reasoning"] = f"Action inferred from {found_type}"

                # 7. Final Sanity Check
                if "type" not in normalized:
                     # One last ditch effort: if we have inputs like "monthly_income", it's probably eligibility
                     if "monthly_income" in str(found_inputs):
                         normalized["type"] = "CALL_WORKER"
                         normalized["worker_name"] = "EligibilityAgent"
                         normalized["reasoning"] = "Inferred Eligibility Check from inputs"
                     else:
                         normalized["type"] = "ASK_USER"
                         normalized["user_message"] = "I am processing your request..."
                
                logging.info(f"Normalized Action: {normalized}")
                return AgentAction.parse_obj(normalized)

            except json.JSONDecodeError:
                logging.error("Invalid JSON returned LLM")
                raise ValueError("LLM returned invalid JSON")

            except json.JSONDecodeError:
                logging.error("Invalid JSON returned LLM")
                raise ValueError("LLM returned invalid JSON")

        except Exception as e:
            logging.error(f"Failed to parse LLM response: {content if 'content' in locals() else 'No Content'}")
            # Fallback to a safe action instead of crashing
            return AgentAction(
                type="ASK_USER", 
                user_message="I clearly misunderstood. Could you re-state that?", 
                reasoning="Fallback on error."
            )
