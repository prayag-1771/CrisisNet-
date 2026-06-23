"use client";

import React, { useState } from "react";
import { ShieldCheck, CheckCircle, AlertTriangle, RotateCcw, X } from "lucide-react";
import SeverityBadge from "./SeverityBadge";

interface QueueItem {
  message_id: number;
  redacted_text: string;
  ai_severity: string;
  confidence: number;
  reason: string | null;
  submitted_at: string;
  classification_id: number;
}

interface ReviewQueueProps {
  queue: QueueItem[];
  onReview: (
    classificationId: number,
    action: string,
    finalSeverity: string,
    reason: string
  ) => Promise<void>;
}

const SEVERITY_OPTIONS = ["LOW", "MEDIUM", "HIGH", "CRITICAL"];
const ACTION_OPTIONS = [
  { id: "Approve", label: "Approve", icon: CheckCircle, color: "var(--severity-low)" },
  { id: "Escalate", label: "Escalate", icon: AlertTriangle, color: "var(--severity-critical)" },
  { id: "Reclassify", label: "Reclassify", icon: RotateCcw, color: "var(--severity-medium)" },
  { id: "Reject", label: "Reject", icon: X, color: "var(--text-muted)" },
];

export default function ReviewQueue({ queue, onReview }: ReviewQueueProps) {
  const [activeReview, setActiveReview] = useState<number | null>(null);
  const [action, setAction] = useState("Approve");
  const [finalSeverity, setFinalSeverity] = useState("HIGH");
  const [reason, setReason] = useState("");
  const [submitting, setSubmitting] = useState(false);

  if (queue.length === 0) {
    return (
      <div className="glass-card" style={{ padding: 40, textAlign: "center" }}>
        <ShieldCheck
          size={48}
          style={{ color: "var(--severity-low)", margin: "0 auto 16px" }}
        />
        <div style={{ fontSize: 16, fontWeight: 600, marginBottom: 8 }}>
          Queue is clear!
        </div>
        <div style={{ fontSize: 13, color: "var(--text-muted)" }}>
          No messages require human review at this time.
        </div>
      </div>
    );
  }

  const handleSubmit = async (classificationId: number) => {
    if (!reason.trim()) return;
    setSubmitting(true);
    try {
      await onReview(classificationId, action, finalSeverity, reason);
      setActiveReview(null);
      setAction("Approve");
      setFinalSeverity("HIGH");
      setReason("");
    } catch (err) {
      console.error(err);
    }
    setSubmitting(false);
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 8,
          marginBottom: 8,
        }}
      >
        <ShieldCheck size={20} style={{ color: "var(--accent)" }} />
        <span style={{ fontSize: 14, fontWeight: 600 }}>
          {queue.length} case{queue.length !== 1 ? "s" : ""} awaiting review
        </span>
      </div>

      {queue.map((item) => (
        <div
          key={item.classification_id}
          className="glass-card"
          style={{ padding: 20 }}
        >
          {/* Case Header */}
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "flex-start",
              marginBottom: 12,
            }}
          >
            <div>
              <div style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 4 }}>
                Message #{item.message_id} · {new Date(item.submitted_at).toLocaleString()}
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                <SeverityBadge severity={item.ai_severity} />
                <span style={{ fontSize: 12, color: "var(--text-muted)" }}>
                  Confidence: {(item.confidence * 100).toFixed(1)}%
                </span>
              </div>
            </div>
            {activeReview !== item.classification_id && (
              <button
                className="btn-primary"
                style={{ fontSize: 13, padding: "8px 16px" }}
                onClick={() => {
                  setActiveReview(item.classification_id);
                  setFinalSeverity(item.ai_severity);
                }}
              >
                Review
              </button>
            )}
          </div>

          {/* Message Text */}
          <div
            style={{
              padding: 12,
              background: "var(--bg-secondary)",
              borderRadius: 8,
              fontSize: 13,
              color: "var(--text-secondary)",
              lineHeight: 1.6,
              marginBottom: item.reason ? 12 : 0,
            }}
          >
            {item.redacted_text}
          </div>

          {/* AI Reason */}
          {item.reason && (
            <div
              style={{
                fontSize: 12,
                color: "var(--text-muted)",
                fontStyle: "italic",
              }}
            >
              AI Reason: {item.reason}
            </div>
          )}

          {/* Review Form */}
          {activeReview === item.classification_id && (
            <div
              className="animate-fade-in-up"
              style={{
                marginTop: 16,
                padding: 16,
                background: "var(--bg-secondary)",
                borderRadius: 12,
                border: "1px solid var(--border-active)",
              }}
            >
              {/* Action Buttons */}
              <div style={{ marginBottom: 16 }}>
                <div
                  style={{
                    fontSize: 12,
                    fontWeight: 600,
                    color: "var(--text-muted)",
                    marginBottom: 8,
                    textTransform: "uppercase",
                    letterSpacing: "0.05em",
                  }}
                >
                  Action
                </div>
                <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                  {ACTION_OPTIONS.map((opt) => {
                    const Icon = opt.icon;
                    return (
                      <button
                        key={opt.id}
                        onClick={() => setAction(opt.id)}
                        style={{
                          display: "flex",
                          alignItems: "center",
                          gap: 6,
                          padding: "8px 14px",
                          borderRadius: 8,
                          border:
                            action === opt.id
                              ? `2px solid ${opt.color}`
                              : "1px solid var(--border-subtle)",
                          background:
                            action === opt.id
                              ? "rgba(139, 92, 246, 0.1)"
                              : "transparent",
                          color: action === opt.id ? opt.color : "var(--text-secondary)",
                          fontSize: 13,
                          fontWeight: action === opt.id ? 600 : 400,
                          cursor: "pointer",
                          transition: "all 0.2s ease",
                        }}
                      >
                        <Icon size={14} />
                        {opt.label}
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Final Severity */}
              <div style={{ marginBottom: 16 }}>
                <div
                  style={{
                    fontSize: 12,
                    fontWeight: 600,
                    color: "var(--text-muted)",
                    marginBottom: 8,
                    textTransform: "uppercase",
                    letterSpacing: "0.05em",
                  }}
                >
                  Final Severity
                </div>
                <div style={{ display: "flex", gap: 8 }}>
                  {SEVERITY_OPTIONS.map((sev) => (
                    <button
                      key={sev}
                      onClick={() => setFinalSeverity(sev)}
                      className={`severity-badge ${sev.toLowerCase()}`}
                      style={{
                        cursor: "pointer",
                        opacity: finalSeverity === sev ? 1 : 0.4,
                        transform: finalSeverity === sev ? "scale(1.1)" : "scale(1)",
                        transition: "all 0.2s ease",
                      }}
                    >
                      {sev}
                    </button>
                  ))}
                </div>
              </div>

              {/* Reason */}
              <div style={{ marginBottom: 16 }}>
                <div
                  style={{
                    fontSize: 12,
                    fontWeight: 600,
                    color: "var(--text-muted)",
                    marginBottom: 8,
                    textTransform: "uppercase",
                    letterSpacing: "0.05em",
                  }}
                >
                  Reason
                </div>
                <textarea
                  className="input-field"
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  placeholder="Explain your review decision..."
                  rows={3}
                  style={{ resize: "vertical", fontFamily: "inherit" }}
                />
              </div>

              {/* Submit / Cancel */}
              <div style={{ display: "flex", gap: 12, justifyContent: "flex-end" }}>
                <button
                  className="btn-secondary"
                  onClick={() => setActiveReview(null)}
                >
                  Cancel
                </button>
                <button
                  className="btn-primary"
                  onClick={() => handleSubmit(item.classification_id)}
                  disabled={!reason.trim() || submitting}
                  style={{ opacity: !reason.trim() || submitting ? 0.5 : 1 }}
                >
                  {submitting ? "Submitting..." : "Submit Review"}
                </button>
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
