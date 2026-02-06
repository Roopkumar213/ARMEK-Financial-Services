import json
import sys
import os

sys.path.append(os.path.join(os.getcwd(), 'backend'))
try:
    from workers import EligibilityAgent
except ImportError:
    print("Error importing backend")
    sys.exit()

def debug_eligibility_leak():
    with open("data/grounded_users.json", "r") as f:
        users = json.load(f)
        
    agent = EligibilityAgent()
    leaks = 0
    
    print("\n--- ANALYZING ELIGIBILITY LEAKS ---\n")
    
    for u in users:
        if not u["metadata"]["is_fraud"]:
            continue
            
        # Run Check
        res = agent.check_eligibility(
            u["stated_income"], 
            u["existing_emi"], 
            u["loan_amount"], 
            u["tenure_months"]
        )
        
        if not res.success:
            leaks += 1
            if leaks <= 5:
                print(f"LEAK #{leaks}")
                print(f"Income: {u['stated_income']}")
                print(f"Loan: {u['loan_amount']}")
                print(f"EMI: {u['existing_emi']}")
                print(f"Tenure: {u['tenure_months']}")
                print(f"Msg: {res.error_message}")
                if res.data:
                    print(f"Data: {res.data}")
                print("-" * 20)
                
    print(f"\nTotal Leaks: {leaks} / 150")

if __name__ == "__main__":
    debug_eligibility_leak()
