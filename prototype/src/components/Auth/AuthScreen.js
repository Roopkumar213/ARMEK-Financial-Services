import React, { useState } from 'react';

const AuthScreen = ({ onLogin }) => {
    const [isLogin, setIsLogin] = useState(true);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [name, setName] = useState('');

    const handleSubmit = (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        // Simulated network delay and validation
        setTimeout(() => {
            if (!email.includes('@')) {
                setError('Please enter a valid email address.');
                setLoading(false);
                return;
            }
            if (password.length < 6) {
                setError('Password must be at least 6 characters.');
                setLoading(false);
                return;
            }

            // Success
            onLogin({ name: name || 'User', email });
        }, 1500);
    };

    return (
        <div style={styles.container}>
            {/* Left Brand Panel */}
            <div style={styles.brandPanel}>
                <div style={styles.brandContent}>
                    <div style={styles.logoHuge}>Orchestrator</div>
                    <h1 style={styles.brandHeading}>Financial freedom,<br />orchestrated.</h1>
                    <p style={styles.brandSub}>Secure. Private. Trusted by millions.</p>
                    <div style={styles.trustBadges}>
                        <span>🔒 256-bit Encryption</span>
                        <span>🛡️ SOC2 Certified</span>
                    </div>
                </div>
            </div>

            {/* Right Form Panel */}
            <div style={styles.formPanel}>
                <div style={styles.formCard}>
                    <h2 style={styles.formTitle}>{isLogin ? 'Welcome Back' : 'Create Account'}</h2>
                    <form onSubmit={handleSubmit} style={styles.form}>
                        {!isLogin && (
                            <div style={styles.field}>
                                <label style={styles.label}>Full Name</label>
                                <input
                                    style={styles.input}
                                    value={name} onChange={e => setName(e.target.value)}
                                    placeholder="e.g. Jane Doe"
                                />
                            </div>
                        )}

                        <div style={styles.field}>
                            <label style={styles.label}>Email Address</label>
                            <input
                                style={styles.input} type="email"
                                value={email} onChange={e => setEmail(e.target.value)}
                                placeholder="name@example.com"
                            />
                        </div>

                        <div style={styles.field}>
                            <label style={styles.label}>Password</label>
                            <input
                                style={styles.input} type="password"
                                value={password} onChange={e => setPassword(e.target.value)}
                                placeholder="••••••••"
                            />
                        </div>

                        {error && <div style={styles.error}>{error}</div>}

                        <button type="submit" style={styles.submitBtn} disabled={loading}>
                            {loading ? 'Securing connection...' : (isLogin ? 'Log In' : 'Create Account')}
                        </button>
                    </form>

                    <div style={styles.toggleRow}>
                        {isLogin ? "New to Orchestrator?" : "Already have an account?"}
                        <button
                            onClick={() => { setIsLogin(!isLogin); setError(''); }}
                            style={styles.linkBtn}
                        >
                            {isLogin ? 'Sign Up' : 'Log In'}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

const styles = {
    container: {
        display: 'flex',
        height: '100vh',
        width: '100vw',
        fontFamily: 'Inter, sans-serif',
    },
    brandPanel: {
        flex: 1,
        background: '#111827', // Dark Slate
        color: 'white',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 60,
    },
    brandContent: {
        maxWidth: 480,
    },
    logoHuge: {
        fontSize: 20, fontWeight: 700, marginBottom: 32, opacity: 0.8,
    },
    brandHeading: {
        fontSize: 48, fontWeight: 800, lineHeight: 1.1, marginBottom: 24, letterSpacing: '-0.02em',
    },
    brandSub: {
        fontSize: 18, opacity: 0.7, marginBottom: 48,
    },
    trustBadges: {
        display: 'flex', gap: 24, fontSize: 13, opacity: 0.5, fontWeight: 500,
    },
    formPanel: {
        flex: 1,
        background: '#F9FAFB',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 24,
    },
    formCard: {
        width: '100%', maxWidth: 400,
        background: 'white',
        padding: 40,
        borderRadius: 16,
        boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06)',
    },
    formTitle: {
        fontSize: 24, fontWeight: 700, color: '#111827', marginBottom: 32,
    },
    form: {
        display: 'flex', flexDirection: 'column', gap: 20,
    },
    field: {
        display: 'flex', flexDirection: 'column', gap: 8,
    },
    label: {
        fontSize: 13, fontWeight: 600, color: '#374151',
    },
    input: {
        padding: '12px 14px',
        borderRadius: 8,
        border: '1px solid #D1D5DB',
        fontSize: 15,
        outline: 'none',
        transition: 'border 0.2s',
    },
    submitBtn: {
        marginTop: 12,
        background: '#2563EB',
        color: 'white',
        border: 'none',
        padding: '14px',
        borderRadius: 8,
        fontSize: 15, fontWeight: 600,
        cursor: 'pointer',
    },
    error: {
        fontSize: 13, color: '#DC2626', background: '#FEF2F2', padding: 10, borderRadius: 6,
    },
    toggleRow: {
        marginTop: 24, textAlign: 'center', fontSize: 14, color: '#6B7280',
    },
    linkBtn: {
        background: 'none', border: 'none', color: '#2563EB', fontWeight: 600, marginLeft: 6,
    }
};

export default AuthScreen;
