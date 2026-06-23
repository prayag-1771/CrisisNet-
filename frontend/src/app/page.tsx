"use client";

import React, { useState, useEffect } from "react";
import ResearchBanner from "../components/ResearchBanner";
import Sidebar from "../components/Sidebar";
import StatsOverview from "../components/StatsOverview";
import Simulator from "../components/Simulator";
import LiveFeed from "../components/LiveFeed";
import ReviewQueue from "../components/ReviewQueue";
import MessageList from "../components/MessageList";
import Analytics from "../components/Analytics";
import LoginScreen from "../components/LoginScreen";

import {
  login,
  getDashboardStats,
  getSeverityTrend,
  getFalseNegatives,
  getReviewQueue,
  getMessages,
  submitMessage,
  submitReview,
  connectWebSocket,
  getAccessToken,
  clearTokens,
} from "../lib/api";

export default function Home() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loginError, setLoginError] = useState<string | null>(null);

  const [activeTab, setActiveTab] = useState("dashboard");

  // State
  const [stats, setStats] = useState<any>(null);
  const [trendData, setTrendData] = useState<any[]>([]);
  const [falseNegatives, setFalseNegatives] = useState<any>(null);
  const [queue, setQueue] = useState<any[]>([]);
  const [messages, setMessages] = useState<any[]>([]);
  const [feedEvents, setFeedEvents] = useState<any[]>([]);

  // ── Authentication ──

  useEffect(() => {
    // Check if we have a token on load
    if (getAccessToken()) {
      setIsAuthenticated(true);
      fetchAllData();
    }
  }, []);

  const handleLogin = async (email: string, pass: string) => {
    try {
      setLoginError(null);
      await login(email, pass);
      setIsAuthenticated(true);
      fetchAllData();
    } catch (err: any) {
      setLoginError(err.message);
    }
  };

  const handleLogout = () => {
    clearTokens();
    setIsAuthenticated(false);
  };

  // ── Data Fetching ──

  const fetchAllData = async () => {
    try {
      const [s, t, fn, q, m] = await Promise.all([
        getDashboardStats(),
        getSeverityTrend(),
        getFalseNegatives(),
        getReviewQueue(),
        getMessages(),
      ]);
      setStats(s);
      setTrendData(t);
      setFalseNegatives(fn);
      setQueue(q);
      setMessages(m);
    } catch (err) {
      console.error("Failed to fetch initial data", err);
    }
  };

  // ── WebSocket ──

  useEffect(() => {
    if (!isAuthenticated) return;

    const cleanup = connectWebSocket((event) => {
      // Add to live feed
      setFeedEvents((prev) => [
        { type: event.type, data: event.data, timestamp: new Date() },
        ...prev,
      ]);

      // Depending on event, refresh certain data
      if (event.type === "new_message") {
        getMessages().then(setMessages);
        getDashboardStats().then(setStats);
        if (event.data.requires_review) {
          getReviewQueue().then(setQueue);
        }
      }
      if (event.type === "queue_update") {
        getReviewQueue().then(setQueue);
        getDashboardStats().then(setStats);
        getMessages().then(setMessages); // Status might have changed
      }
    });

    return cleanup;
  }, [isAuthenticated]);

  // ── Handlers ──

  const handleSimulatorSubmit = async (text: string) => {
    return await submitMessage(text);
  };

  const handleReviewSubmit = async (
    classificationId: number,
    action: string,
    finalSeverity: string,
    reason: string
  ) => {
    await submitReview(classificationId, action, finalSeverity, reason);
    // Refresh queue immediately
    const q = await getReviewQueue();
    setQueue(q);
  };

  // ── Rendering ──

  if (!isAuthenticated) {
    return <LoginScreen onLogin={handleLogin} error={loginError} />;
  }

  return (
    <div style={{ display: "flex", minHeight: "100vh" }}>
      <Sidebar
        activeTab={activeTab}
        onTabChange={setActiveTab}
        pendingReviews={queue.length}
      />

      <main
        style={{
          flex: 1,
          marginLeft: 260,
          display: "flex",
          flexDirection: "column",
        }}
      >
        <ResearchBanner />

        <div style={{ padding: "32px 40px", maxWidth: 1200 }}>
          {/* Header */}
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              marginBottom: 32,
            }}
          >
            <div>
              <h2 style={{ fontSize: 24, fontWeight: 700, marginBottom: 4 }}>
                {activeTab === "dashboard" && "Dashboard Overview"}
                {activeTab === "simulator" && "Message Simulator"}
                {activeTab === "feed" && "Live Event Feed"}
                {activeTab === "reviews" && "Human Review Queue"}
                {activeTab === "messages" && "All Messages"}
                {activeTab === "analytics" && "Analytics"}
              </h2>
              <p style={{ fontSize: 14, color: "var(--text-muted)" }}>
                {new Date().toLocaleDateString(undefined, {
                  weekday: "long",
                  year: "numeric",
                  month: "long",
                  day: "numeric",
                })}
              </p>
            </div>
            <button className="btn-secondary" onClick={handleLogout}>
              Sign Out
            </button>
          </div>

          {/* Content area based on active tab */}
          <div className="animate-fade-in-up" key={activeTab}>
            {activeTab === "dashboard" && (
              <div style={{ display: "flex", flexDirection: "column", gap: 32 }}>
                <StatsOverview stats={stats} />
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 32 }}>
                  <div>
                    <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16 }}>
                      Recent Events
                    </h3>
                    <LiveFeed events={feedEvents.slice(0, 5)} />
                  </div>
                  <div>
                    <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16 }}>
                      Priority Queue
                    </h3>
                    <ReviewQueue queue={queue.slice(0, 3)} onReview={handleReviewSubmit} />
                  </div>
                </div>
              </div>
            )}

            {activeTab === "simulator" && (
              <Simulator onSubmit={handleSimulatorSubmit} />
            )}

            {activeTab === "feed" && <LiveFeed events={feedEvents} />}

            {activeTab === "reviews" && (
              <ReviewQueue queue={queue} onReview={handleReviewSubmit} />
            )}

            {activeTab === "messages" && <MessageList messages={messages} />}

            {activeTab === "analytics" && (
              <Analytics
                stats={stats}
                trendData={trendData}
                falseNegatives={falseNegatives}
              />
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
