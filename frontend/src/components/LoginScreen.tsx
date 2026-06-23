"use client";

import React, { useState } from "react";
import { LogIn, Loader2, UserPlus } from "lucide-react";

interface LoginScreenProps {
  onLogin: (email: string, password: string) => Promise<void>;
  error: string | null;
}

export default function LoginScreen({ onLogin, error }: LoginScreenProps) {
  const [email, setEmail] = useState("admin@crisisnet.dev");
  const [password, setPassword] = useState("admin1234");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    await onLogin(email, password);
    setLoading(false);
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: 20,
      }}
    >
      <div
        className="glass-card animate-fade-in-up"
        style={{ padding: 40, width: "100%", maxWidth: 420 }}
      >
        {/* Logo */}
        <div
          style={{
            textAlign: "center",
            marginBottom: 32,
          }}
        >
          <div
            style={{
              width: 56,
              height: 56,
              borderRadius: 14,
              background: "linear-gradient(135deg, #8b5cf6, #6366f1)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: 24,
              fontWeight: 800,
              color: "white",
              margin: "0 auto 16px",
            }}
          >
            C
          </div>
          <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 4 }}>
            CrisisNet
          </h1>
          <p style={{ fontSize: 13, color: "var(--text-muted)" }}>
            Research Prototype · Sign in to access the dashboard
          </p>
        </div>

        {error && (
          <div
            style={{
              padding: 12,
              background: "var(--severity-critical-bg)",
              border: "1px solid rgba(239, 68, 68, 0.2)",
              borderRadius: 8,
              color: "var(--severity-critical)",
              fontSize: 13,
              marginBottom: 20,
              textAlign: "center",
            }}
          >
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: 16 }}>
            <label
              style={{
                fontSize: 12,
                fontWeight: 600,
                color: "var(--text-muted)",
                textTransform: "uppercase",
                letterSpacing: "0.05em",
                display: "block",
                marginBottom: 6,
              }}
            >
              Email
            </label>
            <input
              id="login-email"
              type="email"
              className="input-field"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@crisisnet.dev"
              required
            />
          </div>

          <div style={{ marginBottom: 24 }}>
            <label
              style={{
                fontSize: 12,
                fontWeight: 600,
                color: "var(--text-muted)",
                textTransform: "uppercase",
                letterSpacing: "0.05em",
                display: "block",
                marginBottom: 6,
              }}
            >
              Password
            </label>
            <input
              id="login-password"
              type="password"
              className="input-field"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
            />
          </div>

          <button
            id="login-submit"
            type="submit"
            className="btn-primary"
            style={{ width: "100%", justifyContent: "center" }}
            disabled={loading}
          >
            {loading ? (
              <>
                <Loader2 size={16} className="animate-spin" />
                Signing in...
              </>
            ) : (
              <>
                <LogIn size={16} />
                Sign In
              </>
            )}
          </button>
        </form>

        {/* Demo Credentials */}
        <div
          style={{
            marginTop: 24,
            padding: 16,
            background: "var(--bg-secondary)",
            borderRadius: 10,
            fontSize: 12,
            color: "var(--text-muted)",
          }}
        >
          <div style={{ fontWeight: 600, marginBottom: 8 }}>
            Demo Credentials:
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            <div>
              <strong>Admin:</strong> admin@crisisnet.dev / admin1234
            </div>
            <div>
              <strong>Reviewer:</strong> reviewer@crisisnet.dev / reviewer1234
            </div>
            <div>
              <strong>Viewer:</strong> viewer@crisisnet.dev / viewer1234
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
