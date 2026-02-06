// ChatbotPage.js
import { useEffect, useState, useRef } from "react";

const BACKEND_URL =
  process.env.REACT_APP_BACKEND_URL || "http://localhost:8000/chat";

/* ---------- UTILS ---------- */
function generateUUID() {
  return crypto.randomUUID();
}

export default function ChatbotPage() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);

  // Dashboard State
  const [sessionState, setSessionState] = useState(null);
  const [sanctionUrl, setSanctionUrl] = useState(null);
  const [rejectionReason, setRejectionReason] = useState(null);

  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  /* ---------- INIT ---------- */
  useEffect(() => {
    const sid = generateUUID();
    setSessionId(sid);
    setMessages([
      {
        id: Date.now(),
        sender: "bot",
        text: "Welcome to the Agentic Loan Platform. I am the Master Orchestrator. I can help you with a loan application.",
      },
    ]);
  }, []);

  /* ---------- AUTOSCROLL ---------- */
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  /* ---------- ACTION HANDLER ---------- */
  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    const userText = input.trim();
    setInput("");
    setLoading(true);

    // Optimistic UI
    setMessages((prev) => [
      ...prev,
      { id: Date.now(), sender: "user", text: userText },
    ]);

    try {
      const response = await fetch(BACKEND_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          message: userText,
        }),
      });

      const data = await response.json();

      // Update Dashboard State
      if (data.data?.state) {
        setSessionState(data.data.state);
      }

      if (data.ui_action === "SHOW_REJECTION") {
        setRejectionReason(data.data.reason);
      }

      if (data.ui_action === "RESET_UI") {
        setMessages([{
          id: Date.now(),
          sender: "bot",
          text: data.reply
        }]);
        setSessionState(null);
        setRejectionReason(null);
        setSanctionUrl(null);
      } else {
        // Standard processing
        setMessages((prev) => [
          ...prev,
          { id: Date.now() + 1, sender: "bot", text: data.reply },
        ]);
      }

      if (data.data?.state?.sanction_url) {
        setSanctionUrl(`http://localhost:8000${data.data.state.sanction_url}`);
      }

    } catch (err) {
      console.error(err);
      setMessages((prev) => [
        ...prev,
        { id: Date.now() + 2, sender: "bot", text: "Connection Error. Please check backend." },
      ]);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  /* ---------- RENDERERS ---------- */
  const renderStatusCard = (title, status, active) => {
    let color = "#cbd5e1"; // gray
    if (status === true) color = "#10b981"; // green
    if (status === false && active) color = "#f59e0b"; // yellow/working
    if (status === "REJECTED") color = "#ef4444"; // red

    return (
      <div style={{ ...styles.statusCard, borderColor: active ? "#6366f1" : "transparent" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <span style={styles.cardTitle}>{title}</span>
          <div style={{ width: 12, height: 12, borderRadius: "50%", background: color }} />
        </div>
        {active && <div style={styles.activityIndicator}>Running...</div>}
      </div>
    );
  };

  const profile = sessionState?.profile || {};
  const risk = sessionState?.risk || {};

  return (
    <div style={styles.page}>

      {/* LEFT PANEL - DASHBOARD */}
      <div style={styles.dashboardPanel}>
        <div style={styles.dashHeader}>
          <h2 style={{ margin: 0, fontSize: 18 }}>Live Application Context</h2>
          <div style={styles.badge}>ID: {sessionId?.slice(0, 8)}</div>
        </div>

        <div style={styles.sectionHeader}>Worker Agents Status</div>

        <div style={styles.cardGrid}>
          {renderStatusCard("Eligibility Check", sessionState?.eligibility_run, !sessionState?.eligibility_run && profile.loan_amount)}
          {renderStatusCard("KYC Verification", sessionState?.kyc_verified, sessionState?.eligibility_run && !sessionState?.kyc_verified && profile.pan)}
          {renderStatusCard("Credit Bureau", sessionState?.credit_bureau_checked, sessionState?.kyc_verified && !sessionState?.credit_bureau_checked)}
          {renderStatusCard("Sanction Generation", sessionState?.sanction_generated, sessionState?.credit_bureau_checked && !sessionState?.sanction_generated)}
        </div>

        <div style={styles.sectionHeader}>Extracted Data</div>
        <div style={styles.dataBox}>
          <DataRow label="Name" value={profile.name} />
          <DataRow label="Income" value={profile.monthly_income ? `₹${profile.monthly_income}` : null} />
          <DataRow label="Existing EMI" value={profile.existing_emi ? `₹${profile.existing_emi}` : null} />
          <DataRow label="Loan Amount" value={profile.loan_amount ? `₹${profile.loan_amount}` : null} />
          <DataRow label="Tenure" value={profile.tenure_months ? `${profile.tenure_months}m` : null} />
          <DataRow label="PAN" value={profile.pan} />
        </div>

        {risk.fake_data_detected && (
          <div style={styles.riskAlert}>
            ⚠️ FRAUD / INCONSISTENCY DETECTED
          </div>
        )}

        {rejectionReason && (
          <div style={styles.rejectionBox}>
            <strong>Application Rejected</strong>
            <p>{rejectionReason}</p>
            <button onClick={() => setInput("Restart Application")} style={styles.retryBtn}>Restart Application</button>
          </div>
        )}

        {sanctionUrl && (
          <div style={styles.successBox}>
            <strong>Loan Approved!</strong>
            <a href={sanctionUrl} target="_blank" rel="noreferrer" style={styles.downloadLink}>Download Sanction Letter</a>
          </div>
        )}

      </div>

      {/* RIGHT PANEL - CHAT */}
      <div style={styles.chatPanel}>
        <div style={styles.chatHeader}>Master Agent Orchestrator</div>
        <div style={styles.messages}>
          {messages.map((msg) => (
            <div key={msg.id} style={{
              ...styles.bubble,
              alignSelf: msg.sender === "user" ? "flex-end" : "flex-start",
              background: msg.sender === "user" ? "#4f46e5" : "#f1f5f9",
              color: msg.sender === "user" ? "white" : "#1e293b"
            }}>
              {msg.text}
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>
        <div style={styles.inputArea}>
          <input
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && sendMessage()}
            placeholder="Type your response..."
            style={styles.input}
            disabled={loading}
          />
          <button onClick={sendMessage} disabled={loading} style={styles.sendBtn}>Send</button>
        </div>
      </div>
    </div>
  );
}

const DataRow = ({ label, value }) => (
  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6, fontSize: 13 }}>
    <span style={{ color: "#64748b" }}>{label}</span>
    <span style={{ fontWeight: 600, color: value ? "#0f172a" : "#cbd5e1" }}>{value || "---"}</span>
  </div>
);

const styles = {
  page: { display: "flex", height: "100vh", fontFamily: "Inter, sans-serif", background: "#f8fafc" },
  dashboardPanel: { width: "35%", background: "white", borderRight: "1px solid #e2e8f0", padding: 24, overflowY: "auto" },
  chatPanel: { flex: 1, display: "flex", flexDirection: "column" },
  dashHeader: { marginBottom: 24, display: "flex", justifyContent: "space-between", alignItems: "center" },
  badge: { fontSize: 10, background: "#f1f5f9", padding: "4px 8px", borderRadius: 4, color: "#64748b" },
  sectionHeader: { fontSize: 12, fontWeight: 700, textTransform: "uppercase", color: "#94a3b8", marginBottom: 12, letterSpacing: 0.5 },
  cardGrid: { display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 24 },
  statusCard: { background: "#f8fafc", padding: 12, borderRadius: 8, border: "1px solid #e2e8f0" },
  cardTitle: { fontSize: 12, fontWeight: 600, color: "#475569" },
  activityIndicator: { fontSize: 10, color: "#6366f1", marginTop: 4, fontWeight: 600 },
  dataBox: { background: "#f8fafc", padding: 16, borderRadius: 12, border: "1px solid #e2e8f0", marginBottom: 24 },
  riskAlert: { background: "#fef2f2", color: "#ef4444", padding: 12, borderRadius: 8, fontSize: 13, fontWeight: 700, textAlign: "center", marginBottom: 16 },
  rejectionBox: { background: "#fff1f2", border: "1px solid #fda4af", padding: 16, borderRadius: 8, color: "#be123c", fontSize: 13 },
  successBox: { background: "#f0fdf4", border: "1px solid #86efac", padding: 16, borderRadius: 8, color: "#166534", textAlign: "center" },
  retryBtn: { marginTop: 8, padding: "6px 12px", background: "#be123c", color: "white", border: "none", borderRadius: 4, cursor: "pointer", fontSize: 12 },
  downloadLink: { display: "block", marginTop: 8, color: "#166534", fontWeight: 700, textDecoration: "underline" },

  chatHeader: { padding: 16, borderBottom: "1px solid #e2e8f0", background: "white", fontWeight: 600, color: "#334155" },
  messages: { flex: 1, padding: 24, overflowY: "auto", display: "flex", flexDirection: "column", gap: 12 },
  bubble: { padding: "12px 18px", borderRadius: 12, maxWidth: "70%", lineHeight: 1.5, fontSize: 14, boxShadow: "0 1px 2px rgba(0,0,0,0.05)" },
  inputArea: { padding: 24, background: "white", borderTop: "1px solid #e2e8f0", display: "flex", gap: 12 },
  input: { flex: 1, padding: 12, borderRadius: 8, border: "1px solid #cbd5e1", outline: "none", fontSize: 14 },
  sendBtn: { padding: "0 24px", background: "#4f46e5", color: "white", borderRadius: 8, border: "none", fontWeight: 600, cursor: "pointer" }
};
