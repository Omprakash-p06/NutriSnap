import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { db } from '../services/db';
import { getWeeklySummary, calculateTDEE } from '../services/aggregator';
import { useMealHistory } from '../hooks/useMealHistory';
import { ProgressDashboard } from '../components/dashboard/ProgressDashboard';
import { MacroBreakdown } from '../components/dashboard/MacroBreakdown';
import { MealPlanner } from '../components/planner/MealPlanner';

export const DashboardPage = () => {
  const { currentUser } = useAuth();
  const { todayCalories, todayMacros } = useMealHistory();
  const [weeklyData, setWeeklyData] = useState([]);
  const [loading, setLoading] = useState(true);

  // Mock profile data - in a real app this comes from user settings
  const userProfile = {
    gender: 'male',
    age: 30,
    height: 175,
    weight: 75,
    activityLevel: 'moderate'
  };

  const tdee = calculateTDEE(userProfile);
  
  // Calculate targets
  const targets = {
    calories: tdee,
    protein: Math.round((tdee * 0.3) / 4), // 30% protein
    carbs: Math.round((tdee * 0.4) / 4),   // 40% carbs
    fat: Math.round((tdee * 0.3) / 9)      // 30% fat
  };

  const currentIntake = {
    calories: todayCalories,
    protein: todayMacros.protein,
    carbs: todayMacros.carbs,
    fat: todayMacros.fat
  };

  useEffect(() => {
    const loadData = async () => {
      const userId = currentUser?.email || 'guest';
      try {
        const summary = await getWeeklySummary(db, userId);
        // Ensure today's data is live from the hook
        if (summary.length > 0) {
          summary[summary.length - 1].calories = todayCalories;
          summary[summary.length - 1].protein = todayMacros.protein;
          summary[summary.length - 1].carbs = todayMacros.carbs;
          summary[summary.length - 1].fat = todayMacros.fat;
        }
        setWeeklyData(summary);
      } catch (err) {
        console.error("Failed to load weekly summary", err);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [currentUser, todayCalories, todayMacros]);

  if (loading) {
    return <div className="flex justify-center items-center h-screen">Loading dashboard...</div>;
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
          <ProgressDashboard data={weeklyData} targetCalories={targets.calories} />
        </div>
        <div>
          <MacroBreakdown macros={todayMacros} />
        </div>
      </div>

      {/* Meal Planner Section */}
      <div className="pt-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">What to eat next?</h2>
        <MealPlanner currentIntake={currentIntake} targets={targets} />
      </div>
    </div>
  );
};
