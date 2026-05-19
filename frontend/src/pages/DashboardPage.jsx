import React, { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import { db } from "../services/db";
import { getWeeklySummary, calculateTDEE } from "../services/aggregator";
import { useMealHistory } from "../hooks/useMealHistory";
import { ProgressDashboard } from "../components/dashboard/ProgressDashboard";
import { MacroBreakdown } from "../components/dashboard/MacroBreakdown";
import { MealPlanner } from "../components/planner/MealPlanner";
import HydrationWidget from "../components/dashboard/HydrationWidget";

export const DashboardPage = () => {
  const { currentUser, token, userSettings } = useAuth();
  const { todayCalories, todayMacros } = useMealHistory();
  const [weeklyData, setWeeklyData] = useState([]);
  const [loading, setLoading] = useState(true);

  // Use real targets from userSettings
  const targets = {
    calories: userSettings?.dailyCalorieGoal || 2000,
    protein: userSettings?.proteinGoal || 150,
    carbs: userSettings?.carbsGoal || 200,
    fat: userSettings?.fatGoal || 70,
  };

  const currentIntake = {
    calories: todayCalories,
    protein: todayMacros.protein,
    carbs: todayMacros.carbs,
    fat: todayMacros.fat,
  };

  useEffect(() => {
    const loadData = async () => {
      if (!token) {
        // Guest mode: no backend token, skip fetch and use local data only
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
          return; // Silently fail for guest/unauth
        }
        const summary = await res.json();
        setWeeklyData(Array.isArray(summary) ? summary : []);
      } catch (err) {
        console.error("Failed to load weekly summary", err);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [token]); // todayMacros removed — new object ref every render causes infinite loop

  if (loading) {
    return (
      <div className="flex justify-center items-center h-screen">
        Loading dashboard...
      </div>
    );
  }

  return (
    <div style={{ maxWidth: "1000px", margin: "0 auto", padding: "24px 16px 80px 16px", display: "flex", flexDirection: "column", gap: "24px" }}>
      <header style={{ marginBottom: "16px" }}>
        <h1 style={{ fontSize: "2rem", fontWeight: 700, color: "var(--text)", margin: "0 0 8px 0" }}>Your Progress</h1>
        <p style={{ color: "var(--text-muted)", margin: 0 }}>Track your daily intake and trends</p>
      </header>

      {/* Charts Section */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", gap: "24px" }}>
        <div style={{ flex: "2 1 600px" }}>
          <ProgressDashboard
            data={weeklyData}
            targetCalories={targets.calories}
          />
        </div>
        <div style={{ flex: "1 1 300px", display: "flex", flexDirection: "column", gap: "24px" }}>
          <MacroBreakdown macros={todayMacros} />
          <HydrationWidget />
        </div>
      </div>

      {/* Meal Planner Section */}
      <div style={{ marginTop: "24px" }}>
        <MealPlanner currentIntake={currentIntake} targets={targets} />
      </div>
    </div>
  );
};
