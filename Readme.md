# ARMEK Financial Services  
Personal Loan Sales Assistant (Agentic AI)

---

## Overview

ARMEK Financial Services is a web-based personal loan sales chatbot built using an Agentic AI architecture.

The system simulates an NBFC-style digital loan officer that guides customers through the complete loan journey — from first interaction to automated sanction letter generation.

---

## Problem Statement

NBFCs depend heavily on static forms and human agents for personal loan sales, which leads to:

| Challenge | Impact |
|--------|--------|
| Static application forms | Low conversion rates |
| Manual agent handling | High operational cost |
| Late eligibility checks | Customer drop-offs |
| Poor loan discovery UX | Reduced trust |

---

## Solution Approach

The system follows a **Master–Worker Agent design**.

| Component | Responsibility |
|--------|----------------|
| Master Agent | Customer conversation and orchestration |
| KYC Worker | PAN verification (demo scope) |
| Credit Worker | Eligibility, FOIR, risk evaluation |
| Document Worker | Sanction letter generation |

All backend decisions are translated into simple, customer-friendly responses.

---

## System Architecture

User
↓
Web Chat UI (React)
↓
Master Agent (FastAPI)
↓
| KYC Worker | Credit Worker | Doc Worker |

↓
Decision + Sanction Letter


---

## Core Capabilities

### Conversation
- Guided, step-by-step flow  
- Context retained across messages  
- Handles corrections without restarting  

### Verification
- PAN format validation  
- Dedicated KYC worker agent  

### Credit Evaluation
- Income threshold checks  
- FOIR-based affordability logic  
- Risk band classification  
- Maximum eligible amount calculation  

### Automation
- Instant approval or rejection  
- Encrypted PDF sanction letter  

---

## Sanction Letter

- Professionally formatted PDF  
- Company branding and logo  
- Key Fact Sheet included  
- Password-protected (first name, lowercase)  
- System-generated (no physical signature)

---

## Technology Stack

| Layer | Tech |
|----|----|
| Backend | Python, FastAPI |
| PDF | ReportLab, PyPDF |
| Frontend | React (CRA) |
| Architecture | Agentic (Master–Worker) |

---



## End-to-End Flow

1. User initiates conversation  
2. Name and PAN captured  
3. Financial details collected  
4. Credit eligibility evaluated  
5. Approval decision generated  
6. Sanction letter issued  

---

## Disclaimer

This project is a prototype built for demonstration and evaluation purposes only.  
All credit rules and verification logic are simulated.

---

## Author

Roop Kumar  
B.Tech – Computer Science Engineering
