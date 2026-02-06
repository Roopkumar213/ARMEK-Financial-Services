import numpy as np
import json
import random

def generate_grounded_users(count=1000):
    users = []
    
    # ==========================================
    # 1. DISTRIBUTION PARAMETERS (Source: PLFS 2023-24 / CIBIL)
    # ==========================================
    
    # INCOME: Log-Normal distribution
    # Mean ~ ₹25,000, high variance to capture top 10% vs bottom 50%
    mu, sigma = 10.12, 0.8 # ln(25000) ~= 10.12
    incomes = np.random.lognormal(mu, sigma, count)
    
    # CIBIL: Custom weighted choices
    # Prime (>731): 55%, Near Prime (681-731): 24%, Subprime (<681): 21%
    cibil_buckets = ["Prime", "NearPrime", "Subprime"]
    cibil_weights = [0.55, 0.24, 0.21]
    
    # ==========================================
    # 2. GENERATION LOOP
    # ==========================================
    for i in range(count):
        user_id = f"U_{i:04d}"
        
        # --- Income ---
        # Cap min income at 5k to be realistic for "loan applicant" pool (even if ineligible)
        monthly_income = max(5000, int(incomes[i]))
        
        # --- Credit Profile ---
        credit_segment = np.random.choice(cibil_buckets, p=cibil_weights)
        if credit_segment == "Prime":
            cibil = random.randint(731, 850)
            base_foir = random.uniform(0.1, 0.35) # Safe
        elif credit_segment == "NearPrime":
            cibil = random.randint(681, 730)
            base_foir = random.uniform(0.3, 0.5) # Stretched
        else: # Subprime
            cibil = random.randint(300, 680)
            base_foir = random.uniform(0.4, 0.7) # Dangerous
            
        # --- Obligations (EMI) ---
        existing_emi = int(monthly_income * base_foir)
        
        # --- Loan Request ---
        # People usually ask for 10-20x their monthly income
        loan_amount = int(monthly_income * random.uniform(10, 24))
        # Round to nearest 5000
        loan_amount = round(loan_amount / 5000) * 5000
        
        # --- Fraud Injection (15% Targeted) ---
        is_fraud = False
        fraud_type = None
        
        # We inject fraud deterministically into 15% of the pool
        # This overwrites their "Truth" but keeps their "Stated" values
        if i < (count * 0.15): 
            is_fraud = True
            # Fraud Type: Income Inflation
            # User truly earns 30% of what they say
            true_income = int(monthly_income * 0.3)
            fraud_type = "IncomeInflation"
            # We mark this via a specific pattern in PAN for the Mock Bureau to pick up
            pan_pattern = "88" 
        else:
            true_income = monthly_income
            pan_pattern = f"{random.randint(10,99)}"

        # --- PAN Generation ---
        # Format: ABCDE 1234 F
        pan_mid = f"{random.randint(10,99)}{pan_pattern}" # Ensures pattern is embedded
        pan = f"ABCDE{pan_mid}F"

        user = {
            "id": user_id,
            "name": f"User_{i}",
            "stated_income": monthly_income, # What they tell the bot
            "true_income": true_income,      # What the Bureau knows
            "existing_emi": existing_emi,
            "loan_amount": loan_amount,
            "pan": pan,
            "cibil": cibil,
            "is_fraud_simulation": is_fraud,
            "metadata": {
                "source": "Generated_PLFS_Distribution",
                "credit_segment": credit_segment,
                "fraud_type": fraud_type
            }
        }
        users.append(user)
        
    # ==========================================
    # 3. SAVE
    # ==========================================
    with open("grounded_users.json", "w") as f:
        json.dump(users, f, indent=2)
    
    print(f"Generated {len(users)} grounded profiles.")
    
if __name__ == "__main__":
    generate_grounded_users()
