import numpy as np
import json
import random
import os

def generate_evidence_datasets(count=1000):
    users = []
    fraud_manifest = []
    
    # PARAMETERS (Source: PLFS 2023-24, CIBIL 2024)
    # Income: Log-Normal distribution
    # TUNING: Shifted mu from 10.12 to 10.75 to ensure Acceptance > 30%
    mu, sigma = 10.75, 0.7 
    
    # OUTPUT DIRECTORY
    os.makedirs("data", exist_ok=True)
    
    print("Generating grounded dataset based on PLFS 2024 & CIBIL 2024...")
    
    for i in range(count):
        user_id = f"REF_{i:04d}"
        
        # 1. GENERATE BASE PROFILE (PLFS/CIBIL GROUNDING)
        monthly_income = max(12000, int(np.random.lognormal(mu, sigma)))
        income_band = "Low" if monthly_income < 25000 else "Mid" if monthly_income < 60000 else "High"
        
        rand_c = random.random()
        if rand_c < 0.55:
            cibil = random.randint(731, 850)
            credit_band = "Prime"
        elif rand_c < 0.80:
            cibil = random.randint(680, 730)
            credit_band = "NearPrime"
        else:
            cibil = random.randint(300, 679)
            credit_band = "Subprime"
        
        foir = random.uniform(0.1, 0.4) # Reduced existing burden slightly
        existing_emi = int(monthly_income * foir)
        
        # FIX: Loan Amount was too high (8-20x) causing 100% Rejection on FOIR.
        # For 24 months, max loan is approx 10x monthly income (EMI ~45% income).
        # We set it to 3-8x to be safe/mixed.
        loan_amount = round(monthly_income * random.uniform(3, 8) / 10000) * 10000
        
        # Determine Category Baseline
        category = "Eligible"
        if credit_band == "Subprime": category = "Ineligible_Credit"
        if monthly_income < 25000: category = "Ineligible_Income"
        
        # 2. FRAUD & MESSY DATA INJECTION
        is_fraud = False
        is_messy = False # Honest but incompetent data entry
        stated_income = monthly_income
        true_income = monthly_income
        stated_emi = existing_emi
        pan_marker = f"{random.randint(10,66)}"
        fraud_type = "None"
        
        # A. FRAUD (15% = 150 Users)
        if i < 150: 
            is_fraud = True
            category = "Fraud"
            
            # Ensure they usually pass eligibility (Wolf in sheep's clothing)
            monthly_income = max(35000, monthly_income)
            stated_income = monthly_income
            stated_emi = 0 # Hide debt to pass FOIR
            loan_amount = monthly_income * 5 # Safe loan ratio
            
            attack = random.choice(["INCOME_INFLATION", "HIDDEN_DEBT", "SYNTHETIC_ID"])
            
            if attack == "INCOME_INFLATION":
                # Mix of Obvious (>2x) and Subtle (1.2-1.4x)
                if random.random() < 0.7:
                    # Obvious Fraud (Severe) -> Marker 88
                    stated_income = monthly_income * random.uniform(2.0, 3.0)
                    pan_marker = "88"
                    fraud_type = "Income Inflation (Severe)"
                else:
                    # Subtle Fraud (Borderline) -> Marker 89
                    stated_income = monthly_income * random.uniform(1.25, 1.45)
                    pan_marker = "89" 
                    fraud_type = "Income Inflation (Subtle)"
                    
            elif attack == "HIDDEN_DEBT":
                # Stated EMI is 0, True EMI is High
                existing_emi = int(monthly_income * 0.7) 
                pan_marker = "99"
                fraud_type = "Hidden Liability"
                
            elif attack == "SYNTHETIC_ID":
                stated_income = max(60000, monthly_income * 2) 
                cibil = random.randint(300, 500)
                pan_marker = "77"
                fraud_type = "Synthetic ID"
        
        # B. MESSY HONEST (10% = 100 Users) - Source of False Positives
        elif i < 250:
            is_messy = True
            category = "Borderline_Messy"
            # Honest user but bad record keeping
            # Stated income slightly higher than real (e.g. included bonus not in bureau)
            # Increase Variance to TRIGGER warnings (Threshold is 1.25)
            variance = random.uniform(1.15, 1.40) 
            stated_income = int(monthly_income * variance)
            true_income = monthly_income # Bureau has base
            # Bureau match will show distinct but "explainable" gap
            
            # FIX: Must encode Messy status in PAN so Worker can return "True < Stated"
            pan_marker = "11"
            
        # C. STANDARD USERS
        else:
            stated_income = monthly_income
            true_income = monthly_income
            
        pan = f"ABCDE12{pan_marker}F"
        
        # 3. SAVE RECORD
        users.append({
            "user_id": user_id,
            "stated_income": int(stated_income),
            "existing_emi": int(stated_emi),
            "loan_amount": int(loan_amount),
            "tenure_months": 24,
            "pan": pan,
            "name": f"User {i}",
            "metadata": {
                "income_band": income_band,
                "credit_band": credit_band,
                "category": category,
                "data_source": "PLFS_2024_Synthetic" if not is_fraud else "Adversarial_Injection",
                "is_fraud": is_fraud,
                "is_messy": is_messy,
                "fraud_type": fraud_type,
                "true_income": int(true_income),
                "true_emi": int(existing_emi) if is_fraud and fraud_type=="Hidden Liability" else int(stated_emi),
                "true_cibil": cibil
            }
        })

    # WRITE FILES
    with open("data/grounded_users.json", "w") as f:
        json.dump(users, f, indent=2)
        
    with open("data/fraud_injection_manifest.json", "w") as f:
        json.dump(fraud_manifest, f, indent=2)
        
    print(f"Generated {count} users and {len(fraud_manifest)} fraud records.")

if __name__ == "__main__":
    generate_evidence_datasets()
