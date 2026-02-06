# workers.py
import re
import random
import os
from datetime import datetime
from typing import Dict, Any, List

from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, Image, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from pypdf import PdfReader, PdfWriter

from models import WorkerResponse

# ==========================================
# 1. STATE RECONCILIATION AGENT
# ==========================================

class StateReconciliationAgent:
    """
    Monitors state consistency. 
    If a critical field changes, it invalidates downstream verifications.
    """
    def reconcile(self, old_profile: Dict[str, Any], new_inputs: Dict[str, Any]) -> WorkerResponse:
        invalidated_fields = []
        
        # If Income changes, we must re-run Eligibility and Credit Bureau
        if "monthly_income" in new_inputs:
            old_income = old_profile.get("monthly_income")
            new_income = new_inputs["monthly_income"]
            if old_income and abs(old_income - new_income) > 100:
                invalidated_fields.append("eligibility_run")
                invalidated_fields.append("credit_bureau_checked")
                invalidated_fields.append("sanction_generated")

        # If PAN changes, invalidate everything
        if "pan" in new_inputs:
             old_pan = old_profile.get("pan")
             new_pan = new_inputs["pan"]
             if old_pan and old_pan != new_pan:
                 invalidated_fields.append("kyc_verified")
                 invalidated_fields.append("credit_bureau_checked")
                 invalidated_fields.append("sanction_generated")
        
        return WorkerResponse(
            success=True,
            data={"invalidated_flags": invalidated_fields},
            system_instruction="Reset flags if present" if invalidated_fields else None
        )

# ==========================================
# 2. ELIGIBILITY AGENT
# ==========================================

class EligibilityAgent:
    """
    Pure mathematical agent. 
    Calculates FOIR and Max Loan Eligibility.
    Run this EARLY.
    """
    def check_eligibility(self, income: float, existing_emi: float, requested_amount: float, tenure: int) -> WorkerResponse:
        
        # 1. Minimum Income Check
        if income < 25000:
            return WorkerResponse(
                success=False,
                error_message="Income below minimum threshold of ₹25,000",
                risk_score=80,
                system_instruction="REJECT_USER"
            )

        # 2. EMI Calculation
        if tenure <= 0: tenure = 12
        rate_monthly = 12.0 / 1200
        # Standard EMI formula
        proposed_emi = (requested_amount * rate_monthly * (1 + rate_monthly)**tenure) / ((1 + rate_monthly)**tenure - 1)
        
        # 3. FOIR Check (Fixed Obligation to Income Ratio)
        total_obligation = existing_emi + proposed_emi
        foir = total_obligation / income
        
        MAX_FOIR = 0.50  # 50%
        
        if foir > MAX_FOIR:
            return WorkerResponse(
                success=False,
                data={"max_foir": MAX_FOIR, "current_foir": round(foir, 2)},
                error_message=f"Total obligations (₹{int(total_obligation)}) exceed 50% of income.",
                risk_score=60,
                system_instruction="SUGGEST_LOWER_AMOUNT"
            )

        return WorkerResponse(
            success=True,
            data={
                "approved_amount": requested_amount,
                "monthly_emi": int(proposed_emi),
                "foir": round(foir, 2)
            }
        )

# ==========================================
# 3. CREDIT BUREAU AGENT (FRAUD ENGINE)
# ==========================================

# ==========================================
# 3. CREDIT BUREAU AGENT (FRAUD ENGINE)
# ==========================================

# ==========================================
# 3. CREDIT BUREAU AGENT (FRAUD ENGINE)
# ==========================================

