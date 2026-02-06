import json
import csv
import sys
import os
import time
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

try:
    from models import SessionState, AgentAction, WorkerResponse
    from workers import EligibilityAgent, CreditBureauAgent, KYCAgent, DocumentAgent
except ImportError:
    print("ERROR: Could not import backend modules. Ensure you are in the root directory.")
    sys.exit(1)

# ==========================================
# 0. SETUP LOGGING
# ==========================================
os.makedirs("logs", exist_ok=True)

# Force UTF-8 for CSVs to handle Rupee symbols
csv_exec = open("logs/agent_execution_log.csv", "w", newline="", encoding="utf-8")
writer_exec = csv.writer(csv_exec)
writer_exec.writerow(["user_id", "agent_name", "input_summary", "output_status", "risk_score", "timestamp"])

csv_dec = open("logs/final_decisions.csv", "w", newline="", encoding="utf-8")
writer_dec = csv.writer(csv_dec)
writer_dec.writerow(["user_id", "final_status", "rejection_stage", "primary_reason", "fraud_flag", "category", "data_source"])

# Set stdout to handle utf-8 if possible, or ignore errors
# sys.stdout.reconfigure(encoding='utf-8') # Python 3.7+
pass

# ==========================================
# 1. DETERMINISTIC BRAIN
# ==========================================
class DeterministicBrain:
    def decide(self, session: SessionState) -> AgentAction:
        profile = session.profile
        
        # 1. ELIGIBILITY
        if not session.eligibility_run:
            return AgentAction(
                type="CALL_WORKER", worker_name="EligibilityAgent",
                worker_inputs={
                    "income": profile.monthly_income, "existing_emi": profile.existing_emi or 0,
                    "loan_amount": profile.loan_amount, "tenure_months": profile.tenure_months or 24
                }, reasoning="Eligibility Check"
            )

        # 2. FRAUD/CREDIT
        if not session.credit_bureau_checked:
            return AgentAction(
                type="CALL_WORKER", worker_name="CreditBureauAgent",
                worker_inputs={
                    "pan": profile.pan, "stated_income": profile.monthly_income, 
                    "stated_emi": profile.existing_emi or 0
                }, reasoning="Fraud Check"
            )

        # 3. KYC
        if not session.kyc_verified:
            return AgentAction(
                type="CALL_WORKER", worker_name="KYCAgent",
                worker_inputs={"pan": profile.pan, "name": profile.name},
                reasoning="KYC Verification"
            )

        # 4. SANCTION
        if not session.sanction_generated:
            return AgentAction(
                type="CALL_WORKER", worker_name="DocumentAgent",
                worker_inputs={
                    "customer_name": profile.name, "amount": session.profile.loan_amount, 
                    "tenure": session.profile.tenure_months
                }, reasoning="Sanction Letter"
            )

        return AgentAction(type="TERMINATE", user_message="Approved", reasoning="Done")

