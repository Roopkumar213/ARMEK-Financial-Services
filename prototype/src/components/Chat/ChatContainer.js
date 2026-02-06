import React, { useEffect } from 'react';
import ChatInput from './ChatInput';

const ChatContainer = ({ messages, input, setInput, onSend, loading }) => {
    // Get the last message from the system to display as "Insight"
    const lastSystemMessage = [...messages].reverse().find(m => m.sender === 'bot');
    const insightText = lastSystemMessage ? lastSystemMessage.text : "We are analyzing your profile to find the best loan offers.";

    return (
        <div style={styles.container}>
            <h3 className="h3">System Insight</h3>

            <div style={styles.insightCard}>
                <div style={styles.iconArea}>
                    💡
                </div>
                <div style={styles.contentArea}>
                    <p style={styles.text}>{insightText}</p>
                </div>
            </div>

            {/* 
         We keep the input visually hidden/minimized unless purely for dev overrides or specific prompts. 
         For a consumer app, we usually wouldn't have a chat input at all, or it would be a specific form.
         Here we style it as a "Note to underwriter" or similar optional field if we must keep it, 
         or just hide it if the flow is automated. Given the prototype nature, I'll style it as a 
         "Ask a question" box but minimal.
      */}
            <div style={styles.inputArea}>
                <ChatInput
                    input={input}
                    setInput={setInput}
                    onSend={onSend}
                    loading={loading}
                />
            </div>
        </div>
    );
};

const styles = {
    container: {
        display: 'flex',
        flexDirection: 'column',
        gap: 16,
    },
    insightCard: {
        background: 'var(--brand-light)',
        border: '1px solid #DBEAFE', // Blue 100
        borderRadius: 'var(--radius-card)',
        padding: '24px',
        display: 'flex',
        gap: 16,
        alignItems: 'flex-start',
    },
    iconArea: {
        fontSize: 20,
        marginTop: 2,
    },
    contentArea: {
        flex: 1,
    },
    text: {
        margin: 0,
        fontSize: 15,
        color: 'var(--brand-dark)',
        lineHeight: 1.6,
    },
    inputArea: {
        marginTop: 8,
    }
};

export default ChatContainer;
