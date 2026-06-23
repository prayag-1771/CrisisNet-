"use client";

import React from "react";

/**
 * Severity badge with color-coded styling and optional pulse animation for CRITICAL.
 */
export default function SeverityBadge({ severity }: { severity: string }) {
  const level = severity?.toLowerCase() || "low";
  return (
    <span className={`severity-badge ${level}`}>
      {level === "critical" && <span className="pulse-dot" />}
      {severity}
    </span>
  );
}
