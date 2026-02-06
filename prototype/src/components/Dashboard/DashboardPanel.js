import React from 'react';

const DashboardPanel = ({ sessionState, sessionId, rejectionReason, sanctionUrl, onRestart, history }) => {
    const profile = sessionState?.profile || {};
    const status = rejectionReason ? 'Attention Needed' : (sanctionUrl ? 'Approved' : 'Application in Review');
    const subtext = rejectionReason ? 'We cannot proceed with your application at this time.' : (sanctionUrl ? 'Congratulations! Your loan offer is ready.' : 'We are verifying your details. This usually takes less than 2 minutes.');

    return (
        <div style={styles.container}>
            {/* 1. Hero Status */}
            <div style={styles.heroCard}>
                <div style={styles.statusIcon}>
                    {rejectionReason ? '⚠️' : (sanctionUrl ? '🎉' : '⏳')}
                </div>
                <div style={styles.heroContent}>
                    <h1 className="h2">{status}</h1>
                    <p className="body-sm">{subtext}</p>
                </div>
            </div>

            {/* 2. Applicant Snapshot (Readable) */}
            <h3 className="h3">Your Details</h3>
            <div style={styles.grid}>
                <InfoCard label="Annual Income" value={profile.monthly_income ? `₹${(Number(profile.monthly_income) * 12).toLocaleString()}` : '---'} />
                <InfoCard label="Loan Amount" value={profile.loan_amount ? `₹${Number(profile.loan_amount).toLocaleString()}` : '---'} />
                <InfoCard label="Monthly EMI" value={profile.existing_emi ? `₹${Number(profile.existing_emi).toLocaleString()}` : '---'} />
                <InfoCard label="Tenure" value={profile.tenure_months ? `${profile.tenure_months} months` : '---'} />
            </div>

            {/* 3. Live System Feed (Transparent AI) */}
            <div style={styles.progressCard}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
                    <h3 className="h3" style={{ margin: 0 }}>Processing Application</h3>
                    <div style={styles.liveBadge}>LIVE SYSTEM FEED</div>
                </div>

                <div style={styles.chatWindow}>
                    {/* Render History */}
                    {(history || []).slice(-6).map((msg, i) => (
                        <div key={i} style={{
                            ...styles.chatRow,
                            justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start'
                        }}>
                            <div style={{
                                ...styles.chatBubble,
                                background: msg.role === 'user' ? '#EFF6FF' : '#F9FAFB',
                                color: msg.role === 'user' ? '#1E40AF' : '#374151',
                                border: msg.role === 'user' ? '1px solid #BFDBFE' : '1px solid #E5E7EB'
                            }}>
                                {msg.role !== 'user' && <span style={styles.botLabel}>System: </span>}
                                {msg.content}
                            </div>
                        </div>
                    ))}
                    {(!history || history.length === 0) && (
                        <div style={styles.emptyState}>Initializing secure agents...</div>
                    )}
                </div>
            </div>

            {rejectionReason && (
                <div style={styles.actionRow}>
                    <button onClick={onRestart} style={styles.btnSecondary}>Start New Application</button>
                    <div style={styles.helpText}>Need help? Contact support@orchestrator.com</div>
                </div>
            )}

            {sanctionUrl && (
                <div style={styles.actionRow}>
                    <a href={sanctionUrl} target="_blank" rel="noreferrer" style={styles.btnPrimary}>View Loan Offer</a>
                </div>
            )}
        </div>
    );
};

/* --- Components --- */
const InfoCard = ({ label, value }) => (
    <div style={styles.infoCard}>
        <div className="label">{label}</div>
        <div style={styles.infoValue}>{value}</div>
    </div>
);

