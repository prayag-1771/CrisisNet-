"use client";

import React from "react";
import {
  LayoutDashboard,
  MessageSquare,
  ShieldCheck,
  BarChart3,
  Send,
  Activity,
} from "lucide-react";

interface SidebarProps {
  activeTab: string;
  onTabChange: (tab: string) => void;
  pendingReviews: number;
}

const navItems = [
  { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
  { id: "simulator", label: "Simulator", icon: Send },
  { id: "feed", label: "Live Feed", icon: Activity },
  { id: "reviews", label: "Review Queue", icon: ShieldCheck },
  { id: "messages", label: "Messages", icon: MessageSquare },
  { id: "analytics", label: "Analytics", icon: BarChart3 },
];

export default function Sidebar({ activeTab, onTabChange, pendingReviews }: SidebarProps) {
  return (
    <aside
      style={{
        width: 260,
        minHeight: "100vh",
        background: "var(--bg-secondary)",
        borderRight: "1px solid var(--border-subtle)",
        padding: "24px 16px",
        display: "flex",
        flexDirection: "column",
        gap: 8,
        position: "fixed",
        left: 0,
        top: 0,
        zIndex: 50,
      }}
    >
      {/* Logo */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 12,
          padding: "8px 12px",
          marginBottom: 24,
        }}
      >
        <div
          style={{
            width: 36,
            height: 36,
            borderRadius: 10,
            background: "linear-gradient(135deg, #8b5cf6, #6366f1)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: 18,
            fontWeight: 800,
            color: "white",
          }}
        >
          C
        </div>
        <div>
          <div style={{ fontSize: 16, fontWeight: 700 }}>CrisisNet</div>
          <div style={{ fontSize: 11, color: "var(--text-muted)" }}>
            Triage Dashboard
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav style={{ display: "flex", flexDirection: "column", gap: 4 }}>
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              id={`nav-${item.id}`}
              onClick={() => onTabChange(item.id)}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 12,
                padding: "10px 14px",
                borderRadius: 10,
                border: "none",
                cursor: "pointer",
                fontSize: 14,
                fontWeight: isActive ? 600 : 400,
                color: isActive ? "white" : "var(--text-secondary)",
                background: isActive
                  ? "linear-gradient(135deg, rgba(139, 92, 246, 0.2), rgba(99, 102, 241, 0.1))"
                  : "transparent",
                transition: "all 0.2s ease",
                position: "relative",
              }}
            >
              <Icon size={18} />
              <span>{item.label}</span>
              {item.id === "reviews" && pendingReviews > 0 && (
                <span
                  style={{
                    marginLeft: "auto",
                    background: "var(--severity-critical)",
                    color: "white",
                    fontSize: 11,
                    fontWeight: 700,
                    padding: "2px 8px",
                    borderRadius: 9999,
                    minWidth: 22,
                    textAlign: "center",
                  }}
                >
                  {pendingReviews}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {/* Bottom Info */}
      <div style={{ marginTop: "auto", padding: "12px", fontSize: 11, color: "var(--text-muted)" }}>
        v0.1.0 · Research Prototype
      </div>
    </aside>
  );
}
