import React, { useState, useEffect } from "react";
import { useRegisterSW } from "virtual:pwa-register/react";
import { RefreshCw, WifiOff, X } from "lucide-react";

export const UpdateToast = () => {
  const [isOffline, setIsOffline] = useState(!navigator.onLine);

  const {
    needRefresh: [needRefresh, setNeedRefresh],
    updateServiceWorker,
  } = useRegisterSW({
    onRegistered(r) {
      // Check for updates periodically - but let's be less aggressive
      if (r && !import.meta.env.DEV) {
        setInterval(
          () => {
            r.update();
          },
          4 * 60 * 60 * 1000,
        ); // Every 4 hours instead of 1
      }
    },
    onRegisterError(error) {
      console.error("SW registration error", error);
    },
  });

  useEffect(() => {
    const handleOnline = () => setIsOffline(false);
    const handleOffline = () => setIsOffline(true);

    window.addEventListener("online", handleOnline);
    window.addEventListener("offline", handleOffline);

    return () => {
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("offline", handleOffline);
    };
  }, []);

  if (!isOffline && !needRefresh) return null;
  if (needRefresh && import.meta.env.DEV) return null;

  return (
    <div
      style={{
        position: "fixed",
        bottom: "20px",
        left: "50%",
        transform: "translateX(-50%)",
        zIndex: 5000, // Higher than most but safe
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: "10px",
        pointerEvents: "none",
        width: "100%",
        maxWidth: "400px",
        padding: "0 20px",
      }}
    >
      {/* Offline Banner */}
      {isOffline && (
        <div
          className="glass-card"
          style={{
            backgroundColor: "#fff3cd",
            color: "#856404",
            padding: "8px 20px",
            borderRadius: "30px",
            display: "flex",
            alignItems: "center",
            gap: "10px",
            fontSize: "0.9rem",
            fontWeight: "bold",
            pointerEvents: "auto",
            boxShadow: "0 4px 12px rgba(0,0,0,0.1)",
          }}
        >
          <WifiOff size={18} />
          <span>You are offline.</span>
        </div>
      )}

      {/* Update Prompt */}
      {needRefresh && (
        <div
          className="glass-card"
          style={{
            display: "flex",
            alignItems: "center",
            gap: "15px",
            pointerEvents: "auto",
            width: "100%",
            padding: "15px 20px",
          }}
        >
          <div
            style={{
              backgroundColor: "var(--primary-coral)",
              color: "#fff",
              padding: "8px",
              borderRadius: "50%",
              display: "flex",
            }}
          >
            <RefreshCw size={20} />
          </div>
          <div style={{ flex: 1 }}>
            <h4 style={{ fontSize: "0.95rem", margin: 0 }}>Update Available</h4>
            <p style={{ fontSize: "0.8rem", margin: 0, opacity: 0.7 }}>
              New version of NutriSnap is ready.
            </p>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <button
              onClick={() => updateServiceWorker(true)}
              className="clay-btn"
              style={{ padding: "6px 15px", fontSize: "0.8rem" }}
            >
              Update
            </button>
            <button
              onClick={() => setNeedRefresh(false)}
              style={{
                background: "transparent",
                border: "none",
                color: "var(--text-muted)",
                cursor: "pointer",
              }}
            >
              <X size={20} />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

