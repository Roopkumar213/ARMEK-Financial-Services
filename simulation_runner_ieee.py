import json
import time
import sys
import os
import matplotlib.pyplot as plt
import pandas as pd
from typing import List
from dataclasses import dataclass, asdict

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

try:
    from models import SessionState, AgentAction, WorkerResponse
    from workers import EligibilityAgent, CreditBureauAgent, KYCAgent, DocumentAgent
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
                    reasoning="Eligibility check first."
                )
            return AgentAction(type="ASK_USER", reason="Income?")

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
            return AgentAction(type="ASK_USER", reason="PAN?")

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
# 2. IEEE HARNESS
# ==========================================
@dataclass
class SimResult:
    user_id: str
    credit_segment: str # Prime, Subprime
    final_status: str 
    rejection_stage: str = None
    rejection_reason: str = None
    is_fraud_simulation: bool = False
    fraud_detected: bool = False
    fraud_score: int = 0

class SimulationRunnerIEEE:
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
        session.profile.tenure_months = user_data["tenure_months"]
        session.profile.pan = user_data["pan"]
        
        status = "IN_PROGRESS"
        rejection_stage = None
        rejection_reason = None
        fraud_score = 0
        
        for _ in range(8): # Loop limit
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
                    fraud_score = result.risk_score
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
                    if "REJECT" in (result.system_instruction or "") or "FLAG" in (result.system_instruction or ""):
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
            is_fraud_simulation=user_data["metadata"]["is_fraud"],
            fraud_detected=(rejection_stage == "CreditBureauAgent" and fraud_score >= 50),
            fraud_score=fraud_score
        )

# ==========================================
# 3. REPORTING
# ==========================================
def generate_ieee_report(results: List[SimResult]):
    df = pd.DataFrame([asdict(r) for r in results])
    
    print("\n" + "="*50)
    print("IEEE CONFERENCE VALIDATION REPORT (1,000 Users)")
    print("="*50)
    
    # 1. Overall
    total = len(df)
    accepted = len(df[df['final_status']=='ACCEPTED'])
    rejected = len(df[df['final_status']=='REJECTED'])
    print(f"Total N: {total}")
    print(f"Accepted: {accepted} ({accepted/total*100:.1f}%)")
    print(f"Rejected: {rejected} ({rejected/total*100:.1f}%)")
    
    # 2. Fraud Efficacy
    fraud_sims = df[df['is_fraud_simulation']==True]
    detected = fraud_sims[fraud_sims['fraud_detected']==True]
    
    print("\n[FRAUD DETECTION]")
    print(f"Injected Anomalies: {len(fraud_sims)}")
    print(f"Correctly Detected: {len(detected)}")
    print(f"Sensitivity (Recall): {len(detected)/len(fraud_sims)*100:.2f}%")
    
    # 3. False Positive Rate (Honest users flagged as fraud)
    honest = df[df['is_fraud_simulation']==False]
    false_flags = honest[honest['fraud_detected']==True]
    print(f"Honest Users Flagged: {len(false_flags)}")
    print(f"False Positive Rate: {len(false_flags)/len(honest)*100:.2f}%")
    
    # Graphs
    # A. Conf Matrix
    import numpy as np
    tp = len(detected)
    fn = len(fraud_sims) - tp
    fp = len(false_flags)
    tn = len(honest) - fp
    
    print(f"\nConfusion Matrix:\nTP={tp}\tFP={fp}\nFN={fn}\tTN={tn}")

    plt.figure(figsize=(6, 6))
    plt.pie([tp, fn], labels=[f'Detected ({tp})', f'Missed ({fn})'], autopct='%1.1f%%', colors=['#22c55e', '#ef4444'])
    plt.title('Fraud Sensitivity (Target > 85%)')
    plt.savefig('ieee_fraud_sensitivity.png')

if __name__ == "__main__":
    with open("ieee_grounded_users.json", "r") as f:
        users = json.load(f)
        
    runner = SimulationRunnerIEEE()
    results = []
    
    # Batch Run
    start = time.time()
    for u in users:
        results.append(runner.run_user(u))
    end = time.time()
    
    print(f"Simulation Time: {end-start:.2f}s")
    generate_ieee_report(results)
