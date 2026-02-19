# Early-Stage Loan Underwriting Using Agentic Master-Worker Conversational Orchestration

**NCRICCT'26 Conference Paper** | **Kuppam Engineering College**

---

## Overview

Production implementation of the Master-Worker agent architecture for conversational loan underwriting presented in the NCRICCT'26 paper. Demonstrates **47% early eligibility rejection rate** and **₹73,461 cost savings per 1,000 applications** through centralized orchestration and conditional execution.

**Key Paper Results Reproduced**:
- 47% reduction in credit bureau calls (530 vs 1,000 baseline)
- 94.7% precision/recall at eligibility gating stage  
- 84.05% fraud recall under stress conditions
- PLFS 2023-24 and CIBIL 2024-grounded evaluation (N=1,000)

---

## System Components

| Agent | Responsibility | Activation Condition |
|-------|---------------|-------------------|
| **Master Agent** | Conversation orchestration, workflow control | Always active |
| **Eligibility Worker** | Income/PAN screening | First user input |
| **KYC Worker** | Identity validation | Post-eligibility |
| **Credit Worker** | FOIR, risk scoring | Post-KYC |
| **Document Worker** | Sanction letter PDF | Final approval |

**Early rejection gate**: 47% applications terminated after minimal input, avoiding backend services.

---

## Paper Results

| Workflow | Credit Checks | Early Rejection | Cost/1K Apps |
|----------|---------------|----------------|--------------|
| Form-Based Baseline | 1,000 (100%) | 0% | ₹156,300 |
| Linear Chat Baseline | 1,000 (100%) | 0% | ₹156,300 |
| **Agentic System** | **530 (53%)** | **47%** | **₹82,839** |

**Savings**: **₹73,461 per 1,000 applications** (47% reduction)

---

## Technical Implementation

| Component | Technology |
|-----------|------------|
| Backend | Python 3.11, FastAPI |
| Chat UI | Streamlit |
| Dataset | PLFS/CIBIL-grounded synthetic generator |
| Validation | Ablation + stress test scripts |
| PDF Generation | ReportLab (sanction letters) |

---

## Quick Start

```bash
git clone https://github.com/RoopKumar3244/loan-agentic-underwriting
cd loan-agentic-underwriting
pip install -r requirements.txt

# Run full system
streamlit run streamlit_ui.py
Demo: http://localhost:8501

Reproduce Paper Evaluation
bash
# Generate paper dataset (N=1,000)
python generate_dataset.py --size 1000 --plfs-income --cibil-credit

# Run ablation study (Table V)
python run_validation.py --ablation

# Stress test (Table IV: 84.05% fraud recall)
python run_validation.py --stress
Expected: 47% early rejection, 94.7% gating precision, matches all paper tables.

File Structure
text
├── streamlit_ui.py          # Chat interface (Fig. 1)
├── master_agent.py         # Central orchestrator (Algorithm 1)
├── worker_agents.py        # KYC/Credit/Document workers
├── generate_dataset.py     # PLFS/CIBIL dataset (Table I)
├── run_validation.py       # Ablation/stress tests (Tables IV-VI)
├── grounded_users.json     # Paper evaluation data
└── README.md              # NCRICCT'26 reproducibility
Academic Validation
Dataset: Synthetic N=1,000 matching:

Income: PLFS 2023-24 (<₹25K: 14.3%)

Credit: CIBIL 2024 (<650: 13.2%)

Adversarial: 15% fraud cases

Validation: All paper claims reproducible via run_validation.py

Deployment Notes
Production requires:

Live CIBIL/Experian API (₹50/check)

Aadhaar e-KYC (₹6.30/check)

RBI-compliant data storage

Current: Research prototype with simulated services matching paper evaluation.

Author
A. Roop Kumar
Department of Computer Science and Engineering
Kuppam Engineering College, Kuppam, India
