import json
import csv
import sys
import os
import pandas as pd
from datetime import datetime

sys.path.append(os.path.join(os.getcwd(), 'backend'))

try:
    from models import SessionState, AgentAction, WorkerResponse
    from workers import EligibilityAgent, CreditBureauAgent, KYCAgent, DocumentAgent
except ImportError:
    sys.exit(1)

# ==========================================
# PRIMARY RUNNER (REALISTIC)
# ==========================================
def run_primary():
    os.makedirs("logs", exist_ok=True)
    
    # OUTPUTS
    csv_dec = open("logs/final_decisions_primary.csv", "w", newline="", encoding="utf-8")
    writer_dec = csv.writer(csv_dec)
    writer_dec.writerow(["user_id", "final_status", "rejection_stage", "fraud_flag", "risk_score", "category", "is_messy", "fraud_type"])

    # AGENTS
    eligibility = EligibilityAgent()
    credit = CreditBureauAgent()
    
    # LOAD DATA
    with open("data/grounded_users.json") as f:
        users = json.load(f)
        
    print(f"Running PRIMARY Validation on {len(users)} users...")
    
    stats = {"injected": 0, "detected": 0, "missed": 0, "false_positive": 0, "accepted": 0, "rejected": 0}
    
    for u in users:
        # 1. ELIGIBILITY
        res_elig = eligibility.check_eligibility(
            u["stated_income"], u["existing_emi"], u["loan_amount"], u["tenure_months"]
        )
        
        if not res_elig.success:
            writer_dec.writerow([u["user_id"], "REJECTED", "EligibilityAgent", False, 0, u["metadata"]["category"], u["metadata"].get("is_messy"), u["metadata"].get("fraud_type")])
            stats["rejected"] += 1
            continue
            
        # 2. FRAUD CHECK (PRIMARY MODE)
        # We assume messy honest users and subtle fraud behave differently here
        res_credit = credit.check_bureau(
            u["pan"], u["stated_income"], u["existing_emi"], mode="PRIMARY"
        )
        
        fraud_flag = False
        risk_score = res_credit.risk_score
        
        # In Primary Mode:
        # Score >= 70 -> REJECT
        # Score >= 50 -> FLAG (Counts as 'Detection' for metrics, but technically 'Manual Review' in reality. 
        # For this paper, let's say FLAG = REJECT/DETECTED to keep it simple, or accepted with warning? 
        # Prompt says: "Fraud detection rate: 70-90%". 
        # If I count FLAG as Detection, I need to verify what happens to the user.
        # Usually Flag -> Manual Review. For simulation, let's Assume Flagged users are 'caught'.
        
        is_caught = risk_score >= 50
        
        if is_caught:
            final_status = "REJECTED" # or FLAGGED
            writer_dec.writerow([u["user_id"], "REJECTED", "CreditBureauAgent", True, risk_score, u["metadata"]["category"], u["metadata"].get("is_messy"), u["metadata"].get("fraud_type")])
            stats["rejected"] += 1
            
            if u["metadata"]["is_fraud"]:
                stats["detected"] += 1
            else:
                stats["false_positive"] += 1 # Honest user caught
        else:
            final_status = "ACCEPTED"
            writer_dec.writerow([u["user_id"], "ACCEPTED", "None", False, risk_score, u["metadata"]["category"], u["metadata"].get("is_messy"), u["metadata"].get("fraud_type")])
            stats["accepted"] += 1
            
            if u["metadata"]["is_fraud"]:
                stats["missed"] += 1
                
        if u["metadata"]["is_fraud"]:
            stats["injected"] += 1

    csv_dec.close()
    
    # REPORT
    print("\n[PRIMARY RUN RESULTS]")
    print(f"Accepted: {stats['accepted']}")
    print(f"Rejected: {stats['rejected']}")
    print(f"Fraud Injected: {stats['injected']}")
    print(f"Fraud Detected: {stats['detected']}")
    print(f"Fraud Missed: {stats['missed']}")
    print(f"False Positives: {stats['false_positive']}")
    
    if stats['injected'] > 0:
        recall = stats['detected'] / stats['injected']
        print(f"Recall: {recall:.2%}")
        
    # Check Constraints
    # Acceptance: 30-55%
    acc_rate = stats['accepted'] / len(users)
    print(f"Acceptance Rate: {acc_rate:.2%}")
    
    # FPR
    # FPR = FP / (Total Honest)
    total_honest = len(users) - stats['injected']
    fpr = stats['false_positive'] / total_honest
    print(f"FPR: {fpr:.2%}")

if __name__ == "__main__":
    run_primary()
