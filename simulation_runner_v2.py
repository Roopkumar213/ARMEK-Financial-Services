import json
import time
import sys
import os
import matplotlib.pyplot as plt
import pandas as pd
from typing import List
from dataclasses import dataclass, asdict

# Add backend to path so we can import models/workers
sys.path.append(os.path.join(os.getcwd(), 'backend'))

try:
    from models import SessionState, AgentAction, WorkerResponse, CustomerProfile
    from workers import EligibilityAgent, CreditBureauAgent, KYCAgent, DocumentAgent, StateReconciliationAgent
except ImportError:
    print("ERROR: Could not import backend modules.")
    sys.exit(1)

# ==========================================
# 1. DETERMINISTIC BRAIN (Mock LLM)
# ==========================================
class DeterministicBrain:
    def decide(self, session: SessionState) -> AgentAction:
        profile = session.profile
        
        # 1. ELIGIBILITY FIRST
        if not session.eligibility_run:
            if profile.monthly_income and profile.loan_amount:
                return AgentAction(
                    type="CALL_WORKER",
                    worker_name="EligibilityAgent",
                    worker_inputs={
                        "income": profile.monthly_income, 
                        "existing_emi": profile.existing_emi or 0, 
                        "loan_amount": profile.loan_amount, 
                        "tenure_months": profile.tenure_months or 12
                    },
                    reasoning="Eligibility check required first."
                )
            return AgentAction(type="ASK_USER", user_message="Income?", reasoning="Need details")

        # 2. FRAUD/CREDIT
        if not session.credit_bureau_checked:
            if profile.pan:
                return AgentAction(
                    type="CALL_WORKER",
                    worker_name="CreditBureauAgent",
                    worker_inputs={
                        "pan": profile.pan,
                        "stated_income": profile.monthly_income,
                        "stated_emi": profile.existing_emi or 0
                    },
                    reasoning="Checking fraud before KYC."
                )
            return AgentAction(type="ASK_USER", user_message="PAN?", reasoning="Need PAN")

        # 3. KYC
        if not session.kyc_verified:
            return AgentAction(
                type="CALL_WORKER",
                worker_name="KYCAgent",
                worker_inputs={"pan": profile.pan, "name": profile.name},
                reasoning="Verifying identity."
            )

        # 4. SANCTION
        if not session.sanction_generated:
            return AgentAction(
                type="CALL_WORKER",
                worker_name="DocumentAgent",
                worker_inputs={
                    "customer_name": profile.name,
                    "amount": session.profile.loan_amount,
                    "tenure": session.profile.tenure_months
                },
                reasoning="Generating Sanction Letter."
            )

        # 5. DONE
        return AgentAction(type="TERMINATE", user_message="Done", reasoning="Process Complete")

# ==========================================
# 2. SIMULATION HARNESS
# ==========================================
@dataclass
class SimResult:
    user_id: str
    credit_segment: str # Prime, Subprime, etc
    final_status: str 
    rejection_stage: str = None
    rejection_reason: str = None
    is_fraud_simulation: bool = False
    fraud_detected: bool = False