# ==========================================
# 2. EXECUTION ENGINE
# ==========================================
class IEEEValidator:
    def __init__(self):
        self.brain = DeterministicBrain()
        self.eligibility = EligibilityAgent()
        self.credit = CreditBureauAgent()
        self.kyc = KYCAgent()
        self.doc = DocumentAgent()

    def run_user(self, u):
        session = SessionState(session_id=u["user_id"])
        # Hydrate Profile
        session.profile.name = u["name"]
        session.profile.monthly_income = u["stated_income"]
        session.profile.existing_emi = u["existing_emi"]
        session.profile.loan_amount = u["loan_amount"]
        session.profile.tenure_months = u["tenure_months"]
        session.profile.pan = u["pan"]
        
        final_status = "IN_PROGRESS"
        rejection_stage = "None"
        reason = "None"
        fraud_flag = False
        
        for _ in range(8):
            action = self.brain.decide(session)
            
            if action.type == "TERMINATE":
                final_status = "ACCEPTED"
                break
                
            if action.type == "CALL_WORKER":
                worker = action.worker_name
                inputs = action.worker_inputs
                ts = datetime.now().isoformat()
                
                # Execute
                risk_score = 0
                output_status = "SUCCESS"
                
                if worker == "EligibilityAgent":
                    res = self.eligibility.check_eligibility(inputs["income"], inputs["existing_emi"], inputs["loan_amount"], inputs["tenure_months"])
                    session.eligibility_run = True
                    if not res.success: output_status = "FAIL"
                    
                elif worker == "CreditBureauAgent":
                    res = self.credit.check_bureau(inputs["pan"], inputs["stated_income"], inputs["stated_emi"])
                    session.credit_bureau_checked = True
                    risk_score = res.risk_score
                    if not res.success: output_status = "FAIL"
                    
                elif worker == "KYCAgent":
                    res = self.kyc.verify_pan(inputs["pan"], inputs["name"])
                    session.kyc_verified = True
                    
                elif worker == "DocumentAgent":
                    res = self.doc.generate_sanction_letter(inputs["customer_name"], inputs["amount"], inputs["tenure"])
                    session.sanction_generated = True

                # Log Execution
                writer_exec.writerow([u["user_id"], worker, "...", output_status, risk_score, ts])
                
                # Handle Rejection
                if not res.success:
                    final_status = "REJECTED"
                    rejection_stage = worker
                    reason = res.error_message
                    if worker == "CreditBureauAgent" and risk_score >= 50:
                        fraud_flag = True
                    break

        # Log Final Decision
        writer_dec.writerow([
            u["user_id"], final_status, rejection_stage, reason, fraud_flag, 
            u["metadata"]["category"], u["metadata"]["data_source"]
        ])

# ==========================================
# 3. METRICS & PLOTTING
# ==========================================
def generate_metrics():
    print("Generating Tables and Plots...")
    df = pd.read_csv("logs/final_decisions.csv")
    
    # TABLE A: Dataset Composition
    print("\n[TABLE A] Dataset Composition")
    print(df['category'].value_counts())
    
    # TABLE B: Outcome Distribution
    print("\n[TABLE B] Outcomes")
    print(df['final_status'].value_counts(normalize=True))
    
    # TABLE C: Fraud Performance
    fraud_injection = pd.read_json("data/fraud_injection_manifest.json")
    fraud_ids = fraud_injection['user_id'].tolist()
    
    # Filter our results for these IDs
    fraud_results = df[df['user_id'].isin(fraud_ids)]
    detected = fraud_results[fraud_results['fraud_flag'] == True]
    
    tp = len(detected)
    fn = len(fraud_results) - tp
    recall = tp / len(fraud_results) * 100
    
    # FPR
    normals = df[~df['user_id'].isin(fraud_ids)]
    fp = len(normals[normals['fraud_flag'] == True])
    tn = len(normals) - fp
    fpr = fp / len(normals) * 100
    
    print(f"\n[TABLE C] Fraud Metrics")
    print(f"Injected: {len(fraud_results)}")
    print(f"Detected: {tp}")
    print(f"Recall: {recall:.2f}%")
    print(f"False Positives: {fp} ({fpr:.2f}%)")
    
    # TABLE D: Funnel
    print("\n[TABLE D] Rejection Funnel")
    print(df[df['final_status']=='REJECTED']['rejection_stage'].value_counts())

    # PLOTS
    # 1. Funnel
    plt.figure(figsize=(8,5))
    df['rejection_stage'].value_counts().plot(kind='bar')
    plt.title('Rejection Funnel')
    plt.savefig('logs/rejection_funnel.png')
    
    # 2. Fraud Pie
    plt.figure(figsize=(6,6))
    plt.pie([tp, fn], labels=['Detected', 'Missed'], autopct='%1.1f%%', colors=['green', 'red'])
    plt.title('Fraud Detection Performance')
    plt.savefig('logs/fraud_detection.png')

if __name__ == "__main__":
    start = time.time()
    
    # Load Data
    with open("data/grounded_users.json") as f:
        users = json.load(f)
        
    validator = IEEEValidator()
    print(f"Running validation on {len(users)} users...")
    
    for u in users:
        validator.run_user(u)
        
    csv_exec.close()
    csv_dec.close()
    
    end = time.time()
    print(f"Execution complete in {end-start:.2f}s")
    
    generate_metrics()
