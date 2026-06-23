"use client";

import React from "react";
import { Activity } from "lucide-react";
import SeverityBadge from "./SeverityBadge";

interface FeedEvent {
  type: string;
  data: {
    message_id?: number;
    severity?: string;
    confidence?: number;
    requires_review?: boolean;
    action?: string;
    final_severity?: string;
    classification_id?: number;
    reviewer_id?: number;
  };
  timestamp: Date;
}

interface LiveFeedProps {
  events: FeedEvent[];
}

/**
 * Real-time event feed showing WebSocket events from the backend.
 */
export default function LiveFeed({ events }: LiveFeedProps) {
  if (events.length === 0) {
    return (
      <div className="glass-card" style={{ padding: 40, textAlign: "center" }}>
        <Activity
          size={48}
          style={{ color: "var(--text-muted)", margin: "0 auto 16px" }}
        />
        <div style={{ fontSize: 16, fontWeight: 600, marginBottom: 8 }}>
          No events yet
        </div>
        <div style={{ fontSize: 13, color: "var(--text-muted)" }}>
          Submit a message through the Simulator or wait for WebSocket events.
          Events will appear here in real-time.
        </div>
      </div>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      {events.map((event, idx) => (
        <div
          key={idx}
          className="glass-card animate-slide-in"
          style={{
            padding: 16,
            display: "flex",
            alignItems: "center",
            gap: 16,
            animationDelay: `${idx * 50}ms`,
          }}
        >
          {/* Event Type Indicator */}
          <div
            style={{
              width: 8,
              height: 8,
              borderRadius: "50%",
              background:
                event.type === "new_message"
                  ? "var(--accent)"
                  : event.type === "queue_update"
                  ? "var(--severity-high)"
                  : "var(--severity-low)",
              flexShrink: 0,
            }}
          />

          {/* Event Content */}
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: 14, fontWeight: 500 }}>
              {event.type === "new_message" && (
                <>
                  New message #{event.data.message_id} classified
                  {event.data.severity && (
                    <span style={{ marginLeft: 8 }}>
                      <SeverityBadge severity={event.data.severity} />
                    </span>
                  )}
                </>
              )}
              {event.type === "queue_update" && (
                <>
                  Review action:{" "}
                  <strong>{event.data.action}</strong> on classification #
                  {event.data.classification_id}
                </>
              )}
              {event.type === "classification_update" && (
                <>Classification updated for message #{event.data.message_id}</>
              )}
              {event.type === "resolution" && (
                <>Message #{event.data.message_id} resolved</>
              )}
              {event.type === "pong" && (
                <span style={{ color: "var(--text-muted)" }}>Heartbeat</span>
              )}
            </div>
            {event.data.confidence !== undefined && (
              <div
                style={{
                  fontSize: 12,
                  color: "var(--text-muted)",
                  marginTop: 4,
                }}
              >
                Confidence: {(event.data.confidence * 100).toFixed(1)}%
                {event.data.requires_review && (
                  <span
                    style={{
                      marginLeft: 8,
                      color: "var(--severity-high)",
                      fontWeight: 600,
                    }}
                  >
                    ⚠ Requires Review
                  </span>
                )}
              </div>
            )}
          </div>

          {/* Timestamp */}
          <div style={{ fontSize: 11, color: "var(--text-muted)", flexShrink: 0 }}>
            {event.timestamp.toLocaleTimeString()}
          </div>
        </div>
      ))}
    </div>
  );
}
