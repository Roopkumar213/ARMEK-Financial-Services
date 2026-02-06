import React, { useEffect, useState } from "react";
import DashboardLayout from "./components/Layout/MainLayout";
import AuthScreen from "./components/Auth/AuthScreen";
import LoanWizard from "./components/Loan/LoanWizard";
import DashboardPanel from "./components/Dashboard/DashboardPanel";

/* --- BACKEND CONFIG --- */
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || "http://localhost:8000/chat";

function generateUUID() {
  return crypto.randomUUID();
}

function App() {
  // --- VIEW STATE ---
  const [currentView, setCurrentView] = useState('AUTH'); // 'AUTH' | 'DASHBOARD' | 'WIZARD' | 'PROCESSING' | 'DECISION'

  // --- DATA STATE ---
  const [currentUser, setCurrentUser] = useState(null);
  const [sessionId, setSessionId] = useState(null);
  const [sessionState, setSessionState] = useState(null); // Backend State
  const [rejectionReason, setRejectionReason] = useState(null);
  const [sanctionUrl, setSanctionUrl] = useState(null);
  const [history, setHistory] = useState([]); // Live Agent Logs

  // --- INIT ---
  useEffect(() => {
    // Only init session if logged in
    if (currentUser && !sessionId) {
      setSessionId(generateUUID());
    }
  }, [currentUser, sessionId]);

  // --- AUTH HANDLERS ---
  const handleLogin = (user) => {
    setCurrentUser(user);
    setCurrentView('DASHBOARD');
  };

  const handleLogout = () => {
    setCurrentUser(null);
    setSessionId(null);
    setSessionState(null);
    setRejectionReason(null);
    setSanctionUrl(null);
    setHistory([]);
    setCurrentView('AUTH');
  };

  // --- LOAN HANDLERS ---
  const startApplication = () => {
    setCurrentView('WIZARD');
  };

  const submitApplication = async (formData) => {
    setCurrentView('PROCESSING'); // Show visual loader

    // 1. Construct the "Mega Prompt" to simulate user conversation
    const prompt = `Start Application. My name is ${currentUser?.name || 'User'}. My PAN is ${formData.pan}. My monthly income is ${formData.income}. I want a loan of ${formData.amount} for ${formData.tenure} months.`;

    // 2. Send to Orchestrator
    try {
      await orchestrate(prompt);
      // Determine next view based on result
      // If success -> 'DECISION' (Approved/Rejected is inside Decision View)
      // We'll give it a fake delay so the 'Processing' animation can play
      setTimeout(() => {
        setCurrentView('DECISION');
      }, 4000);

    } catch (e) {
      console.error("Orchestration failed", e);
    }
  };

  const orchestrate = async (message) => {
    if (!sessionId) return;

    try {
      const response = await fetch(BACKEND_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          message: message,
        }),
      });
      const data = await response.json();

      // Update System State
      if (data.data?.state) {
        setSessionState(data.data.state);
        // Extract History
        if (data.data.state.conversation_history) {
          setHistory(data.data.state.conversation_history);
        }
        if (data.data.state.sanction_url) {
          setSanctionUrl(`http://localhost:8000${data.data.state.sanction_url}`);
        }
      }
      if (data.ui_action === "SHOW_REJECTION") {
        setRejectionReason(data.data.reason);
      }
    } catch (err) {
      console.error("Backend Error", err);
    }
  };

  const resetApplication = () => {
    // Reset backend
    orchestrate("Restart Application");
    setRejectionReason(null);
    setSanctionUrl(null);
    setCurrentView('DASHBOARD');
  };

  // --- RENDER ---
  if (currentView === 'AUTH') {
    return <AuthScreen onLogin={handleLogin} />;
  }

  return (
    <DashboardLayout user={currentUser} onLogout={handleLogout}>

      {currentView === 'DASHBOARD' && (
        <DashboardView
          user={currentUser}
          onApply={startApplication}
        />
      )}

      {currentView === 'WIZARD' && (
        <LoanWizard onComplete={submitApplication} />
      )}

      {(currentView === 'PROCESSING' || currentView === 'DECISION') && (
        <DashboardPanel
          sessionState={sessionState}
          sessionId={sessionId}
          rejectionReason={rejectionReason}
          sanctionUrl={sanctionUrl}
          onRestart={resetApplication}
          // Force processing state if in processing view
          isProcessing={currentView === 'PROCESSING'}
          history={history}
        />
      )}

    </DashboardLayout>
  );
}

// Simple internal Dashboard View (Welcome State)
const DashboardView = ({ user, onApply }) => (
  <div style={{ textAlign: 'center', padding: '60px 0' }}>
    <h1 style={{ fontSize: 32, fontWeight: 700, marginBottom: 16 }}>
      Welcome back, {user?.name?.split(' ')[0]}
    </h1>
    <p style={{ fontSize: 18, color: '#6B7280', marginBottom: 40 }}>
      You have no active loans.
    </p>
    <button
      onClick={onApply}
      style={{
        background: '#2563EB', color: 'white', border: 'none',
        padding: '16px 32px', fontSize: 16, fontWeight: 600,
        borderRadius: 12, cursor: 'pointer',
        boxShadow: '0 10px 20px -5px rgba(37, 99, 235, 0.4)'
      }}
    >
      Apply for a Loan
    </button>

    <div style={{ marginTop: 60, display: 'flex', justifyContent: 'center', gap: 40, opacity: 0.6 }}>
      <Feature icon="⚡" text="Instant Approvals" />
      <Feature icon="🔒" text="Secure Processing" />
      <Feature icon="📉" text="Low Interest Rates" />
    </div>
  </div>
);

const Feature = ({ icon, text }) => (
  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8 }}>
    <div style={{ fontSize: 24 }}>{icon}</div>
    <div style={{ fontSize: 14, fontWeight: 500, color: '#374151' }}>{text}</div>
  </div>
);

export default App;
