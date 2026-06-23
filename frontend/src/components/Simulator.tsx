"use client";

import React, { useState } from "react";
import { Send, Loader2 } from "lucide-react";
import SeverityBadge from "./SeverityBadge";

interface SimulatorProps {
  onSubmit: (text: string) => Promise<any>;
}

/**
 * The Sandboxed Message Simulator.
 * Users type synthetic crisis messages here to trigger the full LangGraph pipeline.
 */
export default function Simulator({ onSubmit }: SimulatorProps) {
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<any[]>([]);

  // Pre-built demo messages for quick testing
  const demoMessages = [
    "I've been feeling stressed about exams lately. Any study tips?",
    "I can't stop crying. Everything feels pointless. I haven't eaten in days.",
    "I have a plan to end my life tonight. I've written letters to my family.",
    "My roommate locked themselves in the bathroom with a weapon. Please help!",
  ];

  const handleSubmit = async () => {
    if (!text.trim() || loading) return;
    setLoading(true);
    try {
      const result = await onSubmit(text.trim());
      setResults((prev) => [
        { text: text.trim(), result, timestamp: new Date() },
        ...prev,
      ]);
      setText("");
    } catch (err: any) {
      setResults((prev) => [
        { text: text.trim(), error: err.message, timestamp: new Date() },
        ...prev,
      ]);
    }
    setLoading(false);
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
      {/* Input Area */}
      <div className="glass-card" style={{ padding: 24 }}>
        <h3
          style={{
            fontSize: 16,
            fontWeight: 600,
            marginBottom: 16,
            display: "flex",
            alignItems: "center",
            gap: 8,
          }}
        >
          <Send size={18} style={{ color: "var(--accent)" }} />
          Sandboxed Message Simulator
        </h3>
        <p
          style={{
            fontSize: 13,
            color: "var(--text-muted)",
            marginBottom: 16,
          }}
        >
          Submit a synthetic crisis message to trigger the full AI triage
          pipeline. All data is fictional.
        </p>

        <textarea
          id="simulator-input"
          className="input-field"
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Type a synthetic crisis message here..."
          rows={4}
          style={{ resize: "vertical", fontFamily: "inherit" }}
        />

        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginTop: 16,
          }}
        >
          <div style={{ fontSize: 12, color: "var(--text-muted)" }}>
            {text.length} / 5000 characters
          </div>
          <button
            id="simulator-submit"
            className="btn-primary"
            onClick={handleSubmit}
            disabled={!text.trim() || loading}
            style={{ opacity: !text.trim() || loading ? 0.5 : 1 }}
          >
            {loading ? (
              <>
                <Loader2 size={16} className="animate-spin" />
                Processing...
              </>
            ) : (
              <>
                <Send size={16} />
                Submit to Pipeline
              </>
            )}
          </button>
        </div>
      </div>

      {/* Quick Demo Messages */}
      <div className="glass-card" style={{ padding: 24 }}>
        <h4
          style={{
            fontSize: 14,
            fontWeight: 600,
            marginBottom: 12,
            color: "var(--text-secondary)",
          }}
        >
          Quick Demo Messages
        </h4>
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {demoMessages.map((msg, idx) => (
            <button
              key={idx}
              id={`demo-message-${idx}`}
              className="btn-secondary"
              onClick={() => setText(msg)}
              style={{
                textAlign: "left",
                fontSize: 13,
                whiteSpace: "nowrap",
                overflow: "hidden",
                textOverflow: "ellipsis",
              }}
            >
              {msg}
            </button>
          ))}
        </div>
      </div>

      {/* Results History */}
      {results.length > 0 && (
        <div className="glass-card" style={{ padding: 24 }}>
          <h4
            style={{
              fontSize: 14,
              fontWeight: 600,
              marginBottom: 16,
              color: "var(--text-secondary)",
            }}
          >
            Pipeline Results
          </h4>
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {results.map((r, idx) => (
              <div
                key={idx}
                className="animate-slide-in"
                style={{
                  padding: 16,
                  background: "var(--bg-secondary)",
                  borderRadius: 12,
                  border: "1px solid var(--border-subtle)",
                }}
              >
                <div
                  style={{
                    fontSize: 13,
                    color: "var(--text-secondary)",
                    marginBottom: 8,
                  }}
                >
                  &ldquo;{r.text.substring(0, 80)}
                  {r.text.length > 80 ? "..." : ""}&rdquo;
                </div>
                {r.error ? (
                  <div style={{ fontSize: 13, color: "var(--severity-critical)" }}>
                    Error: {r.error}
                  </div>
                ) : (
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: 12,
                    }}
                  >
                    <SeverityBadge severity={r.result?.severity || "UNKNOWN"} />
                    <span style={{ fontSize: 12, color: "var(--text-muted)" }}>
                      ID: {r.result?.id} ·{" "}
                      {new Date(r.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