class SimulationRunnerV2:
    def __init__(self):
        self.brain = DeterministicBrain()
        self.eligibility = EligibilityAgent()
        self.credit = CreditBureauAgent()
        self.kyc = KYCAgent()
        self.doc = DocumentAgent()

    def run_user(self, user_data) -> SimResult:
        # Init Session
        session = SessionState(session_id=user_data["id"])
        
        # Inject Profile Data
        session.profile.name = user_data["name"]
        session.profile.monthly_income = user_data["stated_income"]
        session.profile.existing_emi = user_data["existing_emi"]
        session.profile.loan_amount = user_data["loan_amount"]
        session.profile.tenure_months = 24
        session.profile.pan = user_data["pan"]
        
        status = "IN_PROGRESS"
        rejection_stage = None
        rejection_reason = None
        
        max_steps = 10
        for _ in range(max_steps):
            action = self.brain.decide(session)
            
            if action.type == "TERMINATE":
                status = "ACCEPTED"
                break
                
            if action.type == "CALL_WORKER":
                worker = action.worker_name
                inputs = action.worker_inputs
                
                # EXECUTE
                if worker == "EligibilityAgent":
                    result = self.eligibility.check_eligibility(
                        inputs["income"], inputs["existing_emi"], inputs["loan_amount"], inputs["tenure_months"]
                    )
                    session.eligibility_run = True
                elif worker == "CreditBureauAgent":
                    result = self.credit.check_bureau(
                        inputs["pan"], inputs["stated_income"], inputs["stated_emi"]
                    )
                    session.credit_bureau_checked = True
                elif worker == "KYCAgent":
                    result = self.kyc.verify_pan(inputs["pan"], inputs["name"])
                    session.kyc_verified = True
                elif worker == "DocumentAgent":
                    result = self.doc.generate_sanction_letter(
                        inputs["customer_name"], inputs["amount"], inputs["tenure"]
                    )
                    session.sanction_generated = True

                # HANDLE RESULT
                if not result.success:
                    if result.system_instruction in ["REJECT_USER", "FLAG_FRAUD"]:
                        status = "REJECTED"
                        rejection_stage = worker
                        rejection_reason = result.error_message
                        break
        
        return SimResult(
            user_id=user_data["id"],
            credit_segment=user_data["metadata"]["credit_segment"],
            final_status=status,
            rejection_stage=rejection_stage,
            rejection_reason=rejection_reason,
            is_fraud_simulation=user_data["is_fraud_simulation"],
            fraud_detected=(rejection_stage == "CreditBureauAgent" and "High Risk" in (rejection_reason or ""))
        )

# ==========================================
# 3. REPORTING
# ==========================================
def generate_report(results: List[SimResult]):
    df = pd.DataFrame([asdict(r) for r in results])
    
    print("\n" + "="*40)
    print("REAL-WORLD VALIDATION REPORT")
    print("="*40)
    
    # 1. Overall
    print(f"Total Users: {len(df)}")
    print(f"Accepted: {len(df[df['final_status']=='ACCEPTED'])}")
    print(f"Rejected: {len(df[df['final_status']=='REJECTED'])}")
    
    # 2. Fraud Analysis
    fraud_sims = df[df['is_fraud_simulation']==True]
    detected = fraud_sims[fraud_sims['fraud_detected']==True]
    print("\nFRAUD DETECTION STATS:")
    print(f"Simulated Fraud Cases: {len(fraud_sims)}")
    print(f"Detected Fraud: {len(detected)}")
    print(f"Detection Rate: {len(detected)/len(fraud_sims)*100:.1f}%")
    
    # 3. Rejection by Segment
    ct = pd.crosstab(df['credit_segment'], df['final_status'])
    print("\nOutcomes by Credit Segment:")
    print(ct)
    
    # Graphs
    plt.figure(figsize=(10, 6))
    ct.plot(kind='bar', stacked=True, color=['green', 'red'])
    plt.title('Approvals by Credit Segment (Real Data)')
    plt.ylabel('Count')
    plt.savefig('validation_outcomes.png')
    
    # Fraud Accuracy
    labels = ['Detected', 'Missed']
    sizes = [len(detected), len(fraud_sims)-len(detected)]
    plt.figure(figsize=(6, 6))
    plt.pie(sizes, labels=labels, autopct='%1.1f%%', colors=['#10b981', '#ef4444'])
    plt.title('Fraud Detection Efficiency')
    plt.savefig('validation_fraud.png')

if __name__ == "__main__":
    with open("grounded_users.json", "r") as f:
        users = json.load(f)
        
    runner = SimulationRunnerV2()
    results = []
    
    print(f"Validating {len(users)} real-world profiles...")
    for u in users:
        results.append(runner.run_user(u))
        
    generate_report(results)
