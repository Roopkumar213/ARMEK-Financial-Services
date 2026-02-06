import pandas as pd
import matplotlib.pyplot as plt
import json
import os
import sys

# Ensure backend path is available if needed (mostly for types, but we load CSVs here)
sys.path.append(os.path.join(os.getcwd(), 'backend'))

def generate_artifacts():
    os.makedirs("figures", exist_ok=True)
    
    # LOAD DATA
    with open("data/grounded_users.json", "r") as f:
        users_data = json.load(f)
    df_users = pd.DataFrame(users_data)
    # df_users keys: user_id, stated_income, etc. metadata is a dict
    df_users['category'] = df_users['metadata'].apply(lambda x: x['category'])
    
    df_primary = pd.read_csv("logs/final_decisions_primary.csv")
    df_stress = pd.read_csv("logs/final_decisions_stress.csv")
    
    # ==========================================
    # FIGURE 1: DATASET CATEGORY DISTRIBUTION
    # ==========================================
    files = {}
    
    plt.figure(figsize=(10, 6))
    cat_counts = df_users['category'].value_counts()
    cat_counts.plot(kind='bar', color=['#3b82f6', '#10b981', '#ef4444', '#f59e0b', '#6366f1'])
    plt.title('Figure 1: Grounded Dataset Category Distribution (N=1000)')
    plt.ylabel('Count')
    plt.xlabel('User Category')
    plt.tight_layout()
    plt.savefig('figures/figure1_dataset.png')
    plt.close()
    
    # TABLE I Data
    print("### Table I — Dataset Composition")
    print("| Category | Count | Percentage |")
    print("|---|---|---|")
    total = len(df_users)
    for cat, count in cat_counts.items():
        print(f"| {cat} | {count} | {count/total*100:.1f}% |")
    print("\n")

    # ==========================================
    # FIGURE 2: REJECTION FUNNEL (PRIMARY)
    # ==========================================
    # We need counts of Accepted, Rejected (Eligibility), Rejected (Fraud), Rejected (Other)
    # Rejection Stage in Log: 'EligibilityAgent', 'CreditBureauAgent', 'None' (Accepted)
    
    funnel_counts = df_primary['rejection_stage'].value_counts()
    # Ensure all keys exist
    for key in ['None', 'EligibilityAgent', 'CreditBureauAgent']:
        if key not in funnel_counts: funnel_counts[key] = 0
        
    stages = ['Accepted', 'Rejected (Eligibility)', 'Rejected (Fraud/Risk)']
    values = [funnel_counts['None'], funnel_counts['EligibilityAgent'], funnel_counts['CreditBureauAgent']]
    
    plt.figure(figsize=(8, 6))
    plt.bar(stages, values, color=['#10b981', '#6b7280', '#ef4444'])
    plt.title('Figure 2: Primary Evaluation Rejection Funnel')
    plt.ylabel('User Count')
    for i, v in enumerate(values):
        plt.text(i, v + 10, str(v), ha='center')
    plt.tight_layout()
    plt.savefig('figures/figure2_funnel.png')
    plt.close()
    
    # TABLE IV Data
    print("### Table IV — Rejection Funnel (Primary)")
    print("| Stage | Count | Percentage |")
    print("|---|---|---|")
    print(f"| Accepted | {values[0]} | {values[0]/total*100:.1f}% |")
    print(f"| Rejected (Eligibility) | {values[1]} | {values[1]/total*100:.1f}% |")
    print(f"| Rejected (Fraud/Risk) | {values[2]} | {values[2]/total*100:.1f}% |")
    print("\n")

    # ==========================================
    # FIGURE 3: FRAUD DETECTION OUTCOMES
    # ==========================================
    # Filter for FRAUD users only in Primary
    # We join with users data to know who is fraud, or rely on 'category' column in csv if available.
    # The CSV has 'category' column.
    
    fraud_df = df_primary[df_primary['category'] == 'Fraud']
    injected = len(fraud_df)
    detected = len(fraud_df[fraud_df['fraud_flag'] == True])
    missed = injected - detected
    
    plt.figure(figsize=(6, 6))
    plt.bar(['Injected', 'Detected', 'Missed'], [injected, detected, missed], color=['#6366f1', '#10b981', '#ef4444'])
    plt.title('Figure 3: Fraud Detection Performance (Primary)')
    plt.ylabel('Count')
    plt.tight_layout()
    plt.savefig('figures/figure3_fraud.png')
    plt.close()
    
    # TABLE III Data
    # Calculate FPR: False Positives / Total Non-Fraud
    non_fraud_df = df_primary[df_primary['category'] != 'Fraud']
    honest_n = len(non_fraud_df)
    fps = len(non_fraud_df[non_fraud_df['fraud_flag'] == True])
    fpr = (fps/honest_n)*100 if honest_n > 0 else 0
    
    print("### Table III — Fraud Detection Performance (Primary)")
    print(f"| Metric | Value |")
    print("|---|---|")
    print(f"| Injected Fraud | {injected} |")
    print(f"| Detected Fraud | {detected} |")
    print(f"| Missed Fraud | {missed} |")
    print(f"| Recall | {detected/injected*100:.2f}% |")
    print(f"| False Positive Rate | {fpr:.2f}% |")
    print("\n")
    
    # TABLE II Data
    accepted_n = len(df_primary[df_primary['final_status'] == 'ACCEPTED'])
    rejected_n = len(df_primary[df_primary['final_status'] == 'REJECTED'])
    print("### Table II — Outcome Distribution (Primary)")
    print("| Outcome | Count | Percentage |")
    print("|---|---|---|")
    print(f"| Accepted | {accepted_n} | {accepted_n/total*100:.1f}% |")
    print(f"| Rejected | {rejected_n} | {rejected_n/total*100:.1f}% |")
    print("\n")

    # ==========================================
    # FIGURE 4: PRIMARY VS STRESS COMPARISON
    # ==========================================
    # Metrics: Acceptance Rate, Fraud Recall
    
    # Primary Metrics
    p_acc = (accepted_n / total) * 100
    p_rec = (detected / injected) * 100
    
    # Stress Metrics
    s_fraud = df_stress[df_stress['category'] == 'Fraud']
    s_detected = len(s_fraud[s_fraud['fraud_flag'] == True])
    s_acc_n = len(df_stress[df_stress['final_status'] == 'ACCEPTED'])
    
    s_acc = (s_acc_n / total) * 100
    s_rec = (s_detected / len(s_fraud)) * 100
    
    labels = ['Primary (Realistic)', 'Stress (Adversarial)']
    acc_scores = [p_acc, s_acc]
    rec_scores = [p_rec, s_rec]
    
    x = range(len(labels))
    width = 0.35
    
    plt.figure(figsize=(10, 6))
    fig, ax = plt.subplots()
    rects1 = ax.bar([i - width/2 for i in x], acc_scores, width, label='Acceptance Rate', color='#3b82f6')
    rects2 = ax.bar([i + width/2 for i in x], rec_scores, width, label='Fraud Recall', color='#ef4444')
    
    ax.set_ylabel('Percentage (%)')
    ax.set_title('Figure 4: Primary vs Stress Mode Comparison')
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.legend()
    
    plt.tight_layout()
    plt.savefig('figures/figure4_comparison.png')
    plt.close()

    # TABLE V Data
    s_rej_n = len(df_stress[df_stress['final_status'] == 'REJECTED'])
    print("### Table V — Stress Test Summary")
    print("| Metric | Value |")
    print("|---|---|")
    print(f"| Fraud Recall | {s_rec:.2f}% |")
    print(f"| Rejection Rate | {s_rej_n/total*100:.1f}% |")
    print("\n")

if __name__ == "__main__":
    generate_artifacts()