class CreditBureauAgent:
    """
    IEEE-Grade Fraud Detection Engine.
    Uses Multi-Signal Scoring (0-100) to detect anomalies.
    """
    def check_bureau(self, pan: str, stated_income: float, stated_emi: float, mode: str = "PRIMARY") -> WorkerResponse:
        pan = pan.upper()
        
        # 1. FETCH BUREAU TRUTH (MOCKED API)
        bureau_data = self._fetch_bureau_truth(pan, stated_income, stated_emi)
        
        # CONFIGURABLE THRESHOLDS
        if mode == "STRESS":
            TH_INCOME_SEVERE = 1.3
            TH_INCOME_MODERATE = 1.1 # Strict
            TH_DEBT_SEVERE = 0.1
            TH_DEBT_MODERATE = 0.01 # Zero tolerance
        else: # PRIMARY (Realistic)
            TH_INCOME_SEVERE = 1.6
            TH_INCOME_MODERATE = 1.25 # Allow some variance (bonuses etc)
            TH_DEBT_SEVERE = 0.25
            TH_DEBT_MODERATE = 0.1 # Allow small hidden debts
            
        # 2. CALCULATE RISK SCORE
        score = 0
        signals = []
        
        # Signal A: Income Inflation
        income_ratio = stated_income / (bureau_data["verified_income"] + 1)
        if income_ratio > TH_INCOME_SEVERE:  
            score += 80
            signals.append(f"CRITICAL: Income >{TH_INCOME_SEVERE}x Verified ({income_ratio:.1f}x)")
        elif income_ratio > TH_INCOME_MODERATE: 
            score += 50 # Increased from 40 to trigger Flag (>50) for messy data
            signals.append(f"WARN: Income Mismatch ({income_ratio:.1f}x)")
            
        # Signal B: Hidden Liabilities
        hidden_debt = bureau_data["actual_emi"] - stated_emi
        if hidden_debt > (stated_income * TH_DEBT_SEVERE): 
            score += 75 
            signals.append(f"CRITICAL: Significant Hidden Debt (₹{int(hidden_debt)})")
        elif hidden_debt > (stated_income * TH_DEBT_MODERATE):
            score += 30
            signals.append("WARN: Minor Undeclared Dept")
            
        # Signal C: Synthetic/Bust-out Risk (Constant)
        if stated_income > 50000 and bureau_data["cibil"] < 600:
            score += 75
            signals.append("CRITICAL: Synthetic Profile (High Income / Deep Subprime)")
            
        # Signal D: CIBIL Floor (Constant)
        if bureau_data["cibil"] < 650:
            score += 15
            signals.append(f"Credit Score Risk ({bureau_data['cibil']})")
            
        # 3. DECISION
        # Thresholds: >= 70 REJECT, 50-69 FLAG, <50 PASS
        if score >= 70:
            return WorkerResponse(
                success=False,
                risk_score=score,
                error_message=f"CRITICAL FRAUD RISK (Score {score}). {signals}",
                system_instruction="REJECT_USER"
            )
        elif score >= 50:
            return WorkerResponse(
                success=False,
                risk_score=score,
                error_message=f"High Risk Warning (Score {score}). {signals}",
                system_instruction="FLAG_FRAUD"
            )
            
        return WorkerResponse(
            success=True,
            data={"cibil": bureau_data["cibil"], "verified_income": bureau_data["verified_income"]},
            risk_score=score
        )

    def _fetch_bureau_truth(self, pan: str, stated_income: float, stated_emi: float):
        """
        Oracle function that returns the 'True' financial state of the user.
        Derived from the 'Pan Marker' injected by the Generator.
        """
        # Markers: 88=IncomeFraud, 99=DebtFraud, 77=Synthetic
        pan_nums = "".join(filter(str.isdigit, pan))
        
        # DEFAULTS (Honest User)
        verified_income = stated_income
        actual_emi = stated_emi
        cibil = random.randint(700, 850)
        
        if "88" in pan_nums: # Income Inflation
            verified_income = stated_income * 0.3 # Base truth
            
            # If it was "Subtle Fraud" (generated by random choice in generator), 
            # the generator set Stated Income to 1.25x True Income.
            # But here we are RE-DERIVING True Income from Stated Income using a fixed 0.3 factor.
            # This is a Problem. The "Truth" logic must match the "Generator" logic.
            # The Generator set: stated = true * factor.
            # So true = stated / factor.
            # But here `_fetch_bureau_truth` only sees `stated`.
            # If I stick to `verified = stated * 0.3`, then `stated` is 3.3x verified.
            # That forces it to be SEVERE fraud always.
            
            # FIX: I need to allow the "Truth" to be closer to Stated for subtle cases.
            # But the backend doesn't know IF it is subtle. It just sees "88".
            # Hack: Use last digit of PAN to encode severity?
            # Generator: pan_marker = "88" always.
            # Let's update `_fetch_bureau_truth` to be smarter or 
            # Update Generator to encode severity/truth in the PAN?
            # Or just assume the "Stated" income passed in is the "Lie" and 
            # we need to recover the "Truth".
            # In Generator: 
            #   Severe: Stated = True * 3.0 -> True = Stated * 0.33
            #   Subtle: Stated = True * 1.3 -> True = Stated * 0.77
            # If I hardcode `verified = stated * 0.3`, then Subtle Fraud (1.3x) 
            # effectively becomes Severe Fraud (3.3x) because the Bureau forces the truth down.
            
            # REAL FIX: The Agent shouldn't "derive" truth from Stated. 
            # The Agent should fetch truth.
            # In this simulation, `_fetch_bureau_truth` IS the API.
            # It needs to return the value that `generate_evidence_data` thought was "True".
            # But it doesn't have access to the JSON.
            
            # Solution: Encode the "Truth Ratio" in the PAN? 
            # Or just randomize the truth retrieval slightly?
            # If I make `verified_income = stated_income * random.uniform(0.3, 0.8)`,
            # it breaks determinism unless seeded.
            
            # BETTER SOLUTION: For "88", make verified_income = stated_income * 0.6 (Average).
            # Then:
            #   User A (Severe): Claims 30k (True 10k). Ratio 3.0. Bureau returns 18k (0.6). Ratio 1.6 -> SEVERE.
            #   User B (Subtle): Claims 13k (True 10k). Ratio 1.3. Bureau returns 7.8k (0.6). Ratio 1.6 -> SEVERE.
            # Still fails to distinguish.
            
            # I must encode the severity in the PAN.
            # Let's change Generator to use "88" for Severe and "89" for Subtle.
            pass

        if "88" in pan_nums: # severe
            verified_income = stated_income * 0.3
            cibil = random.randint(550, 700)
        elif "89" in pan_nums: # subtle (NEW)
            verified_income = stated_income * 0.8 # Stated is 1.25x Verified
            cibil = random.randint(600, 720)
        
        elif "11" in pan_nums: # Messy Honest (NEW)
            # Stated is ~1.3x Verified (Uniform 1.15-1.40)
            verified_income = stated_income * 0.77 
            cibil = random.randint(700, 800) # Still good credit
            
        elif "99" in pan_nums: # Hidden Debt
            actual_emi = stated_income * 0.7 
            cibil = random.randint(500, 650)
            
        elif "77" in pan_nums: # Synthetic
            cibil = random.randint(300, 550)
            
        return {
            "verified_income": verified_income,
            "actual_emi": actual_emi,
            "cibil": cibil
        }

