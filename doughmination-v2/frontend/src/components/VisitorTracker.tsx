/*
 * Copyright (c) 2026 Clove Twilight
 * Licensed under the ESAL-1.3 Licence.
 * See LICENCE.md in the project root for full licence information.
 */

import { useEffect } from "react";
import { useLocation } from "react-router-dom";

/**
 * Pings POST /helper on every route change so the backend can log the visit.
 * Renders nothing. Mount inside <BrowserRouter> so useLocation works.
 *
 * Fires for ALL paths, including the 404 catch-all (which is the point —
 * the backend wants to see attempts at non-existent URLs too).
 */
const VisitorTracker = () => {
  const location = useLocation();

  useEffect(() => {
    const path = `${location.pathname}${location.search}${location.hash}`;
    const body = JSON.stringify({ path });

    // Prefer sendBeacon when leaving the page; otherwise plain fetch.
    // Both are fire-and-forget — we never block rendering on the log call.
    try {
      if (typeof navigator !== "undefined" && navigator.sendBeacon) {
        const blob = new Blob([body], { type: "application/json" });
        const ok = navigator.sendBeacon("/api/helper", blob);
        if (ok) return;
      }
    } catch {
      // fall through to fetch
    }

    fetch("/api/helper", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body,
      keepalive: true,
      credentials: "same-origin",
    }).catch(() => {
      // Silently ignore — visitor logging must never break the UI.
    });
  }, [location.pathname, location.search, location.hash]);

  return null;
};

export default VisitorTracker;
