"use client";

import React from "react";
import { MessageSquare, ChevronRight } from "lucide-react";
import SeverityBadge from "./SeverityBadge";

interface MessageItem {
  id: number;
  source: string;
  redacted_text: string | null;
  submitted_at: string;
  severity: string | null;
  confidence: number | null;
}

interface MessageListProps {
  messages: MessageItem[];
  onSelect?: (id: number) => void;
}

export default function MessageList({ messages, onSelect }: MessageListProps) {
  if (messages.length === 0) {
    return (
      <div className="glass-card" style={{ padding: 40, textAlign: "center" }}>
        <MessageSquare
          size={48}
          style={{ color: "var(--text-muted)", margin: "0 auto 16px" }}
        />
        <div style={{ fontSize: 16, fontWeight: 600, marginBottom: 8 }}>
          No messages yet
        </div>
        <div style={{ fontSize: 13, color: "var(--text-muted)" }}>
          Submit a message through the Simulator to see it here.
        </div>
      </div>
    );
  }

  return (
    <div className="glass-card" style={{ overflow: "hidden" }}>
      <table className="data-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Message Preview</th>
            <th>Source</th>
            <th>Severity</th>
            <th>Confidence</th>
            <th>Time</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {messages.map((msg) => (
            <tr
              key={msg.id}
              onClick={() => onSelect?.(msg.id)}
              style={{ cursor: onSelect ? "pointer" : "default" }}
            >
              <td style={{ fontWeight: 600, color: "var(--text-primary)" }}>
                #{msg.id}
              </td>
              <td style={{ maxWidth: 300 }}>
                <div
                  style={{
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    whiteSpace: "nowrap",
                    maxWidth: 300,
                  }}
                >
                  {msg.redacted_text || "[Pending]"}
                </div>
              </td>
              <td>
                <span
                  style={{
                    fontSize: 12,
                    padding: "4px 8px",
                    borderRadius: 6,
                    background: "var(--bg-secondary)",
                    color: "var(--text-muted)",
                  }}
                >
                  {msg.source}
                </span>
              </td>
              <td>
                {msg.severity ? (
                  <SeverityBadge severity={msg.severity} />
                ) : (
                  <span style={{ color: "var(--text-muted)" }}>—</span>
                )}
              </td>
              <td>
                {msg.confidence !== null ? (
                  <span
                    style={{
                      fontWeight: 600,
                      color:
                        msg.confidence >= 0.75
                          ? "var(--severity-low)"
                          : "var(--severity-high)",
                    }}
                  >
                    {(msg.confidence * 100).toFixed(1)}%
                  </span>
                ) : (
                  <span style={{ color: "var(--text-muted)" }}>—</span>
                )}
              </td>
              <td style={{ fontSize: 12 }}>
                {new Date(msg.submitted_at).toLocaleString()}
              </td>
              <td>
                <ChevronRight size={16} style={{ color: "var(--text-muted)" }} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
