import React, { useState, useEffect } from 'react';

const LoanWizard = ({ onComplete }) => {
    const [step, setStep] = useState(1);
    const [formData, setFormData] = useState({
        amount: '', tenure: '',
        income: '', pan: '',
    });

    const handleNext = () => {
        if (step < 3) setStep(step + 1);
    };

    const handleSubmit = () => {
        setStep(3); // Moving to processing
        onComplete(formData); // Trigger backend orchestration
    };

    return (
        <div style={styles.container}>
            <div style={styles.card}>
                {/* Progress Bar */}
                <div style={styles.progressTrack}>
                    <div style={{ ...styles.progressBar, width: `${(step / 3) * 100}%` }} />
                </div>

                <div style={styles.content}>
                    {step === 1 && (
                        <StepAmount
                            data={formData}
                            onChange={setFormData}
                            onNext={handleNext}
                        />
                    )}
                    {step === 2 && (
                        <StepProfile
                            data={formData}
                            onChange={setFormData}
                            onNext={handleSubmit}
                        />
                    )}
                    {step === 3 && (
                        <StepProcessing />
                    )}
                </div>
            </div>
        </div>
    );
};

const StepAmount = ({ data, onChange, onNext }) => {
    const valid = data.amount && data.tenure;
    return (
        <div style={styles.stepContainer}>
            <h2 style={styles.h2}>How much do you need?</h2>
            <p style={styles.p}>We offer loans from ₹10,000 to ₹5,00,000.</p>

            <div style={styles.field}>
                <label style={styles.label}>Loan Amount (₹)</label>
                <input
                    style={styles.inputHuge} type="number"
                    value={data.amount} placeholder="50000"
                    onChange={e => onChange({ ...data, amount: e.target.value })}
                    autoFocus
                />
            </div>

            <div style={styles.field}>
                <label style={styles.label}>Tenure (Months)</label>
                <select
                    style={styles.select}
                    value={data.tenure}
                    onChange={e => onChange({ ...data, tenure: e.target.value })}
                >
                    <option value="">Select tenure</option>
                    <option value="6">6 Months</option>
                    <option value="12">12 Months</option>
                    <option value="24">24 Months</option>
                    <option value="36">36 Months</option>
                </select>
            </div>

            <button style={valid ? styles.btnPrimary : styles.btnDisabled} onClick={valid ? onNext : null}>
                Continue
            </button>
        </div>
    )
};

const StepProfile = ({ data, onChange, onNext }) => {
    const valid = data.income && data.pan && data.pan.length === 10;
    return (
        <div style={styles.stepContainer}>
            <h2 style={styles.h2}>Tell us about yourself</h2>
            <p style={styles.p}>We need a few details to verify your eligibility.</p>

            <div style={styles.field}>
                <label style={styles.label}>Monthly Income (₹)</label>
                <input
                    style={styles.input} type="number"
                    value={data.income} placeholder="e.g. 85000"
                    onChange={e => onChange({ ...data, income: e.target.value })}
                />
            </div>

            <div style={styles.field}>
                <label style={styles.label}>PAN Number</label>
                <input
                    style={styles.input}
                    value={data.pan} placeholder="ABCDE1234F"
                    maxLength={10}
                    onChange={e => onChange({ ...data, pan: e.target.value.toUpperCase() })}
                />
            </div>

            <button style={valid ? styles.btnPrimary : styles.btnDisabled} onClick={valid ? onNext : null}>
                Submit Application
            </button>
        </div>
    )
};

const StepProcessing = () => {
    // This is purely visual. The parent component handles the actual backend state & transition.
    return (
        <div style={styles.processingContainer}>
            <div style={styles.loaderPulse} />
            <h3 style={styles.procTitle}>Verifying your details...</h3>
            <p style={styles.procSub}>This usually takes less than a minute. Please do not close this window.</p>

            <div style={styles.checks}>
                <CheckItem label="Checking eligibility" delay="0s" />
                <CheckItem label="Verifying credit history" delay="3s" />
                <CheckItem label="Calculating best offer" delay="6s" />
            </div>
        </div>
    )
};

const CheckItem = ({ label, delay }) => (
    <div style={{ ...styles.checkItem, animationDelay: delay }}>
        <span style={{ color: '#2563EB' }}>✓</span> {label}
    </div>
);


const styles = {
    container: {
        display: 'flex', justifyContent: 'center', paddingTop: 40,
    },
    card: {
        width: '100%', maxWidth: 640,
        background: 'white',
        borderRadius: 24,
        boxShadow: '0 10px 40px -10px rgba(0,0,0,0.1)',
        overflow: 'hidden',
    },
    progressTrack: {
        height: 6, background: '#F3F4F6',
    },
    progressBar: {
        height: '100%', background: '#2563EB', transition: 'width 0.4s ease',
    },
    content: {
        padding: 48,
    },
    stepContainer: {
        display: 'flex', flexDirection: 'column', gap: 24,
    },
    h2: { fontSize: 28, fontWeight: 700, margin: 0 },
    p: { fontSize: 16, color: '#6B7280', margin: 0 },
    field: { display: 'flex', flexDirection: 'column', gap: 8 },
    label: { fontSize: 13, fontWeight: 600, color: '#374151', textTransform: 'uppercase', letterSpacing: '0.05em' },
    input: { padding: 16, borderRadius: 12, border: '1px solid #E5E7EB', fontSize: 16, outline: 'none' },
    inputHuge: { padding: 16, borderRadius: 12, border: '1px solid #E5E7EB', fontSize: 32, fontWeight: 600, outline: 'none' },
    select: { padding: 16, borderRadius: 12, border: '1px solid #E5E7EB', fontSize: 16, outline: 'none', background: 'white' },
    btnPrimary: { padding: 18, borderRadius: 12, border: 'none', background: '#2563EB', color: 'white', fontSize: 16, fontWeight: 600, cursor: 'pointer', marginTop: 16 },
    btnDisabled: { padding: 18, borderRadius: 12, border: 'none', background: '#E5E7EB', color: '#9CA3AF', fontSize: 16, fontWeight: 600, cursor: 'not-allowed', marginTop: 16 },

    processingContainer: { textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '24px 0' },
    loaderPulse: { width: 64, height: 64, borderRadius: '50%', background: '#DBEAFE', animation: 'pulse 1.5s infinite', marginBottom: 24 },
    procTitle: { fontSize: 20, fontWeight: 600, marginBottom: 8 },
    procSub: { fontSize: 14, color: '#6B7280', marginBottom: 32 },
    checks: { display: 'flex', flexDirection: 'column', gap: 12, alignItems: 'flex-start' },
    checkItem: { display: 'flex', gap: 12, fontSize: 14, color: '#4B5563', opacity: 0, animation: 'fadeIn 0.5s forwards' },
};

/* --- Global animations required in index.css for full effect, adding backup styles here --- */
document.head.insertAdjacentHTML("beforeend", `<style>
@keyframes pulse { 0% { transform: scale(0.95); opacity: 0.5; } 50% { transform: scale(1.05); opacity: 0.8; } 100% { transform: scale(0.95); opacity: 0.5; } }
@keyframes fadeIn { to { opacity: 1; } }
</style>`)

export default LoanWizard;
