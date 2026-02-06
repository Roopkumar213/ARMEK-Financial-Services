import json
import sys
import os

sys.path.append(os.path.join(os.getcwd(), 'backend'))
try:
    from workers import CreditBureauAgent
except ImportError:
    print("Error importing backend")
    sys.exit()

def debug_misses():
    with open("ieee_grounded_users.json", "r") as f:
        users = json.load(f)
        
    agent = CreditBureauAgent()
    misses = 0
    
    print("\n--- ANALYZING FRAUD MISSES ---\n")
    
    for u in users:
        if not u["metadata"]["is_fraud"]:
            continue
            
        # Run Check
        res = agent.check_bureau(u["pan"], u["stated_income"], u["existing_emi"])
        
        # If it passed (Score < 70 means NOT Rejected in strict mode)
        # Wait, in simulation runner:
        # if "REJECT" in result.system_instruction -> REJECT
        # My updated worker returns REJECT if score >= 70.
        
        if res.risk_score < 70:
            misses += 1
            if misses <= 10:
                print(f"MISS #{misses}")
                print(f"Type: {u['metadata']['fraud_type']}")
                print(f"Income: {u['stated_income']}")
                print(f"EMI: {u['existing_emi']}")
                print(f"PAN: {u['pan']}")
                print(f"Score: {res.risk_score}")
                print(f"Signals: {res.data}") # Wait data doesn't have signals, error message has signals?
                # Actually, check_bureau returns signals in error_message usually?
                # But here success=True usually if score < 70 (or Flag).
                # The worker returns system_instruction="FLAG" if 50-69.
                # Is FLAG considered detected?
                # Simulation Runner says: `fraud_detected=(rejection_stage == "CreditBureauAgent" and fraud_score >= 50)`
                # So FLAG (50-69) counts as DETECTED.
                
                # So I need to check if score < 50.
                if res.risk_score >= 50:
                    # This was actually DETECTED by the runner.
                    # So why did the runner report only 85 detected?
                    # Maybe my manual count here is different?
                    pass
                else:
                    print(f"REAL MISS! Score < 50.")
                    
    print(f"\nTotal Misses (Score < 50): {misses} / 150")

if __name__ == "__main__":
    debug_misses()
