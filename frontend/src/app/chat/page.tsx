"use client";

import React, { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { Send, Loader2, User, Bot, AlertTriangle, ShieldCheck } from "lucide-react";

import {
  getAccessToken,
  clearTokens,
  submitChatMessage,
  getMessage,
  connectWebSocket,
} from "../../lib/api";

interface ChatMessage {
  id: string;
  role: "user" | "bot";
  text: string;
  status?: "sending" | "completed" | "pending_review" | "error";
  backendMessageId?: number;
  timestamp: Date;
}

export default function ChatPage() {
  const router = useRouter();
  const [isAuthenticated, setIsAuthenticated] = useState(true);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputText, setInputText] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  
  // Single session ID for this conversation thread
  const sessionId = useRef(`session_${Math.random().toString(36).substr(2, 9)}`);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // ── Authentication Check ──
  useEffect(() => {
    if (!getAccessToken()) {
      setIsAuthenticated(false);
      router.push("/");
    }
  }, [router]);

  // ── Auto Scroll ──
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // ── WebSocket Integration ──
  useEffect(() => {
    if (!isAuthenticated) return;

    const cleanup = connectWebSocket(async (event) => {
      // If a human reviewed our message (or any message updated)
      if (event.type === "queue_update" || event.type === "new_message") {
        // We need to check if any of our messages were stuck in pending_review
        setMessages((prevMessages) => {
          const updatedMessages = [...prevMessages];
          const pendingIdx = updatedMessages.findIndex(
            (m) => m.role === "user" && m.status === "pending_review"
          );
          
          if (pendingIdx !== -1) {
            const pendingMsg = updatedMessages[pendingIdx];
            if (pendingMsg.backendMessageId) {
              // Async check the status
              checkMessageStatus(pendingMsg.backendMessageId);
            }
          }
          return updatedMessages;
        });
      }
    });

    return cleanup;
  }, [isAuthenticated]);

  const checkMessageStatus = async (backendId: number) => {
    try {
      const details = await getMessage(backendId);
      
      // If it has a response and routing decision, it's done!
      if (details.response && details.routing) {
        setMessages((prev) => {
          // Update the user message status
          const updated = prev.map((m) =>
            m.backendMessageId === backendId ? { ...m, status: "completed" as const } : m
          );
          
          // Check if we already have the bot's reply for this message
          const hasReply = updated.some(
            (m) => m.role === "bot" && m.backendMessageId === backendId
          );
          
          if (!hasReply) {
            // Add the AI's (now human-approved) response!
            updated.push({
              id: `bot_${backendId}`,
              role: "bot",
              text: details.response.response_text,
              timestamp: new Date(details.response.delivered_at || Date.now()),
              backendMessageId: backendId,
            });
          }
          return updated;
        });
      }
    } catch (err) {
      console.error("Failed to check message status", err);
    }
  };

  const handleLogout = () => {
    clearTokens();
    router.push("/");
  };

  const handleSend = async () => {
    if (!inputText.trim()) return;

    const userText = inputText.trim();
    setInputText("");
    setIsTyping(true);

    const tempId = `msg_${Date.now()}`;
    const newUserMsg: ChatMessage = {
      id: tempId,
      role: "user",
      text: userText,
      status: "sending",
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, newUserMsg]);

    try {
      const data = await submitChatMessage(userText, sessionId.current);

      setMessages((prev) =>
        prev.map((m) =>
          m.id === tempId
            ? { ...m, status: data.status, backendMessageId: data.id }
            : m
        )
      );

      if (data.status === "completed") {
        // Immediately fetch the response
        const details = await getMessage(data.id);
        if (details.response) {
          setMessages((prev) => [
            ...prev,
            {
              id: `bot_${data.id}`,
              role: "bot",
              text: details.response.response_text,
              timestamp: new Date(),
              backendMessageId: data.id,
            },
          ]);
        }
      }

    } catch (error) {
      setMessages((prev) =>
        prev.map((m) => (m.id === tempId ? { ...m, status: "error" } : m))
      );
    } finally {
      setIsTyping(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  if (!isAuthenticated) return null;

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100vh", backgroundColor: "var(--bg-primary)" }}>
      {/* Header */}
      <header
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          padding: "16px 24px",
          background: "var(--glass-bg)",
          backdropFilter: "blur(12px)",
          borderBottom: "1px solid var(--border-subtle)",
          zIndex: 10,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <div
            style={{
              width: 40,
              height: 40,
              borderRadius: 10,
              background: "linear-gradient(135deg, #8b5cf6, #6366f1)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "white",
            }}
          >
            <ShieldCheck size={20} />
          </div>
          <div>
            <h1 style={{ fontSize: 18, fontWeight: 700, margin: 0 }}>CrisisNet Support</h1>
            <p style={{ fontSize: 12, color: "var(--text-muted)", margin: 0 }}>
              AI triage assistant · Advisory only
            </p>
          </div>
        </div>
        <button className="btn-secondary" onClick={handleLogout}>
          Sign Out
        </button>
      </header>

      {/* Chat Area */}
      <main
        style={{
          flex: 1,
          overflowY: "auto",
          padding: "24px",
          display: "flex",
          flexDirection: "column",
          gap: 24,
        }}
      >
        {messages.length === 0 && (
          <div
            style={{
              flex: 1,
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
              color: "var(--text-muted)",
              textAlign: "center",
            }}
          >
            <Bot size={48} style={{ opacity: 0.2, marginBottom: 16 }} />
            <h2 style={{ fontSize: 20, fontWeight: 600, color: "var(--text-primary)", marginBottom: 8 }}>
              How can we help you today?
            </h2>
            <p style={{ maxWidth: 400, fontSize: 14 }}>
              This is a secure, sandboxed environment. Your messages are analyzed by our AI triage system. If you are in immediate distress, you may be connected to a human counselor.
            </p>
          </div>
        )}

        {messages.map((msg) => (
          <div
            key={msg.id}
            style={{
              display: "flex",
              flexDirection: msg.role === "user" ? "row-reverse" : "row",
              gap: 16,
              alignItems: "flex-end",
            }}
          >
            <div
              style={{
                width: 32,
                height: 32,
                borderRadius: "50%",
                background: msg.role === "user" ? "var(--accent)" : "var(--bg-secondary)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: msg.role === "user" ? "white" : "var(--text-primary)",
                border: msg.role === "bot" ? "1px solid var(--border-subtle)" : "none",
                flexShrink: 0,
              }}
            >
              {msg.role === "user" ? <User size={16} /> : <Bot size={16} />}
            </div>
            
            <div
              style={{
                maxWidth: "70%",
                display: "flex",
                flexDirection: "column",
                alignItems: msg.role === "user" ? "flex-end" : "flex-start",
                gap: 4,
              }}
            >
              <div
                className="animate-fade-in-up"
                style={{
                  padding: "12px 16px",
                  borderRadius: 16,
                  borderBottomRightRadius: msg.role === "user" ? 4 : 16,
                  borderBottomLeftRadius: msg.role === "bot" ? 4 : 16,
                  background: msg.role === "user" ? "var(--accent)" : "var(--bg-secondary)",
                  color: msg.role === "user" ? "white" : "var(--text-primary)",
                  border: msg.role === "bot" ? "1px solid var(--border-subtle)" : "none",
                  fontSize: 14,
                  lineHeight: 1.5,
                  whiteSpace: "pre-wrap",
                }}
              >
                {msg.text}
              </div>
              
              {/* Status Indicators for User Messages */}
              {msg.role === "user" && (
                <div style={{ fontSize: 11, color: "var(--text-muted)", display: "flex", alignItems: "center", gap: 4 }}>
                  {msg.status === "sending" && <><Loader2 size={10} className="animate-spin" /> Analyzing...</>}
                  {msg.status === "pending_review" && (
                    <span style={{ color: "var(--severity-high)", display: "flex", alignItems: "center", gap: 4 }}>
                      <AlertTriangle size={10} /> Connecting to a human counselor...
                    </span>
                  )}
                  {msg.status === "completed" && "Delivered"}
                  {msg.status === "error" && <span style={{ color: "var(--severity-critical)" }}>Failed to send</span>}
                </div>
              )}
            </div>
          </div>
        ))}
        
        {/* Typing Indicator */}
        {isTyping && (
          <div style={{ display: "flex", gap: 16, alignItems: "flex-end" }}>
            <div
              style={{
                width: 32,
                height: 32,
                borderRadius: "50%",
                background: "var(--bg-secondary)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                border: "1px solid var(--border-subtle)",
                flexShrink: 0,
              }}
            >
              <Bot size={16} />
            </div>
            <div
              className="animate-fade-in-up"
              style={{
                padding: "16px",
                borderRadius: 16,
                borderBottomLeftRadius: 4,
                background: "var(--bg-secondary)",
                border: "1px solid var(--border-subtle)",
                display: "flex",
                alignItems: "center",
                gap: 4,
              }}
            >
              <div className="typing-dot" style={{ animationDelay: "0ms" }} />
              <div className="typing-dot" style={{ animationDelay: "150ms" }} />
              <div className="typing-dot" style={{ animationDelay: "300ms" }} />
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </main>

      {/* Input Area */}
      <footer
        style={{
          padding: "24px",
          background: "var(--bg-primary)",
          borderTop: "1px solid var(--border-subtle)",
        }}
      >
        <div
          style={{
            maxWidth: 800,
            margin: "0 auto",
            position: "relative",
          }}
        >
          <textarea
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type your message here... (Press Enter to send)"
            style={{
              width: "100%",
              padding: "16px 56px 16px 20px",
              borderRadius: 24,
              border: "1px solid var(--border-subtle)",
              background: "var(--bg-secondary)",
              color: "var(--text-primary)",
              fontSize: 15,
              resize: "none",
              outline: "none",
              minHeight: 56,
              maxHeight: 120,
              fontFamily: "inherit",
              lineHeight: 1.5,
              boxShadow: "0 4px 20px rgba(0,0,0,0.1)",
            }}
            rows={1}
            disabled={isTyping || messages.some(m => m.status === "pending_review")}
          />
          <button
            onClick={handleSend}
            disabled={!inputText.trim() || isTyping || messages.some(m => m.status === "pending_review")}
            style={{
              position: "absolute",
              right: 8,
              bottom: 8,
              width: 40,
              height: 40,
              borderRadius: "50%",
              background: inputText.trim() && !isTyping ? "var(--accent)" : "var(--bg-secondary)",
              color: inputText.trim() && !isTyping ? "white" : "var(--text-muted)",
              border: "none",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              cursor: inputText.trim() && !isTyping ? "pointer" : "not-allowed",
              transition: "all 0.2s ease",
            }}
          >
            <Send size={18} style={{ marginLeft: 2 }} />
          </button>
        </div>
        <div style={{ textAlign: "center", marginTop: 12, fontSize: 11, color: "var(--text-muted)" }}>
          CrisisNet is an AI research prototype. If you are in real danger, please call emergency services immediately.
        </div>
      </footer>
      
      <style dangerouslySetInnerHTML={{__html: `
        .typing-dot {
          width: 6px;
          height: 6px;
          background: var(--text-muted);
          border-radius: 50%;
          animation: typing 1.4s infinite ease-in-out;
        }
        @keyframes typing {
          0%, 100% { transform: scale(1); opacity: 0.5; }
          50% { transform: scale(1.2); opacity: 1; }
        }
      `}} />
    </div>
  );
}
