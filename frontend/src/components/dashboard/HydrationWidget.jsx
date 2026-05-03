import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Droplets } from "lucide-react";
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
  const [goal] = useState(2000); // 2L goal, could be fetched from settings later
  const [isLogging, setIsLogging] = useState(false);

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
      }
      fetchTodayWater();
    }
  }, [currentUser]);

  const fetchTodayWater = async () => {
    if (!token) return;
    try {
      const res = await fetch("/api/water/today", {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      if (data.total !== undefined) {
        setTotalWater(data.total);
        saveLocally(data.total);
      }
    } catch (err) {
      console.error("Failed to fetch water:", err);
    }
  };

  const saveLocally = (amount) => {
    if (!currentUser) return;
    const todayStr = new Date().toISOString().split("T")[0];
    localStorage.setItem(
      `nutrisnap-water-tab-${currentUser.email}`,
      JSON.stringify({ date: todayStr, amount }),
    );
  };

  const handleLogWater = async (amount) => {
    if (!token) return;

    // 1. Update UI Optimistically
    const newTotal = totalWater + amount;
    setTotalWater(newTotal);
    saveLocally(newTotal);

    setIsLogging(true);
    try {
      await fetch("/api/water/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ amount }),
      });
    } catch (err) {
      console.error("Failed to sync water to server:", err);
    } finally {
      setIsLogging(false);
    }
  };

  const percent = (totalWater / goal) * 100;

  return (
    <SpotlightCard className="glass-card" glowColor="rgba(62, 207, 160, 0.2)">
      <div style={{ display: "flex", gap: "20px", alignItems: "center" }}>
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

          <div style={{ display: "flex", gap: "10px" }}>
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
        </div>
      </div>
    </SpotlightCard>
  );
}
