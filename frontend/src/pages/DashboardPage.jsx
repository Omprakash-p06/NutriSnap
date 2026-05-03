import React, { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import { db } from "../services/db";
import { getWeeklySummary, calculateTDEE } from "../services/aggregator";
import { useMealHistory } from "../hooks/useMealHistory";
import { ProgressDashboard } from "../components/dashboard/ProgressDashboard";
import { MacroBreakdown } from "../components/dashboard/MacroBreakdown";
import { MealPlanner } from "../components/planner/MealPlanner";

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
        setLoading(false);
        return;
      }
      try {
        const res = await fetch("/api/logs/weekly", {
          headers: { Authorization: `Bearer ${token}` },
        });
        const summary = await res.json();
        setWeeklyData(summary);
      } catch (err) {
        console.error("Failed to load weekly summary", err);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [token, todayCalories, todayMacros]);

  if (loading) {
    return (
      <div className="flex justify-center items-center h-screen">
        Loading dashboard...
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto pb-20 px-4 pt-6 space-y-6">
      <header className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Your Progress</h1>
        <p className="text-gray-500">Track your daily intake and trends</p>
      </header>

      {/* Charts Section */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="md:col-span-2">
          <ProgressDashboard
            data={weeklyData}
            targetCalories={targets.calories}
          />
        </div>
        <div>
          <MacroBreakdown macros={todayMacros} />
        </div>
      </div>

      {/* Meal Planner Section */}
      <div className="pt-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">
          What to eat next?
        </h2>
        <MealPlanner currentIntake={currentIntake} targets={targets} />
      </div>
    </div>
  );
};
