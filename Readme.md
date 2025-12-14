ARMEK Financial Services

Personal Loan Sales Assistant (Agentic AI)

Overview

ARMEK Financial Services is a web-based personal loan sales chatbot built using an Agentic AI architecture.
The system simulates an NBFC-style digital sales officer that guides customers through the complete loan journey — from initial interaction to automated sanction letter generation.

The solution replaces static forms with a conversational interface while keeping credit evaluation, decisioning, and documentation deterministic and explainable.

Problem Statement

NBFCs rely heavily on static application forms and human agents for personal loan sales, resulting in:

Low conversion rates

High operational cost

Delayed eligibility identification

Poor customer experience during loan discovery

The objective is to design an AI-driven conversational system that improves conversion while maintaining compliance and decision transparency.

Solution Approach

The system follows a Master–Worker Agent design:

A single Master Agent interacts with the customer

Multiple Worker Agents perform backend tasks

The Master Agent orchestrates the flow and translates decisions into user-friendly responses

This ensures separation of concerns, explainability, and extensibility.

System Architecture
User
 ↓
Web Chat UI (React)
 ↓
Master Agent (FastAPI)
 ↓
-------------------------------------------------
| KYC Worker | Credit Worker | Document Worker |
-------------------------------------------------
 ↓
Approval Decision + Sanction Letter

Core Capabilities
Conversational Flow

Guided, step-by-step interaction

Context retained across messages

Handles corrections without restarting the flow

Verification

PAN format validation (demo scope)

KYC handled by a dedicated worker agent

Credit Evaluation

Income threshold checks

FOIR-based affordability logic

Risk band classification (Low / Medium / High)

Maximum eligible amount computation

Automation

Instant approval or rejection

Automated PDF sanction letter

Password-protected document delivery

Sanction Letter Generation

Professionally formatted PDF

Company branding and logo

Key Fact Sheet included

Encrypted using borrower’s first name

System-generated, no physical signature required

Technology Stack
Backend

Python

FastAPI

ReportLab (PDF generation)

PyPDF (encryption)

Frontend

React (Create React App)

Fetch API

Responsive UI

Repository Structure
ARMEK-Financial-Services/
├── backend/
│   ├── main.py
│   ├── agents.py
│   ├── workers.py
│   ├── static/
│   └── generated_letters/
│
├── prototype/
│   ├── src/
│   └── public/
│
└── README.md

End-to-End Flow

User initiates conversation

Name and PAN captured

Financial details collected

Credit eligibility evaluated

Approval decision generated

Sanction letter issued

Disclaimer

This project is a prototype built for demonstration and evaluation purposes only.
All credit rules, KYC checks, and approval logic are simulated and do not represent real NBFC policies.

Author

Roop Kumar
B.Tech – Computer Science Engineering