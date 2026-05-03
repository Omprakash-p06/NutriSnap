import React, { useState, useMemo } from "react";
import { RefreshCw } from "lucide-react";
import { recipes } from "../../services/planner/recipes";
import { suggestMeals } from "../../services/planner/engine";
import { RecipeCard } from "./RecipeCard";

export const MealPlanner = ({ currentIntake, targets }) => {
  const [refreshKey, setRefreshKey] = useState(0);

  const suggestions = useMemo(() => {
    if (!currentIntake || !targets) return [];

    const gaps = {
      calories: targets.calories - currentIntake.calories,
      protein: targets.protein - currentIntake.protein,
      carbs: targets.carbs - currentIntake.carbs,
      fat: targets.fat - currentIntake.fat,
    };

    // Calculate suggestions based on gaps
    let meals = suggestMeals(recipes, gaps);

    // Add randomness for refresh if we have a lot of options
    if (refreshKey > 0 && meals.length > 0) {
      // Just a simple shuffle of the top 5
      const pool = suggestMeals(recipes, gaps).slice(0, 5);
      meals = pool.sort(() => Math.random() - 0.5).slice(0, 3);
    }

    return meals;
  }, [currentIntake, targets, refreshKey]);

  if (!currentIntake || !targets) return null;

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">
            Suggested Meals
          </h3>
          <p className="text-sm text-gray-500">
            Based on your remaining macros
          </p>
        </div>
        <button
          onClick={() => setRefreshKey((k) => k + 1)}
          className="p-2 text-gray-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-full transition-colors"
          title="Refresh Suggestions"
        >
          <RefreshCw
            size={20}
            className={refreshKey > 0 ? "animate-spin-once" : ""}
          />
        </button>
      </div>

      {suggestions.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {suggestions.map((recipe, idx) => (
            <RecipeCard key={`${recipe.id}-${idx}`} recipe={recipe} />
          ))}
        </div>
      ) : (
        <div className="text-center py-8 text-gray-500">
          <p>No meals fit within your current remaining budget.</p>
          <p className="text-sm mt-1">
            Try eating a light snack or adjusting targets.
          </p>
        </div>
      )}
    </div>
  );
};
