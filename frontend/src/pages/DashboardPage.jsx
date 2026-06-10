import React, { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import { useMealHistory } from "../hooks/useMealHistory";
import { ProgressDashboard } from "../components/dashboard/ProgressDashboard";
import { MacroBreakdown } from "../components/dashboard/MacroBreakdown";
import ProgressRing from "../components/ProgressRing";
import InsightCards from "../components/dashboard/InsightCards";
import DailyCheckpoints from "../components/dashboard/DailyCheckpoints";
import MealList from "../components/dashboard/MealList";
import HydrationWidget from "../components/dashboard/HydrationWidget";
import "./Home.css";

export const DashboardPage = () => {
  const { token, userSettings } = useAuth();
  const { todayMeals, todayCalories, todayMacros, deleteMeal } = useMealHistory();
  const [weeklyData, setWeeklyData] = useState([]);
  const [loading, setLoading] = useState(true);

  // Use real targets from userSettings
  const targets = {
    calories: userSettings?.dailyCalorieGoal || 2000,
    protein: userSettings?.proteinGoal || 150,
    carbs: userSettings?.carbsGoal || 200,
    fat: userSettings?.fatGoal || 70,
  };

  useEffect(() => {
    const loadData = async () => {
      if (!token) {
        // Guest mode: no backend token, use local/empty data
        setWeeklyData([]);
        setLoading(false);
        return;
      }
      try {
        const res = await fetch("/api/logs/weekly", {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!res.ok) {
          setLoading(false);
          return;
        }
        const summary = await res.json();
        
        // Ensure all elements have `date` field mapped from backend `day`
        const mapped = (Array.isArray(summary) ? summary : []).map(item => ({
          ...item,
          date: item.day || item.date,
        }));
        
        setWeeklyData(mapped);
      } catch (err) {
        console.error("Failed to load weekly summary", err);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [token]);

  if (loading) {
    return (
      <div className="flex justify-center items-center h-screen" style={{ color: "var(--text-muted)", fontSize: "1.1rem" }}>
        Loading dashboard...
      </div>
    );
  }

  const remainingCalories = Math.max(0, targets.calories - todayCalories);
  const percentComplete = Math.min(100, Math.round((todayCalories / targets.calories) * 100));

  return (
    <div style={{ maxWidth: "1100px", margin: "0 auto", padding: "24px 16px 80px 16px", display: "flex", flexDirection: "column", gap: "24px" }}>
      <header style={{ marginBottom: "8px" }}>
        <h1 style={{ fontSize: "2rem", fontWeight: 700, color: "var(--text)", margin: "0 0 8px 0" }}>Your Progress</h1>
        <p style={{ color: "var(--text-muted)", margin: 0 }}>Track your daily intake and trends</p>
      </header>

      {/* AI Coaching Insights banner */}
      <InsightCards />

      {/* Main Grid: Left side for detailed weekly graphs & meal list, right side for today's snapshots/checkpoints */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: "24px", alignItems: "start" }}>
        
        {/* Left Column: Weekly Trend and Daily Meal List */}
        <div style={{ display: "flex", flexDirection: "column", gap: "24px", flex: "2 1 600px" }}>
          <ProgressDashboard
            data={weeklyData}
            targetCalories={targets.calories}
          />
          <div className="glass-card" style={{ padding: "24px" }}>
            <MealList todayMeals={todayMeals} deleteMeal={deleteMeal} />
          </div>
        </div>

        {/* Right Column: Today's Intake Progress, Macros, Checkpoints, and Hydration */}
        <div style={{ display: "flex", flexDirection: "column", gap: "24px", flex: "1 1 320px" }}>
          
          {/* Today's Calories Goal Card */}
          <div className="glass-card" style={{ padding: "20px", display: "flex", flexDirection: "column", alignItems: "center" }}>
            <div style={{ alignSelf: "flex-start", marginBottom: "16px" }}>
              <h3 style={{ fontSize: "1.125rem", fontWeight: 600, color: "var(--text)", margin: 0 }}>Today's Calories</h3>
              <p style={{ fontSize: "0.875rem", color: "var(--text-muted)", margin: "4px 0 0 0" }}>Daily budget progress</p>
            </div>
            
            <ProgressRing
              current={todayCalories}
              max={targets.calories}
              size={170}
              strokeWidth={14}
            />

            <div style={{ display: "flex", justifyContent: "space-between", width: "100%", marginTop: "16px", borderTop: "1px solid var(--border-color)", paddingTop: "16px" }}>
              <div style={{ textAlign: "center", flex: 1 }}>
                <span style={{ display: "block", fontSize: "0.85rem", color: "var(--text-muted)" }}>Remaining</span>
                <span style={{ fontSize: "1.1rem", fontWeight: 600, color: "var(--text)" }}>{remainingCalories} kcal</span>
              </div>
              <div style={{ width: "1px", backgroundColor: "var(--border-color)" }}></div>
              <div style={{ textAlign: "center", flex: 1 }}>
                <span style={{ display: "block", fontSize: "0.85rem", color: "var(--text-muted)" }}>Progress</span>
                <span style={{ fontSize: "1.1rem", fontWeight: 600, color: "#10b981" }}>{percentComplete}%</span>
              </div>
            </div>
          </div>

          {/* Today's Macros breakdown */}
          <MacroBreakdown macros={todayMacros} />

          {/* Daily Checkpoints */}
          <DailyCheckpoints
            todayCalories={todayCalories}
            todayMeals={todayMeals}
            todayMacros={todayMacros}
          />

          {/* Hydration Widget */}
          <HydrationWidget />
        </div>
      </div>
    </div>
  );
};
