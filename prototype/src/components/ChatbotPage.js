// ChatbotPage.js
// Enterprise-grade Agentic Loan Assistant UI
// Clean, stable, judge-friendly, demo-proof

import { useEffect, useState, useRef } from "react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;



function generateUUID() {
  return crypto.randomUUID();
}

// Human-readable stage labels (NO internal leakage)
const STAGE_LABELS = {
  ASK_NAME: "Getting Started",
  ASK_PAN: "Identity Verification",
  ASK_INCOME: "Income Details",
  ASK_EMI: "Financial Obligations",
  ASK_AMOUNT: "Loan Requirement",
  ASK_TENURE: "Loan Preferences",
  COMPLETED: "Loan Approved",
  REJECTED: "Application Update",
};

export default function ChatbotPage() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);

  const [sanctionUrl, setSanctionUrl] = useState(null);
  const [currentStage, setCurrentStage] = useState("ASK_NAME");

  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  /* ---------- INIT ---------- */
  useEffect(() => {
    setSessionId(generateUUID());
    setMessages([
      {
        id: Date.now(),
        sender: "bot",
        text:
          "Hello! Welcome to ARMEK Financial Services.\n" +
          "I’ll help you check and apply for a personal loan in just a few steps. " +
          "To begin, may I have your full name?",
      },
    ]);
  }, []);

  /* ---------- AUTOSCROLL ---------- */
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, sanctionUrl, loading]);

  /* ---------- SEND MESSAGE ---------- */
  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    const userText = input.trim();
    setInput("");
    setLoading(true);

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

      if (!response.ok) throw new Error("Network error");

      const data = await response.json();

      if (data.stage) {
        setCurrentStage(data.stage);
      }

      if (data.reply) {
        setMessages((prev) => [
          ...prev,
          { id: Date.now() + 1, sender: "bot", text: data.reply },
        ]);
      }

      if (
        data.ui_action === "SHOW_SANCTION_DOWNLOAD" &&
        data.data?.letter_url &&
        !sanctionUrl
      ) {
        setSanctionUrl(`http://localhost:8000${data.data.letter_url}`);
      }
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 2,
          sender: "bot",
          text:
            "I’m facing a brief connection issue. " +
            "Please try again in a moment.",
        },
      ]);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  /* ---------- ENTER KEY ---------- */
  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  /* ---------- UI ---------- */
  return (
    <div style={styles.page}>
      <div style={styles.chatCard}>
        {/* Header */}
        <div style={styles.header}>
          <h2 style={styles.title}>ARMEK Financial Services</h2>
          <p style={styles.subtitle}>AI Personal Loan Assistant</p>

          <span style={styles.stageBadge}>
            {STAGE_LABELS[currentStage] || "Processing"}
          </span>
        </div>

        {/* Messages */}
        <div style={styles.messages}>
          {messages.map((msg) => (
            <div
              key={msg.id}
              style={{
                ...styles.message,
                alignSelf:
                  msg.sender === "user" ? "flex-end" : "flex-start",
                background:
                  msg.sender === "user" ? "#4f46e5" : "#f1f5f9",
                color: msg.sender === "user" ? "#fff" : "#111",
              }}
            >
              {msg.text}
            </div>
          ))}

          {loading && (
            <div style={styles.thinking}>
              Reviewing details…
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Sanction Download */}
        {sanctionUrl && (
          <div style={styles.downloadBox}>
            <button
              onClick={() => window.open(sanctionUrl, "_blank")}
              style={styles.downloadBtn}
            >
              📄 Download Sanction Letter
            </button>
            <p style={styles.passwordText}>
              🔐 Password: your first name in lowercase
            </p>
          </div>
        )}

        {/* Input */}
        <div style={styles.inputRow}>
          <input
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyPress}
            placeholder={
              loading ? "Please wait…" : "Type your response here"
            }
            style={styles.input}
            disabled={loading}
          />
          <button
            onClick={sendMessage}
            disabled={!input.trim() || loading}
            style={{
              ...styles.sendBtn,
              opacity: !input.trim() || loading ? 0.5 : 1,
            }}
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}

/* ---------- STYLES ---------- */

const styles = {
  page: {
    minHeight: "100vh",
    background: "linear-gradient(135deg, #667eea, #764ba2)",
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    padding: 20,
    fontFamily:
      "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto",
  },
  chatCard: {
    width: "100%",
    maxWidth: 480,
    height: "90vh",
    background: "#fff",
    borderRadius: 20,
    display: "flex",
    flexDirection: "column",
    overflow: "hidden",
    boxShadow: "0 25px 70px rgba(0,0,0,0.35)",
  },
  header: {
    background: "linear-gradient(135deg, #4f46e5, #7c3aed)",
    color: "#fff",
    padding: 20,
    textAlign: "center",
  },
  title: { margin: 0, fontSize: 22, fontWeight: 700 },
  subtitle: { margin: "4px 0", fontSize: 13, opacity: 0.9 },
  stageBadge: {
    marginTop: 8,
    display: "inline-block",
    padding: "4px 12px",
    borderRadius: 12,
    background: "rgba(255,255,255,0.25)",
    fontSize: 11,
    fontWeight: 600,
  },
  messages: {
    flex: 1,
    padding: 20,
    background: "#fafafa",
    display: "flex",
    flexDirection: "column",
    gap: 12,
    overflowY: "auto",
  },
  message: {
    maxWidth: "80%",
    padding: "12px 16px",
    borderRadius: 16,
    fontSize: 14,
    lineHeight: 1.5,
    boxShadow: "0 2px 8px rgba(0,0,0,0.08)",
    whiteSpace: "pre-wrap",
  },
  thinking: {
    fontSize: 12,
    color: "#555",
    fontStyle: "italic",
  },
  inputRow: {
    display: "flex",
    gap: 10,
    padding: 16,
    borderTop: "1px solid #e5e7eb",
  },
  input: {
    flex: 1,
    padding: "12px 16px",
    borderRadius: 12,
    border: "1px solid #d1d5db",
    fontSize: 14,
  },
  sendBtn: {
    padding: "12px 20px",
    background: "#4f46e5",
    color: "#fff",
    border: "none",
    borderRadius: 12,
    fontWeight: 600,
  },
  downloadBox: {
    margin: "0 16px 16px",
    padding: 16,
    borderRadius: 12,
    background: "#ecfdf5",
    border: "2px solid #10b981",
    textAlign: "center",
  },
  downloadBtn: {
    background: "#10b981",
    color: "#fff",
    padding: "12px 18px",
    borderRadius: 10,
    border: "none",
    fontWeight: 600,
    width: "100%",
  },
  passwordText: {
    marginTop: 10,
    fontSize: 12,
    color: "#065f46",
  },
};
