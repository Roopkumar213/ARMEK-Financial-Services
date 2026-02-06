import numpy as np
import json
import random

def generate_ieee_dataset(count=1000):
    users = []
    
    # PARAMETERS (Source: PLFS 2023-24, CIBIL 2024)
    mu, sigma = 10.12, 0.8 # ln(25000)
    
    # 1. GENERATE BASE POPULATION
    for i in range(count):
        user_id = f"REF_{i:04d}"
        
        # Base Income
        monthly_income = max(8000, int(np.random.lognormal(mu, sigma)))
        
        # Base CIBIL (Real Distribution)
        # 55% Prime (>730), 25% Near Prime (680-730), 20% Subprime (<680)
        rand_c = random.random()
        if rand_c < 0.55:
            cibil = random.randint(731, 850)
            credit_segment = "Prime"
        elif rand_c < 0.80:
            cibil = random.randint(680, 730)
            credit_segment = "NearPrime"
        else:
            cibil = random.randint(300, 679)
            credit_segment = "Subprime"
            
        # Base Obligations
        foir = random.uniform(0.1, 0.6) # 10% to 60% EMI load
        existing_emi = int(monthly_income * foir)
        
        # Loan Request (Random realistic request)
        loan_amount = round(monthly_income * random.uniform(8, 20) / 10000) * 10000
        
        # 2. FRAUD INJECTION (15% = 150 Users)
        # We define 3 specific attack vectors found in literature
        is_fraud = False
        fraud_type = "None"
        pan_marker = "00"
        
        if i < 150: # First 150 are the Fraudsters
            is_fraud = True
            attack_vector = random.choice(["INCOME_INFLATION", "HIDDEN_DEBT", "SYNTHETIC_ID"])
            
            if attack_vector == "INCOME_INFLATION":
                # Stated Income is Lie. True income is low.
                # User says 100k, actually earns 30k.
                stated_income = monthly_income * random.uniform(2.5, 4.0)
                true_income = monthly_income 
                pan_marker = "88" # Marker for Bureau to return True Income
                fraud_type = "Income Inflation (>2.5x)"
                
            elif attack_vector == "HIDDEN_DEBT":
                # User hides EMIs. Stated EMI is low. True EMI is high.
                stated_income = monthly_income
                true_income = monthly_income
                # They claim 0 or low EMI, but actually have huge debt
                existing_emi = 0 
                # Bureau will see the "True" FOIR of >70%
                pan_marker = "99" # Marker for Bureau to reveal debt
                fraud_type = "Hidden Liabilities"
                
            elif attack_vector == "SYNTHETIC_ID":
                # mismatched profile (High Stated Income + Very Low CIBIL + Bad History)
                # FIX: Force them to claim high income to be "Risk" otherwise they are just poor.
                stated_income = max(60000, monthly_income * 2) 
                true_income = monthly_income # True income is likely low/irrelevant as ID is synthetic
                cibil = random.randint(300, 500) # Deep subprime
                pan_marker = "77"
                fraud_type = "Synthetic/Bust-out Risk"
                
        else:
            # Honest Users
            stated_income = monthly_income
            true_income = monthly_income
            pan_marker = f"{random.randint(10,66)}"
            
        # 3. PAN GENERATION
        # Format: ABCDE 12(Marker) F
        pan = f"ABCDE12{pan_marker}F"
        
        user = {
            "id": user_id,
            "name": f"Applicant_{i}",
            "stated_income": int(stated_income),
            "existing_emi": int(existing_emi),
            "loan_amount": int(loan_amount),
            "pan": pan,
            "cibil": cibil, # This is the "Real" CIBIL
            "tenure_months": 24,
            "metadata": {
                "is_fraud": is_fraud,
                "fraud_type": fraud_type,
                "credit_segment": credit_segment,
                "true_income": int(true_income)
            }
        }
        users.append(user)
        
    with open("ieee_grounded_users.json", "w") as f:
        json.dump(users, f, indent=2)
    print(f"Generated {count} profiles. Fraud: 150.")

if __name__ == "__main__":
    generate_ieee_dataset()
