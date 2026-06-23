"use client";

import React from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
} from "recharts";
import { BarChart3 } from "lucide-react";

interface AnalyticsProps {
  stats: {
    total_messages: number;
    severity_distribution: Record<string, number>;
    escalation_rate: number;
    human_override_rate: number;
    avg_resolution_time_seconds: number | null;
    pending_reviews: number;
  } | null;
  trendData: any[];
  falseNegatives: { total_false_negatives: number; cases: any[] } | null;
}

const SEVERITY_COLORS: Record<string, string> = {
  LOW: "#22c55e",
  MEDIUM: "#f59e0b",
  HIGH: "#f97316",
  CRITICAL: "#ef4444",
};

export default function Analytics({ stats, trendData, falseNegatives }: AnalyticsProps) {
  // Pie chart data from severity distribution
  const pieData = stats
    ? Object.entries(stats.severity_distribution).map(([key, value]) => ({
        name: key,
        value,
      }))
    : [];

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
      {/* Charts Row */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 24 }}>
        {/* Severity Distribution Pie */}
        <div className="glass-card" style={{ padding: 24 }}>
          <h4
            style={{
              fontSize: 14,
              fontWeight: 600,
              marginBottom: 20,
              display: "flex",
              alignItems: "center",
              gap: 8,
            }}
          >
            <BarChart3 size={16} style={{ color: "var(--accent)" }} />
            Severity Distribution
          </h4>
          {pieData.length > 0 ? (
            <ResponsiveContainer width="100%" height={260}>
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  paddingAngle={4}
                  dataKey="value"
                >
                  {pieData.map((entry) => (
                    <Cell
                      key={entry.name}
                      fill={SEVERITY_COLORS[entry.name] || "#8b5cf6"}
                    />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    background: "#16161f",
                    border: "1px solid rgba(255,255,255,0.06)",
                    borderRadius: 8,
                    color: "#f0f0f5",
                    fontSize: 13,
                  }}
                />
                <Legend
                  formatter={(value: string) => (
                    <span style={{ color: "var(--text-secondary)", fontSize: 12 }}>
                      {value}
                    </span>
                  )}
                />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div
              style={{
                height: 260,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: "var(--text-muted)",
                fontSize: 13,
              }}
            >
              No data available
            </div>
          )}
        </div>

        {/* Severity Trend Bar Chart */}
        <div className="glass-card" style={{ padding: 24 }}>
          <h4
            style={{
              fontSize: 14,
              fontWeight: 600,
              marginBottom: 20,
              display: "flex",
              alignItems: "center",
              gap: 8,
            }}
          >
            <BarChart3 size={16} style={{ color: "var(--accent)" }} />
            Severity Trend (7 Days)
          </h4>
          {trendData.length > 0 ? (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={trendData}>
                <CartesianGrid
                  strokeDasharray="3 3"
                  stroke="rgba(255,255,255,0.04)"
                />
                <XAxis
                  dataKey="date"
                  tick={{ fill: "#5a5a6e", fontSize: 11 }}
                  axisLine={{ stroke: "rgba(255,255,255,0.06)" }}
                />
                <YAxis
                  tick={{ fill: "#5a5a6e", fontSize: 11 }}
                  axisLine={{ stroke: "rgba(255,255,255,0.06)" }}
                />
                <Tooltip
                  contentStyle={{
                    background: "#16161f",
                    border: "1px solid rgba(255,255,255,0.06)",
                    borderRadius: 8,
                    color: "#f0f0f5",
                    fontSize: 13,
                  }}
                />
                <Bar dataKey="LOW" stackId="a" fill="#22c55e" radius={[0, 0, 0, 0]} />
                <Bar dataKey="MEDIUM" stackId="a" fill="#f59e0b" />
                <Bar dataKey="HIGH" stackId="a" fill="#f97316" />
                <Bar
                  dataKey="CRITICAL"
                  stackId="a"
                  fill="#ef4444"
                  radius={[4, 4, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div
              style={{
                height: 260,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: "var(--text-muted)",
                fontSize: 13,
              }}
            >
              No trend data available
            </div>
          )}
        </div>
      </div>

      {/* False Negative Tracker */}
      <div className="glass-card" style={{ padding: 24 }}>
        <h4
          style={{
            fontSize: 14,
            fontWeight: 600,
            marginBottom: 8,
            display: "flex",
            alignItems: "center",
            gap: 8,
            color: falseNegatives && falseNegatives.total_false_negatives > 0
              ? "var(--severity-critical)"
              : "var(--severity-low)",
          }}
        >
          ⚠ False Negative Tracker
        </h4>
        <p
          style={{
            fontSize: 13,
            color: "var(--text-muted)",
            marginBottom: 16,
          }}
        >
          Cases where AI classified as LOW/MEDIUM but a human reclassified as
          HIGH/CRITICAL. This is the most critical safety metric.
        </p>

        {falseNegatives && falseNegatives.total_false_negatives > 0 ? (
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            <div
              style={{
                fontSize: 28,
                fontWeight: 800,
                color: "var(--severity-critical)",
                marginBottom: 8,
              }}
            >
              {falseNegatives.total_false_negatives}
              <span
                style={{
                  fontSize: 14,
                  fontWeight: 500,
                  color: "var(--text-secondary)",
                  marginLeft: 8,
                }}
              >
                false negatives detected
              </span>
            </div>
            {falseNegatives.cases.map((c: any, idx: number) => (
              <div
                key={idx}
                style={{
                  padding: 12,
                  background: "var(--severity-critical-bg)",
                  borderRadius: 8,
                  border: "1px solid rgba(239, 68, 68, 0.2)",
                  fontSize: 13,
                }}
              >
                AI said <strong>{c.ai_classification}</strong>, human said{" "}
                <strong>{c.human_classification}</strong> — {c.reason}
              </div>
            ))}
          </div>
        ) : (
          <div
            style={{
              padding: 20,
              background: "var(--severity-low-bg)",
              borderRadius: 8,
              textAlign: "center",
              color: "var(--severity-low)",
              fontWeight: 600,
            }}
          >
            ✓ No false negatives detected
          </div>
        )}
      </div>
    </div>
  );
}
