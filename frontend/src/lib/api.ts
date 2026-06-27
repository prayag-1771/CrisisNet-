/**
 * API client for CrisisNet backend.
 *
 * Handles authentication, token management, and all API calls.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ── Token Management ──

let accessToken: string | null = null;
let refreshToken: string | null = null;

export function setTokens(access: string, refresh: string) {
  accessToken = access;
  refreshToken = refresh;
  if (typeof window !== "undefined") {
    localStorage.setItem("crisisnet_access", access);
    localStorage.setItem("crisisnet_refresh", refresh);
  }
}

export function loadTokens() {
  if (typeof window !== "undefined") {
    accessToken = localStorage.getItem("crisisnet_access");
    refreshToken = localStorage.getItem("crisisnet_refresh");
  }
}

export function clearTokens() {
  accessToken = null;
  refreshToken = null;
  if (typeof window !== "undefined") {
    localStorage.removeItem("crisisnet_access");
    localStorage.removeItem("crisisnet_refresh");
  }
}

export function getAccessToken() {
  return accessToken;
}

export function getUserRole(): string | null {
  if (!accessToken) return null;
  try {
    let payload = accessToken.split(".")[1];
    // Convert Base64Url to Base64
    payload = payload.replace(/-/g, "+").replace(/_/g, "/");
    // Add padding if necessary
    const pad = payload.length % 4;
    if (pad) {
      if (pad === 1) throw new Error("InvalidLengthError");
      payload += new Array(5 - pad).join("=");
    }
    const decoded = JSON.parse(atob(payload));
    return decoded.role || null;
  } catch (err) {
    return null;
  }
}

// ── Fetch Wrapper ──

async function apiFetch(path: string, options: RequestInit = {}): Promise<Response> {
  loadTokens();

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string> || {}),
  };

  if (accessToken) {
    headers["Authorization"] = `Bearer ${accessToken}`;
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  // If 401, try refresh
  if (res.status === 401 && refreshToken) {
    const refreshRes = await fetch(`${API_BASE}/api/v1/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    if (refreshRes.ok) {
      const data = await refreshRes.json();
      setTokens(data.access_token, data.refresh_token);
      headers["Authorization"] = `Bearer ${data.access_token}`;
      return fetch(`${API_BASE}${path}`, { ...options, headers });
    } else {
      clearTokens();
      throw new Error("Session expired");
    }
  }

  return res;
}

// ── Auth API ──

export async function login(email: string, password: string) {
  const res = await fetch(`${API_BASE}/api/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Login failed");
  }
  const data = await res.json();
  setTokens(data.access_token, data.refresh_token);
  return data;
}

export async function register(email: string, password: string, role: string = "viewer") {
  const res = await fetch(`${API_BASE}/api/v1/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password, role }),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Registration failed");
  }
  return res.json();
}

// ── Messages API ──

export async function submitMessage(text: string) {
  const res = await apiFetch("/api/v1/messages/", {
    method: "POST",
    body: JSON.stringify({ text, source: "demo_simulator" }),
  });
  if (!res.ok) throw new Error("Failed to submit message");
  return res.json();
}

export async function getMessages(severity?: string, skip = 0, limit = 50) {
  let path = `/api/v1/messages/?skip=${skip}&limit=${limit}`;
  if (severity) path += `&severity=${severity}`;
  const res = await apiFetch(path);
  if (!res.ok) throw new Error("Failed to fetch messages");
  return res.json();
}

export async function getMessage(id: number) {
  const res = await apiFetch(`/api/v1/messages/${id}`);
  if (!res.ok) throw new Error("Failed to fetch message");
  return res.json();
}

// ── Review Queue API ──

export async function getReviewQueue() {
  const res = await apiFetch("/api/v1/reviews/queue");
  if (!res.ok) throw new Error("Failed to fetch review queue");
  return res.json();
}

export async function submitReview(
  classificationId: number,
  action: string,
  finalSeverity: string,
  reason: string
) {
  const res = await apiFetch(`/api/v1/reviews/${classificationId}`, {
    method: "POST",
    body: JSON.stringify({
      action,
      final_severity: finalSeverity,
      reason,
    }),
  });
  if (!res.ok) throw new Error("Failed to submit review");
  return res.json();
}

// ── Dashboard API ──

export async function getDashboardStats() {
  const res = await apiFetch("/api/v1/dashboard/stats");
  if (!res.ok) throw new Error("Failed to fetch stats");
  return res.json();
}

export async function getSeverityTrend(days = 7) {
  const res = await apiFetch(`/api/v1/dashboard/severity-trend?days=${days}`);
  if (!res.ok) throw new Error("Failed to fetch trend");
  return res.json();
}

export async function getFalseNegatives() {
  const res = await apiFetch("/api/v1/dashboard/false-negative-tracker");
  if (!res.ok) throw new Error("Failed to fetch false negatives");
  return res.json();
}

// ── WebSocket ──

export function connectWebSocket(onMessage: (event: { type: string; data: any }) => void) {
  const wsUrl = API_BASE.replace("http", "ws") + "/ws/feed";
  const ws = new WebSocket(wsUrl);

  ws.onmessage = (event) => {
    try {
      const parsed = JSON.parse(event.data);
      onMessage(parsed);
    } catch {
      // Ignore non-JSON messages
    }
  };

  ws.onclose = () => {
    // Reconnect after 3 seconds
    setTimeout(() => connectWebSocket(onMessage), 3000);
  };

  // Heartbeat every 30 seconds
  const heartbeat = setInterval(() => {
    if (ws.readyState === WebSocket.OPEN) {
      ws.send("ping");
    }
  }, 30000);

  return () => {
    clearInterval(heartbeat);
    ws.close();
  };
}
