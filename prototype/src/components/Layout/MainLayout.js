import React from 'react';

const DashboardLayout = ({ children, user, onLogout }) => {
    return (
        <div style={styles.appContainer}>
            {/* App Header */}
            <header style={styles.header}>
                <div style={styles.headerContent}>
                    <div style={styles.brand}>
                        <div style={styles.logoMark} />
                        <span style={styles.brandName}>Orchestrator</span>
                    </div>

                    <div style={styles.userControls}>
                        <span style={styles.userName}>Hello, {user?.name || 'User'}</span>
                        <button onClick={onLogout} style={styles.logoutLink}>Sign Out</button>
                        <div style={styles.avatar}>{user?.name?.charAt(0) || 'U'}</div>
                    </div>
                </div>
            </header>

            {/* Content Area */}
            <main style={styles.main}>
                {children}
            </main>

            {/* Footer */}
            <footer style={styles.footer}>
                <div style={styles.footerContent}>
                    <span>&copy; 2026 Orchestrator Financial Services. All rights reserved.</span>
                    <div style={styles.footerLinks}>
                        <span>Privacy</span>
                        <span>Terms</span>
                        <span>Security</span>
                    </div>
                </div>
            </footer>
        </div>
    );
};

const styles = {
    appContainer: {
        minHeight: '100vh',
        display: 'flex', flexDirection: 'column',
        background: '#F9FAFB',
    },
    header: {
        height: 64,
        background: 'white',
        borderBottom: '1px solid #E5E7EB',
        position: 'sticky', top: 0, zIndex: 50,
    },
    headerContent: {
        maxWidth: 1024, margin: '0 auto',
        height: '100%', padding: '0 24px',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
    },
    brand: {
        display: 'flex', alignItems: 'center', gap: 10,
    },
    logoMark: {
        width: 28, height: 28, borderRadius: 6, background: '#2563EB',
    },
    brandName: {
        fontSize: 16, fontWeight: 700, color: '#111827',
    },
    userControls: {
        display: 'flex', alignItems: 'center', gap: 16,
    },
    userName: {
        fontSize: 14, color: '#4B5563', fontWeight: 500,
    },
    logoutLink: {
        background: 'none', border: 'none', color: '#9CA3AF', fontSize: 13, cursor: 'pointer',
    },
    avatar: {
        width: 32, height: 32, borderRadius: '50%', background: '#EFF6FF', color: '#2563EB',
        display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 600, fontSize: 14,
    },
    main: {
        flex: 1,
        width: '100%', maxWidth: 1024, margin: '0 auto',
        padding: '32px 24px',
    },
    footer: {
        borderTop: '1px solid #E5E7EB',
        background: 'white',
        padding: '32px 0',
    },
    footerContent: {
        maxWidth: 1024, margin: '0 auto', padding: '0 24px',
        display: 'flex', justifyContent: 'space-between', color: '#9CA3AF', fontSize: 13,
    },
    footerLinks: {
        display: 'flex', gap: 24,
    }
};

export default DashboardLayout;
