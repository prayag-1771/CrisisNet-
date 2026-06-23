"use client";

import React from "react";
import { AlertTriangle } from "lucide-react";

/**
 * Persistent research prototype banner displayed at the top of the dashboard.
 * Required by project spec — must always be visible.
 */
export default function ResearchBanner() {
  return (
    <div className="research-banner">
      <AlertTriangle size={16} />
      <span>
        <strong>Research Prototype</strong> — Not a real crisis service. For
        demonstration purposes only, using synthetic test data.
      </span>
    </div>
  );
}
