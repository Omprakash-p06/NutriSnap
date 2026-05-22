import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Droplets, Trash2 } from "lucide-react";
import WaterWave from "../animations/WaterWave";
import SpotlightCard from "../common/SpotlightCard";
import { useAuth } from "../../context/AuthContext";

/**
 * HydrationWidget
 * Dashboard card to track and log water intake.
 */
export default function HydrationWidget() {
  const { currentUser, token } = useAuth();
  const [totalWater, setTotalWater] = useState(0);
  const [logs, setLogs] = useState([]); // List of today's water logs
  const [goal] = useState(2000); // 2L goal, could be fetched from settings later
  const [isLogging, setIsLogging] = useState(false);
  const [isDeletingId, setIsDeletingId] = useState(null);

  useEffect(() => {
    if (currentUser) {
      // Local-First Initialization: load from storage immediately
      const savedWater = localStorage.getItem(
        `nutrisnap-water-tab-${currentUser.email}`,
      );
      const todayStr = new Date().toISOString().split("T")[0];
      const parsedData = savedWater ? JSON.parse(savedWater) : null;

      if (parsedData && parsedData.date === todayStr) {
        setTotalWater(parsedData.amount);
        setLogs(parsedData.logs || []);
      }
      fetchTodayWater();
      fetchTodayLogs();
    }
  }, [currentUser, token]);

  const fetchTodayWater = async () => {
    if (!token) return;
    try {
      const res = await fetch("/api/water/today", {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      if (data.total !== undefined) {
        setTotalWater(data.total);
        saveLocally(data.total, logs);
      }
    } catch (err) {
      console.error("Failed to fetch water:", err);
    }
  };

  const saveLocally = (amount, logsList = []) => {
    if (!currentUser) return;
    const todayStr = new Date().toISOString().split("T")[0];
    localStorage.setItem(
      `nutrisnap-water-tab-${currentUser.email}`,
      JSON.stringify({ date: todayStr, amount, logs: logsList }),
    );
  };

  const fetchTodayLogs = async () => {
    if (!token) return;
    try {
      const res = await fetch("/api/water/today/logs", {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setLogs(data || []);
        saveLocally(totalWater, data || []);
      }
    } catch (err) {
      console.error("Failed to fetch water logs:", err);
    }
  };

  const handleDeleteLog = async (logId) => {
    if (!token) return;

    // Find the log to subtract its amount optimistically
    const logToDelete = logs.find(log => log.id === logId);
    const deletedAmount = logToDelete ? logToDelete.amount_ml : 0;

    const newTotal = Math.max(0, totalWater - deletedAmount);
    const updatedLogs = logs.filter(log => log.id !== logId);

    setTotalWater(newTotal);
    setLogs(updatedLogs);
    saveLocally(newTotal, updatedLogs);

    setIsDeletingId(logId);
    try {
      const res = await fetch(`/api/water/${logId}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        fetchTodayWater();
        fetchTodayLogs();
      } else {
        console.error("Failed to delete water log:", res.status);
      }
    } catch (err) {
      console.error("Failed to delete water log:", err);
    } finally {
      setIsDeletingId(null);
    }
  };

  const handleLogWater = async (amount) => {
    if (!token) return;

    // 1. Update UI Optimistically
    const newTotal = totalWater + amount;
    const tempId = Date.now();
    const tempLog = {
      id: tempId,
      amount_ml: amount,
      timestamp: new Date().toISOString(),
      isTemp: true
    };
    const updatedLogs = [tempLog, ...logs];

    setTotalWater(newTotal);
    setLogs(updatedLogs);
    saveLocally(newTotal, updatedLogs);

    setIsLogging(true);
    try {
      const res = await fetch("/api/water/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ amount }),
      });
      if (res.ok) {
        // Refresh logs after adding
        fetchTodayLogs();
      }
    } catch (err) {
      console.error("Failed to sync water to server:", err);
    } finally {
      setIsLogging(false);
    }
  };

  const percent = (totalWater / goal) * 100;

  return (
    <SpotlightCard className="glass-card" glowColor="rgba(62, 207, 160, 0.2)">
      <div style={{ display: "flex", gap: "20px", alignItems: "flex-start" }}>
        <WaterWave percent={percent} />

        <div style={{ flex: 1 }}>
          <h3
            style={{ margin: "0 0 5px 0", fontSize: "1.2rem", fontWeight: 700 }}
          >
            Smart Hydration
          </h3>
          <p style={{ margin: "0 0 15px 0", fontSize: "0.9rem", opacity: 0.7 }}>
            Logged: <strong>{totalWater}ml</strong> / {goal}ml
          </p>

          <div style={{ display: "flex", gap: "10px", marginBottom: "15px" }}>
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              disabled={isLogging}
              onClick={() => handleLogWater(250)}
              className="clay-btn"
              style={{
                padding: "8px 14px",
                fontSize: "0.85rem",
                marginTop: 0,
                background: "var(--accent-mint)",
                display: "flex",
                alignItems: "center",
                gap: "6px",
              }}
            >
              +250ml
            </motion.button>

            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              disabled={isLogging}
              onClick={() => handleLogWater(500)}
              className="clay-btn"
              style={{
                padding: "8px 14px",
                fontSize: "0.85rem",
                marginTop: 0,
                background: "rgba(62, 207, 160, 0.2)",
                color: "var(--text)",
                border: "1px solid var(--accent-mint)",
              }}
            >
              +500ml
            </motion.button>
          </div>

          {/* Display logs with delete buttons */}
          {logs && logs.length > 0 && (
            <div style={{
              fontSize: "0.85rem",
              maxHeight: "150px",
              overflowY: "auto",
              paddingRight: "8px",
            }}>
              <p style={{ margin: "0 0 8px 0", opacity: 0.7 }}>Today's Logs:</p>
              <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                {logs.map((log) => (
                  <div
                    key={log.id}
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      padding: "6px 8px",
                      backgroundColor: "rgba(62, 207, 160, 0.1)",
                      borderRadius: "6px",
                      fontSize: "0.8rem",
                    }}
                  >
                    <span>
                      {log.amount_ml}ml
                      {log.timestamp && ` • ${new Date(log.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}`}
                    </span>
                    <motion.button
                      whileHover={{ scale: 1.1 }}
                      whileTap={{ scale: 0.9 }}
                      onClick={() => handleDeleteLog(log.id)}
                      disabled={isDeletingId === log.id}
                      style={{
                        background: "none",
                        border: "none",
                        cursor: isDeletingId === log.id ? "not-allowed" : "pointer",
                        padding: "2px 4px",
                        display: "flex",
                        alignItems: "center",
                        opacity: isDeletingId === log.id ? 0.5 : 1,
                      }}
                      title="Delete log"
                    >
                      <Trash2 size={14} color="rgba(255, 100, 100, 0.7)" />
                    </motion.button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </SpotlightCard>
  );
}
