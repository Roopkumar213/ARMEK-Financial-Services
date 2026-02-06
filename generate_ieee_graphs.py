import pandas as pd
import matplotlib.pyplot as plt
import os

def generate_ieee_visuals():
    os.makedirs("ieee_figures", exist_ok=True)
    
    # Load Data
    try:
        df = pd.read_csv("logs/final_decisions_primary.csv")
    except FileNotFoundError:
        print("Error: logs/final_decisions_primary.csv not found.")
        return

    # METRICS CALCULATION
    total_input = len(df)
    
    # Rejection Counts
    rejected_eligibility = len(df[df['rejection_stage'] == 'EligibilityAgent'])
    rejected_risk = len(df[df['rejection_stage'] == 'CreditBureauAgent'])
    accepted = len(df[df['final_status'] == 'ACCEPTED'])
    
    # Funnel logic
    stage_1_input = total_input
    stage_2_assessment = total_input - rejected_eligibility
    stage_3_approved = accepted # Assessment passed = Approved (since no downstream stages in this simplified view)
    
    # ==========================================
    # GRAPH 1: PROCESSING WORKFLOW FUNNEL
    # Demonstrates "Early Gating Efficiency"
    # ==========================================
    stages = ['Application\nReceived', 'Eligibility\nScreening', 'Final\nApproval']
    values = [stage_1_input, stage_2_assessment, stage_3_approved]
    
    plt.figure(figsize=(6, 4))
    bars = plt.bar(stages, values, color=['#404040', '#808080', '#C0C0C0'], edgecolor='black', width=0.6)
    
    plt.ylabel('Application Volume (N)')
    # plt.title('Workflow Volume Reduction') # Forbidden by constraints
    
    # Add count labels
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + 15,
                f'{height}', ha='center', va='bottom', fontsize=10, fontweight='bold')
                
    # Add reduction labels
    reduction_1 = ((stage_1_input - stage_2_assessment) / stage_1_input) * 100
    reduction_2 = ((stage_2_assessment - stage_3_approved) / stage_2_assessment) * 100
    
    # Annotation arrows or text could be messy, keeping it clean per IEEE spec.
        
    plt.ylim(0, 1100)
    plt.grid(axis='y', linestyle='--', alpha=0.3)
    plt.tight_layout()
    plt.savefig('ieee_figures/ieee_workflow_funnel.png', dpi=300)
    plt.close()
    
    print(f"Generated Funnel: {values}")

    # ==========================================
    # GRAPH 2: REJECTION SOURCE DISTRIBUTION
    # Demonstrates "Hybrid Filtering" (Rule vs Model)
    # ==========================================
    
    labels = ['Eligibility Rules\n(Deterministic)', 'Risk Assessment\n(Stochastic)']
    counts = [rejected_eligibility, rejected_risk]
    
    plt.figure(figsize=(5, 4))
    bars = plt.bar(labels, counts, color=['#606060', '#A0A0A0'], edgecolor='black', width=0.5)
    
    plt.ylabel('Rejected Applications (N)')
    # plt.xlabel('Rejection Source')
    
    # Add labels
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + 10,
                f'{height}', ha='center', va='bottom', fontsize=10, fontweight='bold')
                
    # Calculate % of total rejections
    total_rejected = rejected_eligibility + rejected_risk
    if total_rejected > 0:
        pct_elig = (rejected_eligibility / total_rejected) * 100
        pct_risk = (rejected_risk / total_rejected) * 100
        
        plt.text(0, rejected_eligibility/2, f"{pct_elig:.1f}%", ha='center', color='white', fontweight='bold')
        plt.text(1, rejected_risk/2, f"{pct_risk:.1f}%", ha='center', color='black', fontweight='bold')

    plt.ylim(0, max(counts) * 1.15)
    plt.grid(axis='y', linestyle='--', alpha=0.3)
    plt.tight_layout()
    plt.savefig('ieee_figures/ieee_rejection_source.png', dpi=300)
    plt.close()
    
    print(f"Generated Rejection Dist: {counts}")

if __name__ == "__main__":
    generate_ieee_visuals()
