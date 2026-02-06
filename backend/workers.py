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
# 3. CREDIT BUREAU AGENT (FRAUD SIMULATION)
# ==========================================

class CreditBureauAgent:
    """
    Simulates a Credit Bureau check.
    Includes 'Logic Traps' for fake data.
    """
    def check_bureau(self, pan: str, stated_income: float, stated_emi: float) -> WorkerResponse:
        pan = pan.upper()
        
        # --- LOGIC TRAP 1: Fake High Income ---
        # Users often input 999999 or 500000 to test the system.
        # If income is suspiciously high without a "Corporate" PAN signature (simulated), flag it.
        if stated_income > 300000:
            # Deterministic check based on PAN last digit
            # If last digit is odd, we assume 'file thin' -> Fraud
            last_digit = int(pan[5:9]) % 10
            if last_digit % 2 != 0:
                return WorkerResponse(
                    success=False,
                    risk_score=95,
                    error_message=f"Income of ₹{stated_income} is inconsistent with credit history for PAN {pan}.",
                    system_instruction="FLAG_FRAUD"
                )

        # --- LOGIC TRAP 2: Hidden Liabilities ---
        # Simulate finding hidden loans for specific PAN patterns
        # If PAN contains '88', we simulate a hidden EMI of 15k
        if "88" in pan:
             actual_obligations = stated_emi + 15000
             if actual_obligations > (stated_income * 0.6):
                  return WorkerResponse(
                    success=False,
                    risk_score=75,
                    error_message=f"Credit Report shows undeclared active loans. Real FOIR > 60%.",
                    system_instruction="REJECT_USER"
                )

        # Default Pass
        simulated_cibil = random.randint(700, 850)
        return WorkerResponse(
            success=True,
            data={"cibil_score": simulated_cibil},
            risk_score=10
        )

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