const TimelineItem = ({ label, status }) => {
    const isDone = status === 'done';
    const isActive = status === 'active';

    return (
        <div style={styles.step}>
            <div style={{
                ...styles.stepIcon,
                background: isDone ? 'var(--success-bg)' : (isActive ? 'var(--brand-light)' : 'var(--bg-subtle)'),
                color: isDone ? 'var(--success-text)' : (isActive ? 'var(--brand-primary)' : 'var(--text-tertiary)'),
                borderColor: isDone ? 'transparent' : (isActive ? 'var(--brand-primary)' : 'var(--border-subtle)'),
            }}>
                {isDone ? '✓' : (isActive ? '●' : '')}
            </div>
            <div style={{
                fontWeight: isActive || isDone ? 500 : 400,
                color: isActive || isDone ? 'var(--text-primary)' : 'var(--text-tertiary)'
            }}>{label}</div>
        </div>
    );
};

/* --- Styles --- */
const styles = {
    container: {
        display: 'flex',
        flexDirection: 'column',
        gap: 32,
    },
    heroCard: {
        background: 'var(--bg-card)',
        border: '1px solid var(--border-subtle)',
        borderRadius: 'var(--radius-card)',
        padding: '32px',
        display: 'flex',
        alignItems: 'center',
        gap: 24,
        boxShadow: 'var(--shadow-card)',
    },
    statusIcon: {
        width: 48, height: 48,
        borderRadius: '50%',
        background: 'var(--bg-subtle)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: 24,
    },
    heroContent: {
        display: 'flex',
        flexDirection: 'column',
        gap: 8,
    },
    grid: {
        display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr', gap: 16,
    },
    infoCard: {
        background: 'var(--bg-card)',
        border: '1px solid var(--border-subtle)',
        borderRadius: 'var(--radius-card)',
        padding: '16px',
        display: 'flex', flexDirection: 'column', gap: 8,
    },
    infoValue: {
        fontSize: 16, fontWeight: 600, color: 'var(--text-primary)',
    },
    progressCard: {
        background: 'var(--bg-card)',
        border: '1px solid var(--border-subtle)',
        borderRadius: 'var(--radius-card)',
        padding: '32px',
        boxShadow: 'var(--shadow-card)',
    },
    timeline: {
        display: 'flex', flexDirection: 'column', gap: 24, paddingLeft: 8,
    },
    step: {
        display: 'flex', alignItems: 'center', gap: 16,
    },
    stepIcon: {
        width: 24, height: 24, borderRadius: '50%',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: 14, border: '1px solid',
        flexShrink: 0,
    },
    actionRow: {
        display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 16, marginTop: 16,
    },
    btnPrimary: {
        background: 'var(--brand-primary)', color: 'white',
        padding: '12px 32px', borderRadius: 'var(--radius-btn)',
        fontSize: 16, fontWeight: 600, textDecoration: 'none',
        boxShadow: '0 4px 6px rgba(37, 99, 235, 0.2)',
    },
    btnSecondary: {
        background: 'white', color: 'var(--text-primary)', border: '1px solid var(--border-subtle)',
        padding: '12px 24px', borderRadius: 'var(--radius-btn)',
        fontSize: 14, fontWeight: 500,
    },
    helpText: {
        fontSize: 13, color: 'var(--text-tertiary)',
    },
    liveBadge: {
        background: '#DCFCE7', color: '#166534', fontSize: 11, fontWeight: 700, padding: '4px 8px', borderRadius: 4, letterSpacing: '0.05em'
    },
    chatWindow: {
        background: 'white', borderRadius: 12, border: '1px solid #E5E7EB', height: 300, overflowY: 'auto', padding: 16, display: 'flex', flexDirection: 'column', gap: 12
    },
    chatRow: {
        display: 'flex', width: '100%',
    },
    chatBubble: {
        maxWidth: '85%', padding: '10px 14px', borderRadius: 12, fontSize: 14, lineHeight: 1.5,
    },
    botLabel: {
        fontWeight: 600, fontSize: 12, textTransform: 'uppercase', marginRight: 6, opacity: 0.7
    },
    emptyState: {
        textAlign: 'center', color: '#9CA3AF', marginTop: 100, fontSize: 14
    }
};

export default DashboardPanel;
