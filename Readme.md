🏦 ARMEK Financial Services
Agentic AI–Powered Personal Loan Assistant
<p align="center"> <strong>Human-like • Agentic • End-to-End • NBFC-Style Loan Automation</strong> </p>
🚀 Overview

ARMEK Financial Services is a web-based Agentic AI personal loan sales chatbot designed to simulate a real NBFC loan officer.

It replaces static forms and heavy human-agent dependency with a conversational, intelligent, and explainable digital sales assistant that guides users from greeting to sanction letter generation in one seamless flow.

🧩 Problem Statement

A large NBFC operating across India wants to increase personal loan conversion rates while reducing reliance on human agents and static application forms.

Key Challenges

Low conversion from form-based journeys

High cost of manual agent handling

Poor customer engagement during loan discovery

Delayed eligibility identification

💡 Proposed Solution

ARMEK implements a Master–Worker Agent architecture where:

A Master Agent handles all customer-facing conversation

Multiple Worker Agents execute specialized backend tasks

Internal decisions are translated into simple, human-friendly responses

This results in:

Faster decisions

Better UX

Automated approvals

Professional sanction documentation

🧠 Agentic AI Architecture
Customer
   │
   ▼
Web Chat UI (React)
   │
   ▼
Master Agent (FastAPI)
   │
   ├── KYC / Verification Worker
   ├── Credit & Eligibility Worker
   └── Sanction Letter Worker
   │
   ▼
Approval Decision + PDF Sanction Letter

Design Principles

Single conversational authority (Master Agent)

Clear separation of responsibilities

Explainable credit decisions

Deterministic, demo-safe logic

✨ Core Features
🤝 Conversational Sales Journey

Human-like greetings and probing questions

Step-by-step guided data capture

Context retention across messages

Smooth handling of corrections

🤖 Agentic Intelligence

Master Agent orchestrates the journey

Worker Agents handle:

PAN/KYC verification

Credit & FOIR evaluation

Risk banding

Document generation

💳 Credit & Eligibility Logic
Rule	Description
Income Threshold	Minimum ₹25,000/month
FOIR	≤ 45%
Risk Bands	LOW / MEDIUM / HIGH
Upsell Logic	Calculates max eligible amount
📄 Automated Sanction Letter

Professionally formatted PDF

Company branding and logo

Key Fact Sheet included

Password-protected (first name, lowercase)

System-generated disclaimer

🖥️ Web Interface

Modern chatbot UI (React)

Real-time responses

Persistent sanction letter download

Stage indicators (Name → PAN → Income → Approval)

Mobile-friendly and responsive

🛠 Tech Stack
Backend

Python

FastAPI

ReportLab (PDF generation)

PyPDF (encryption)

Agent-based orchestration

Frontend

React (CRA)

Fetch API

Responsive UI

📂 Repository Structure
ARMEK-Financial-Services/
│
├── backend/
│   ├── main.py              # API + orchestration
│   ├── agents.py            # Master Agent (language layer)
│   ├── workers.py           # Worker agents
│   ├── static/
│   │   └── nbfc_logo.png
│   └── generated_letters/
│       └── .gitkeep
│
├── prototype/               # Frontend (React)
│   ├── src/
│   │   └── components/
│   │       └── ChatbotPage.js
│   └── public/
│
└── README.md

▶️ End-to-End Demo Flow

User opens chatbot

Master Agent greets and captures name

PAN verification (KYC Worker)

Income and EMI capture

Credit evaluation (Credit Worker)

Approval or rejection decision

Sanction letter generated (Document Worker)

User downloads encrypted PDF

🏆 Why This Project Stands Out

True Agentic AI (not a single chatbot function)

Clean Master–Worker orchestration

End-to-end automation (not just eligibility)

Professional UI + document output

Explainable decisioning

Built like a real NBFC product, not a toy demo

⚠️ Disclaimer

This project is a prototype for demonstration purposes only.
All credit rules, KYC checks, and approval logic are simulated and do not represent real NBFC policies.

👤 Author

Roop Kumar
B.Tech CSE
Agentic AI & Full Stack Development