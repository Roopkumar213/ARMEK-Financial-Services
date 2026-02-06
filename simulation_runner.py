import json
import random
import time
import os
import sys
import matplotlib.pyplot as plt
import pandas as pd
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict

# Add backend to path so we can import models/workers
sys.path.append(os.path.join(os.getcwd(), 'backend'))

try:
    from models import SessionState, AgentAction, WorkerResponse, CustomerProfile
    from workers import EligibilityAgent, CreditBureauAgent, KYCAgent, DocumentAgent, StateReconciliationAgent
except ImportError:
    print("ERROR: Could not import backend modules. Make sure 'backend' folder exists in current directory.")
    sys.exit(1)

# ==========================================
# 1. DETERMINISTIC BRAIN (MOCK LLM)
# ==========================================
class DeterministicBrain:
    """
    Replaces the LLM for high-speed, cost-free testing.
    Follows the EXACT finite state machine meant for the Master Agent.
    """
    def decide(self, session: SessionState) -> AgentAction:
        profile = session.profile
        
        # 1. ELIGIBILITY FIRST (Safe Default)
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
            else:
                return AgentAction(type="ASK_USER", user_message="Income?", reasoning="Need details")

        # 2. FRAUD/CREDIT (If Eligible)
        if not session.credit_bureau_checked:
            # We assume user provided PAN if asked (simulated)
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
            else:
                 return AgentAction(type="ASK_USER", user_message="PAN?", reasoning="Need PAN")

        # 3. KYC (If Credit Safe)
        if not session.kyc_verified:
            return AgentAction(
                type="CALL_WORKER",
                worker_name="KYCAgent",
                worker_inputs={"pan": profile.pan, "name": profile.name},
                reasoning="Verifying identity."
            )

        # 4. SANCTION (If Verified)
        if not session.sanction_generated:
            return AgentAction(
                type="CALL_WORKER",
                worker_name="DocumentAgent",
                worker_inputs={
                    "customer_name": profile.name,
                    "amount": session.profile.loan_amount, # Use approved amount in real logic
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
    category: str
    final_status: str # ACCEPTED, REJECTED
    rejection_stage: Optional[str] = None
    rejection_reason: Optional[str] = None
    agents_called: List[str] = None
    duration_ms: float = 0
    fraud_flag: bool = False

class SimulationRunner:
    def __init__(self):
        self.brain = DeterministicBrain()
        self.eligibility = EligibilityAgent()
        self.credit = CreditBureauAgent()
        self.kyc = KYCAgent()
        self.doc = DocumentAgent()
        self.results: List[SimResult] = []

    def run_user(self, user_profile: Dict[str, Any], category: str) -> SimResult:
        start_time = time.time()
        
        # Init Session
        session = SessionState(session_id=user_profile["id"])
        # Inject Initial User Data (Simulating conversation extraction)
        session.profile.name = user_profile["name"]
        session.profile.monthly_income = user_profile["income"]
        session.profile.existing_emi = user_profile["existing_emi"]
        session.profile.loan_amount = user_profile["loan_amount"]
        session.profile.tenure_months = 12
        session.profile.pan = user_profile["pan"]
        
        agents_called = []
        status = "IN_PROGRESS"
        rejection_stage = None
        rejection_reason = None
        
        # MAX STEPS TO PREVENT INFINITE LOOPS
        for _ in range(10):
            action = self.brain.decide(session)
            
            if action.type == "TERMINATE":
                status = "ACCEPTED"
                break
                
            if action.type == "CALL_WORKER":
                worker = action.worker_name
                agents_called.append(worker)
                
                # Execute Logic
                inputs = action.worker_inputs
                result = None
                
                if worker == "EligibilityAgent":
                    result = self.eligibility.check_eligibility(
                        inputs["income"], inputs["existing_emi"], inputs["loan_amount"], inputs["tenure_months"]
                    )
                    session.eligibility_run = True # Brain update
                    
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

                # Handle Result
                if not result.success:
                    if result.system_instruction == "REJECT_USER" or result.system_instruction == "FLAG_FRAUD":
                        status = "REJECTED"
                        rejection_stage = worker
                        rejection_reason = result.error_message
                        break # Stop processing this user
        
        duration = (time.time() - start_time) * 1000
        
        return SimResult(
            user_id=user_profile["id"],
            category=category,
            final_status=status,
            rejection_stage=rejection_stage,
            rejection_reason=rejection_reason,
            agents_called=agents_called,
            duration_ms=duration,
            fraud_flag=(rejection_stage == "CreditBureauAgent")
        )

    def generate_users(self, count=1000):
        users = []
        categories = {
            "Eligible": 0.35, "Borderline": 0.20, "Ineligible": 0.25, "Fraud": 0.15, "Edge": 0.05
        }
        
        for cat, ratio in categories.items():
            limit = int(count * ratio)
            for i in range(limit):
                u = {"id": f"{cat}_{i}", "name": f"User_{cat}_{i}"}
                
                # Default Good
                u["income"] = 75000
                u["existing_emi"] = 10000
                u["loan_amount"] = 500000
                u["pan"] = f"ABCDE{random.randint(1000,9999)}F"
                
                if cat == "Ineligible":
                    u["income"] = 15000 # Too low
                elif cat == "Borderline":
                    u["existing_emi"] = 40000 # High FOIR
                elif cat == "Fraud":
                    u["pan"] = f"VWXYZ{random.randint(1000,9999)}A" # Flag trigger
                    if "88" not in u["pan"]: u["pan"] = u["pan"][:-3] + "88" + u["pan"][-1]
                elif cat == "Edge":
                    u["pan"] = "INVALIDFORMAT"
                    
                users.append((u, cat))
                
        return users

# ==========================================
# 3. REPORTING
# ==========================================
def generate_report(results: List[SimResult]):
    df = pd.DataFrame([asdict(r) for r in results])
    
    print("\n" + "="*40)
    print("SIMULATION REPORT")
    print("="*40)
    print(f"Total Users: {len(df)}")
    print(f"Accepted: {len(df[df['final_status']=='ACCEPTED'])}")
    print(f"Rejected: {len(df[df['final_status']=='REJECTED'])}")
    
    # 1. Rejection By Stage (Pie Chart)
    rejected = df[df['final_status']=='REJECTED']
    if not rejected.empty:
        stage_counts = rejected['rejection_stage'].value_counts()
        print("\nRejection Breakdown:")
        print(stage_counts)
        
        plt.figure(figsize=(10, 6))
        stage_counts.plot(kind='pie', autopct='%1.1f%%', title='Rejection Distribution by Agent')
        plt.ylabel('')
        plt.savefig('rejection_breakdown.png')
        print("Generated: rejection_breakdown.png")

    # 2. Acceptance by Category (Bar Chart)
    ct = pd.crosstab(df['category'], df['final_status'])
    print("\nOutcomes by Category:")
    print(ct)
    
    ct.plot(kind='bar', stacked=True, figsize=(10, 6), color=['green', 'red'])
    plt.title('Outcome by User Category')
    plt.xlabel('User Category')
    plt.ylabel('Count')
    plt.savefig('outcome_by_category.png')
    print("Generated: outcome_by_category.png")

    # 3. Efficiency Metric
    avg_agents = df['agents_called'].apply(len).mean()
    print(f"\nAvg Agents per User: {avg_agents:.2f}")
    
    # Cost Analysis
    # Assumption: Eligibility=Free, KYC/Credit=$1
    df['simulated_cost'] = df['agents_called'].apply(
        lambda x: sum([1 for a in x if a in ['CreditBureauAgent', 'KYCAgent', 'DocumentAgent']])
    )
    total_cost = df['simulated_cost'].sum()
    print(f"Total Simulated API Cost (Units): {total_cost}")
    
    # Savings: If we had no eligibility check, everyone would hit Credit/KYC
    # Theoretical Max Cost = 1000 * 3 (Credit + KYC + Docs potentially)
    # But Ineligible users (250) would normally be rejected at Credit or never? 
    # Actually, without eligibility, we'd run Credit/KYC on everyone.
    saved = (len(df) * 2) - total_cost # Roughly assuming Credit+KYC avoided for rejected
    print(f"Estimated Backend Calls Saved: {saved}")

if __name__ == "__main__":
    runner = SimulationRunner()
    print("Generating Synthetic Users...")
    users = runner.generate_users(1000)
    
    print(f"Running Simulation for {len(users)} users...")
    results = []
    for u, cat in users:
        results.append(runner.run_user(u, cat))
        
    generate_report(results)
