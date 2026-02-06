import React from 'react';

const ChatInput = ({ input, setInput, onSend, loading }) => {
    return (
        <div style={styles.container}>
            <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && onSend()}
                placeholder="Have a question about your application?"
                style={styles.input}
                disabled={loading}
            />
            {input.trim() && (
                <button onClick={onSend} style={styles.sendBtn}>
                    Send
                </button>
            )}
        </div>
    );
};

const styles = {
    container: {
        background: 'white',
        border: '1px solid var(--border-subtle)',
        borderRadius: 'var(--radius-btn)',
        padding: '4px 12px',
        display: 'flex',
        alignItems: 'center',
        boxShadow: '0 1px 2px rgba(0,0,0,0.05)',
    },
    input: {
        flex: 1,
        border: 'none',
        outline: 'none',
        padding: '10px 0',
        fontSize: 14,
        color: 'var(--text-primary)',
    },
    sendBtn: {
        background: 'none',
        border: 'none',
        color: 'var(--brand-primary)',
        fontWeight: 600,
        fontSize: 14,
    }
};

export default ChatInput;
