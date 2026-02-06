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
# STRESS RUNNER (ADVERSARIAL)
# ==========================================
def run_stress():
    os.makedirs("logs", exist_ok=True)
    
    csv_dec = open("logs/final_decisions_stress.csv", "w", newline="", encoding="utf-8")
    writer_dec = csv.writer(csv_dec)
    writer_dec.writerow(["user_id", "final_status", "rejection_stage", "fraud_flag", "risk_score", "category", "is_messy", "fraud_type"])

    eligibility = EligibilityAgent()
    credit = CreditBureauAgent()
    
    with open("data/grounded_users.json") as f:
        users = json.load(f)
        
    print(f"Running STRESS Validation on {len(users)} users...")
    
    stats = {"injected": 0, "detected": 0, "missed": 0, "false_positive": 0, "accepted": 0, "rejected": 0}
    
    for u in users:
        # 1. ELIGIBILITY
        res_elig = eligibility.check_eligibility(u["stated_income"], u["existing_emi"], u["loan_amount"], u["tenure_months"])
        if not res_elig.success:
            writer_dec.writerow([u["user_id"], "REJECTED", "EligibilityAgent", False, 0, u["metadata"]["category"], u["metadata"].get("is_messy"), u["metadata"].get("fraud_type")])
            stats["rejected"] += 1
            continue
            
        # 2. FRAUD CHECK (STRESS MODE)
        # Strict Mode: Any deviation is flagged
        res_credit = credit.check_bureau(u["pan"], u["stated_income"], u["existing_emi"], mode="STRESS")
        
        is_caught = res_credit.risk_score >= 50 # Flag counts as rejection in Stress
        
        if is_caught:
            writer_dec.writerow([u["user_id"], "REJECTED", "CreditBureauAgent", True, res_credit.risk_score, u["metadata"]["category"], u["metadata"].get("is_messy"), u["metadata"].get("fraud_type")])
            stats["rejected"] += 1
            if u["metadata"]["is_fraud"]:
                stats["detected"] += 1
            else:
                stats["false_positive"] += 1
        else:
            writer_dec.writerow([u["user_id"], "ACCEPTED", "None", False, res_credit.risk_score, u["metadata"]["category"], u["metadata"].get("is_messy"), u["metadata"].get("fraud_type")])
            stats["accepted"] += 1
            if u["metadata"]["is_fraud"]:
                stats["missed"] += 1
                
        if u["metadata"]["is_fraud"]:
            stats["injected"] += 1

    csv_dec.close()
    
    print("\n[STRESS RUN RESULTS]")
    print(f"Accepted: {stats['accepted']}")
    print(f"Rejected: {stats['rejected']}")
    print(f"Fraud Recall: {stats['detected']/stats['injected']:.2%}")
    print(f"FPR: {stats['false_positive']/(len(users)-stats['injected']):.2%}")

if __name__ == "__main__":
    run_stress()
