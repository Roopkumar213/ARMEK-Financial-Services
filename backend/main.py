# main.py
import logging
import re
from typing import Dict, Any, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv
import uvicorn

from workers import verify_customer, check_eligibility, generate_sanction_letter

# ---------- Setup ----------
load_dotenv()
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="NBFC Agentic Loan Assistant API")

app.mount(
    "/generated_letters",
    StaticFiles(directory="generated_letters"),
    name="generated_letters"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Models ----------
class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatResponse(BaseModel):
    reply: str
    stage: str
    ui_action: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


# ---------- Session Store ----------
SESSIONS: Dict[str, Dict[str, Any]] = {}


def get_session(session_id: str):
    if session_id not in SESSIONS:
        SESSIONS[session_id] = {
            "stage": "ASK_NAME",
            "customer": {},
            "history": []
        }
    return SESSIONS[session_id]


# ---------- Name Validation ----------
def is_valid_name(text: str) -> bool:
    text = text.strip().lower()

    invalid = {"hi", "hello", "hey", "yo", "bro", "hii", "hai"}
    if text in invalid:
        return False

    if not re.match(r"^[a-zA-Z ]+$", text):
        return False

    if len(text.split()) < 2:
        return False

    return True


# ---------- Chat ----------
@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    session = get_session(req.session_id)
    text = req.message.strip()
    stage = session["stage"]

    session["history"].append({"role": "user", "content": text})

    # ---------- ASK NAME ----------
    if stage == "ASK_NAME":
        if not is_valid_name(text):
            reply = "To get started, please enter your full name (for example: Rahul Sharma)."
        else:
            session["customer"]["name"] = text
            session["stage"] = "ASK_PAN"
            reply = (
                f"Thanks {text}. I’ll start your loan application.\n\n"
                "Please share your PAN number for identity verification."
            )

    # ---------- ASK PAN ----------
    elif stage == "ASK_PAN":
        pan = text.replace(" ", "").upper()

        if not re.match(r"^[A-Z]{5}[0-9]{4}[A-Z]$", pan):
            reply = "Please enter a valid PAN number (example: ABCDE1234F)."
        else:
            result = verify_customer({"pan": pan})

            if not result["verified"]:
                session["stage"] = "REJECTED"
                reply = "❌ PAN verification failed. Please double-check the PAN number."
            else:
                session["customer"]["pan"] = pan
                session["stage"] = "ASK_INCOME"
                reply = (
                    "✅ Your PAN has been successfully verified.\n\n"
                    "I’ll now gather a few financial details to evaluate your loan eligibility.\n"
                    "What is your monthly income?"
                )

    # ---------- ASK INCOME ----------
    elif stage == "ASK_INCOME":
        if not text.isdigit():
            reply = "Please enter your monthly income as a number (for example: 50000)."
        else:
            session["customer"]["income"] = int(text)
            session["stage"] = "ASK_EMI"
            reply = (
                "Got it.\n\n"
                "Do you currently have any existing EMIs? "
                "If yes, enter the amount. Otherwise, type 'none'."
            )

    # ---------- ASK EMI ----------
    elif stage == "ASK_EMI":
        if text.lower() == "none":
            session["customer"]["emi"] = 0
        elif text.isdigit():
            session["customer"]["emi"] = int(text)
        else:
            return ChatResponse(
                reply="Please enter a valid EMI amount or type 'none'.",
                stage=stage
            )

        session["stage"] = "ASK_AMOUNT"
        reply = (
            "Thanks.\n\n"
            "How much loan amount are you looking for?"
        )

    # ---------- ASK AMOUNT ----------
    elif stage == "ASK_AMOUNT":
        if not text.isdigit():
            reply = "Please enter the loan amount as a number (for example: 100000)."
        else:
            session["customer"]["amount"] = int(text)
            session["stage"] = "ASK_TENURE"
            reply = (
                "Noted.\n\n"
                "What loan tenure do you prefer? "
                "(For example: 12, 24, or 36 months)"
            )

    # ---------- ASK TENURE ----------
    elif stage == "ASK_TENURE":
        if not text.isdigit():
            reply = "Please enter the tenure in months (numbers only)."
        else:
            tenure = int(text)
            c = session["customer"]

            reply_prefix = (
                "Thanks. I’m now running a quick eligibility and credit assessment "
                "based on the details you shared.\n\n"
            )

            eligibility = check_eligibility({
                "monthly_income": c["income"],
                "existing_emi": c["emi"],
                "requested_amount": c["amount"],
                "tenure": tenure,
            })

            if not eligibility["eligible"]:
                session["stage"] = "REJECTED"
                reply = (
                    reply_prefix +
                    f"❌ At the moment, your application does not meet our criteria.\n\n"
                    f"Reason: {eligibility['reason']}.\n\n"
                    "You may improve eligibility by choosing a longer tenure "
                    "or reducing the loan amount."
                )
            else:
                approved_amount = eligibility["approved_amount"]

                letter = generate_sanction_letter({
                    "customer_name": c["name"],
                    "approved_amount": approved_amount,
                    "interest_rate": 12.0,
                    "tenure_months": tenure,
                })

                session["stage"] = "COMPLETED"
                session["letter_url"] = letter["letter_url"]

                reply = (
                    reply_prefix +
                    "🎉 Good news! Your loan has been approved.\n\n"
                    f"✅ Approved Amount: ₹{approved_amount:,}\n"
                    f"✅ Tenure: {tenure} months\n"
                    "✅ Interest Rate: 12% per annum\n\n"
                    "Based on your profile, your EMI comfortably fits within "
                    "our internal affordability checks.\n\n"
                    "📄 You can download your sanction letter below."
                )

                return ChatResponse(
                    reply=reply,
                    stage="COMPLETED",
                    ui_action="SHOW_SANCTION_DOWNLOAD",
                    data={"letter_url": letter["letter_url"]},
                )

    # ---------- COMPLETED ----------
    elif stage == "COMPLETED":
        return ChatResponse(
            reply=(
                "Your loan process is already complete.\n\n"
                "📄 You can download your sanction letter below."
            ),
            stage="COMPLETED",
            ui_action="SHOW_SANCTION_DOWNLOAD",
            data={"letter_url": session.get("letter_url")},
        )

    # ---------- REJECTED ----------
    else:
        reply = (
            "We’re unable to proceed further with this application at the moment.\n\n"
            "If you’d like, you can restart the journey with updated details."
        )

    session["history"].append({"role": "assistant", "content": reply})
    return ChatResponse(reply=reply, stage=session["stage"])



if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
