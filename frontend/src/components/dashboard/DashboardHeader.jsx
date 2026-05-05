import StreakBadge from "../StreakBadge.jsx";
import ProgressRing from "../ProgressRing";
import { Settings as SettingsIcon, Activity } from "lucide-react";
import SpotlightCard from "../common/SpotlightCard";
import { useAuth } from "../../context/AuthContext";

/**
 * DashboardHeader component showing calorie intake and streak.
 */
export default function DashboardHeader({
  todayCalories,
  userSettings,
  setIsSettingsOpen,
}) {
  const { bmi } = useAuth();

  return (
    <SpotlightCard className="glass-card dashboard-card">
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "20px",
        }}
      >
        <h2 style={{ margin: 0, fontSize: "1.1rem", opacity: 0.85 }}>
          Today's Dashboard
        </h2>
        <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
          {bmi && (
            <div
              className="bmi-chip"
              style={{
                background: "rgba(255, 255, 255, 0.1)",
                padding: "4px 10px",
                borderRadius: "12px",
                display: "flex",
                alignItems: "center",
                gap: "6px",
                fontSize: "0.85rem",
                fontWeight: 600,
              }}
            >
              <Activity size={14} />
              <span>BMI: {bmi}</span>
            </div>
          )}
          <StreakBadge streak={userSettings?.streak || 0} />
        </div>
      </div>
      <div className="dashboard-grid">
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            position: "relative",
          }}
        >
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              width: "100%",
              marginBottom: "10px",
            }}
          >
            <h3 style={{ margin: 0, opacity: 0.8 }}>Daily Intake</h3>
            <button
              onClick={() => setIsSettingsOpen(true)}
              style={{
                background: "transparent",
                border: "none",
                cursor: "pointer",
                color: "var(--text-muted)",
              }}
            >
              <SettingsIcon size={20} />
            </button>
          </div>
          <ProgressRing
            current={todayCalories}
            max={userSettings.dailyCalorieGoal}
            size={180}
          />
        </div>
      </div>
    </SpotlightCard>
  );
}
