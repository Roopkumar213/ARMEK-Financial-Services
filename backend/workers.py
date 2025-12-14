from typing import Dict, Any
from datetime import datetime
import os

from reportlab.platypus import HRFlowable
from pypdf import PdfReader, PdfWriter

# =====================================================
# CONFIG
# =====================================================
NBFC_NAME = "ARMEK Financial Services"
NBFC_WEBSITE = "www.armekfinance.com"  # demo-safe
OUTPUT_DIR = "generated_letters"
LOGO_PATH = "static/nbfc_logo.png"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# =====================================================
# WORKER 1 — KYC / VERIFICATION AGENT
# =====================================================
def verify_customer(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simulated KYC worker.
    Verifies PAN format only (demo scope).
    """
    pan = data.get("pan", "").strip().upper()

    if not pan:
        return {"verified": False, "reason": "PAN not provided"}

    if len(pan) != 10:
        return {"verified": False, "reason": "Invalid PAN length"}

    return {"verified": True, "reason": "PAN format verified successfully"}


# =====================================================
# WORKER 2 — CREDIT / ELIGIBILITY AGENT
# =====================================================
def check_eligibility(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    NBFC-style affordability and risk evaluation.
    Returns explainable metrics for the Master Agent.
    """
    income = float(data.get("monthly_income", 0))
    existing_emi = float(data.get("existing_emi", 0))
    requested_amount = float(data.get("requested_amount", 0))
    tenure = int(data.get("tenure", 60))

    # ---------- Guardrails ----------
    if income < 25000:
        return {
            "eligible": False,
            "approved_amount": 0,
            "reason": "Monthly income below minimum eligibility threshold",
            "risk_band": "HIGH",
        }

    if tenure <= 0:
        return {
            "eligible": False,
            "approved_amount": 0,
            "reason": "Invalid loan tenure",
            "risk_band": "HIGH",
        }

    # ---------- EMI Approximation ----------
    proposed_emi = requested_amount / tenure

    # ---------- FOIR ----------
    foir = (existing_emi + proposed_emi) / income

    if foir > 0.45:
        return {
            "eligible": False,
            "approved_amount": 0,
            "reason": "FOIR too high based on existing obligations",
            "foir": round(foir, 2),
            "risk_band": "HIGH",
        }

    # ---------- Risk Band ----------
    risk_band = "LOW" if foir <= 0.30 else "MEDIUM"

    # ---------- Max Eligibility (Upsell Logic) ----------
    max_affordable_emi = income * 0.45 - existing_emi
    max_eligible_amount = int(max_affordable_emi * tenure)

    approved_amount = min(int(requested_amount), max_eligible_amount)

    return {
        "eligible": True,
        "approved_amount": approved_amount,
        "requested_amount": int(requested_amount),
        "foir": round(foir, 2),
        "risk_band": risk_band,
        "max_eligible_amount": max_eligible_amount,
        "reason": "Eligible based on income, obligations, and tenure",
    }


# =====================================================
# WORKER 3 — SANCTION LETTER AGENT
# =====================================================
def generate_sanction_letter(data: Dict[str, Any]) -> Dict[str, Any]:
    from reportlab.platypus import (
        SimpleDocTemplate,
        Paragraph,
        Table,
        TableStyle,
        Spacer,
        Image,
    )
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors

    # ---------- INPUT ----------
    raw_name = data["customer_name"]
    name = " ".join(word.capitalize() for word in raw_name.split())

    amount = int(data["approved_amount"])
    rate = float(data.get("interest_rate", 12.0))
    tenure = int(data.get("tenure_months", 60))
    today = datetime.now().strftime("%d %b %Y")

    safe_name = name.replace(" ", "_")
    file_path = f"{OUTPUT_DIR}/sanction_{safe_name}.pdf"

    # ---------- DOCUMENT ----------
    doc = SimpleDocTemplate(
        file_path,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=28,
        bottomMargin=36,
    )

    styles = getSampleStyleSheet()

    styles.add(
        ParagraphStyle(
            name="TitleCenter",
            alignment=TA_CENTER,
            fontSize=18,
            leading=22,
            fontName="Helvetica-Bold",
            spaceAfter=8,
        )
    )

    styles.add(
        ParagraphStyle(
            name="SubTitleCenter",
            alignment=TA_CENTER,
            fontSize=12,
            leading=14,
            fontName="Helvetica-Bold",
            spaceAfter=16,
        )
    )

    styles.add(
        ParagraphStyle(
            name="BodyTextCustom",
            alignment=TA_LEFT,
            fontSize=11,
            leading=14,
            spaceAfter=10,
        )
    )

    elements = []

    # ---------- LOGO ----------
    if os.path.exists(LOGO_PATH):
        logo = Image(LOGO_PATH, width=140, height=50)
        logo.hAlign = "CENTER"
        elements.append(logo)
        elements.append(Spacer(1, 6))

    # ---------- HEADER ----------
    elements.append(Paragraph("LOAN SANCTION LETTER", styles["TitleCenter"]))
    elements.append(Paragraph(NBFC_NAME, styles["SubTitleCenter"]))

    elements.append(HRFlowable(width="100%", thickness=0.8, color=colors.grey))
    elements.append(Spacer(1, 16))

    # ---------- BORROWER DETAILS ----------
    borrower_table = Table(
        [
            ["Borrower Name", name],
            ["Sanction Date", today],
            ["Loan Type", "Personal Loan"],
        ],
        colWidths=[160, 340],
    )

    borrower_table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),
                ("PADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )

    elements.append(borrower_table)
    elements.append(Spacer(1, 20))

    # ---------- KEY FACT SHEET ----------
    elements.append(Paragraph("KEY FACT SHEET", styles["BodyTextCustom"]))
    elements.append(Spacer(1, 6))

    kfs_table = Table(
        [
           ["Approved Amount", f"INR {amount:,}"],

            ["Interest Rate", f"{rate:.2f}% per annum"],
            ["Tenure", f"{tenure} months"],
            ["Repayment Mode", "Monthly EMI"],
            ["Interest Type", "Fixed"],
        ],
        colWidths=[200, 300],
    )

    kfs_table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),
                ("PADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )

    elements.append(kfs_table)
    elements.append(Spacer(1, 20))

    # ---------- DISCLAIMER ----------
    elements.append(
        Paragraph(
            "This loan is sanctioned subject to completion of documentation, "
            "verification, and internal credit policies of the company. "
            "This is a system-generated document and does not require a physical signature.",
            styles["BodyTextCustom"],
        )
    )

    elements.append(Spacer(1, 30))
    elements.append(HRFlowable(width="100%", thickness=0.6, color=colors.lightgrey))
    elements.append(Spacer(1, 16))

    # ---------- SIGNATURE ----------
    elements.append(Paragraph(f"For {NBFC_NAME}", styles["BodyTextCustom"]))
    elements.append(Paragraph("Authorized Credit Team", styles["BodyTextCustom"]))

    # ---------- BUILD ----------
    doc.build(elements)

    # ---------- ENCRYPT ----------
    reader = PdfReader(file_path)
    writer = PdfWriter()

    for page in reader.pages:
        writer.add_page(page)

    password = name.split()[0].lower()
    writer.encrypt(password)

    with open(file_path, "wb") as f:
        writer.write(f)

    # ---------- RESPONSE ----------
    return {
        "letter_url": f"/generated_letters/{os.path.basename(file_path)}",
        "password": password,
        "meta": {
            "customer_name": name,
            "approved_amount": amount,
            "interest_rate": rate,
            "tenure_months": tenure,
        },
    }
