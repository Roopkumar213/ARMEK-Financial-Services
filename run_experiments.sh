#!/bin/bash
# IEEE Reproducibility Script
# This script executes the full experimental pipeline.

echo "[1/4] Generating Grounded Dataset (N=1000)..."
python generate_evidence_data.py

echo "[2/4] Running Primary Evaluation (Realistic)..."
python run_primary_validation.py

echo "[3/4] Running Adversarial Stress Test..."
python run_stress_validation.py

echo "[4/4] Generating Figures and Tables..."
python generate_paper_artifacts.py

echo "Use 'logs/' for raw data and 'figures/' for plots."
