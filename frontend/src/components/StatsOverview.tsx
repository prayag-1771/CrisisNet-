"use client";

import React from "react";
import {
  MessageSquare,
  TrendingUp,
  ShieldAlert,
  Clock,
  Users,
  AlertCircle,
} from "lucide-react";

interface StatsOverviewProps {
  stats: {
    total_messages: number;
    severity_distribution: Record<string, number>;
    escalation_rate: number;
    human_override_rate: number;
    avg_resolution_time_seconds: number | null;
    pending_reviews: number;
  } | null;
}

export default function StatsOverview({ stats }: StatsOverviewProps) {
  if (!stats) {
    return (
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(4, 1fr)",
          gap: 20,
        }}
        className="stats-grid"
      >
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="stat-card accent" style={{ height: 120, opacity: 0.5 }}>
            <div style={{ fontSize: 12, color: "var(--text-muted)" }}>Loading...</div>
          </div>
        ))}
      </div>
    );
  }

  const cards = [
    {
      label: "Total Messages",
      value: stats.total_messages,
      icon: MessageSquare,
      color: "accent",
      suffix: "",
    },
    {
      label: "Escalation Rate",
      value: stats.escalation_rate,
      icon: ShieldAlert,
      color: "amber",
      suffix: "%",
    },
    {
      label: "Override Rate",
      value: stats.human_override_rate,
      icon: Users,
      color: "red",
      suffix: "%",
    },
    {
      label: "Pending Reviews",
      value: stats.pending_reviews,
      icon: AlertCircle,
      color: stats.pending_reviews > 0 ? "red" : "green",
      suffix: "",
    },
  ];

  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "repeat(4, 1fr)",
        gap: 20,
      }}
      className="stats-grid"
    >
      {cards.map((card, idx) => {
        const Icon = card.icon;
        return (
          <div
            key={card.label}
            className={`stat-card ${card.color} animate-fade-in-up`}
            style={{ animationDelay: `${idx * 100}ms` }}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "flex-start",
              }}
            >
              <div>
                <div
                  style={{
                    fontSize: 12,
                    fontWeight: 500,
                    color: "var(--text-muted)",
                    textTransform: "uppercase",
                    letterSpacing: "0.05em",
                    marginBottom: 8,
                  }}
                >
                  {card.label}
                </div>
                <div
                  style={{
                    fontSize: 32,
                    fontWeight: 800,
                    lineHeight: 1,
                    letterSpacing: "-0.02em",
                  }}
                >
                  {card.value}
                  <span
                    style={{
                      fontSize: 16,
                      fontWeight: 500,
                      color: "var(--text-secondary)",
                    }}
                  >
                    {card.suffix}
                  </span>
                </div>
              </div>
              <div
                style={{
                  width: 40,
                  height: 40,
                  borderRadius: 10,
                  background: "var(--accent-glow)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                }}
              >
                <Icon size={20} style={{ color: "var(--accent)" }} />
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