# ==========================================
# 4. KYC AGENT
# ==========================================

class KYCAgent:
    def verify_pan(self, pan: str, name: str) -> WorkerResponse:
        pan = pan.strip().upper()
        
        if not re.match(r"^[A-Z]{5}[0-9]{4}[A-Z]$", pan):
            return WorkerResponse(success=False, error_message="Invalid PAN format")
            
        return WorkerResponse(success=True, data={"verified_name": name})

# ==========================================
# 5. DOCUMENT AGENT
# ==========================================

class DocumentAgent:
    def generate_sanction_letter(self, customer_name: str, amount: float, tenure: int) -> WorkerResponse:
        try:
            # Re-using the robust ReportLab logic from the original prototype
            # But wrapping it safely
            output_dir = "generated_letters"
            os.makedirs(output_dir, exist_ok=True)
            
            safe_name = customer_name.replace(" ", "_")
            file_path = f"{output_dir}/sanction_{safe_name}.pdf"
            
            doc = SimpleDocTemplate(file_path, pagesize=A4)
            styles = getSampleStyleSheet()
            elements = []
            
            elements.append(Paragraph("LOAN SANCTION LETTER", styles["Title"]))
            elements.append(Spacer(1, 12))
            elements.append(Paragraph(f"Dear {customer_name},", styles["Normal"]))
            elements.append(Paragraph(f"We are pleased to inform you that your loan of INR {amount} has been approved.", styles["Normal"]))
            elements.append(Paragraph(f"Tenure: {tenure} months", styles["Normal"]))
            
            doc.build(elements)
            
            # (Skipping encryption for speed in this prototype rebuild, can add back if needed)
            
            return WorkerResponse(
                success=True, 
                data={"url": f"/{file_path}"}
            )
        except Exception as e:
            return WorkerResponse(success=False, error_message=str(e))
