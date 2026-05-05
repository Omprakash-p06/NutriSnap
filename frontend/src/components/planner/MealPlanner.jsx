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
    <div className="glass-card" style={{ padding: "24px" }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "24px" }}>
        <div>
          <h3 style={{ fontSize: "1.2rem", fontWeight: 600, color: "var(--text)", margin: 0 }}>
            Suggested Meals
          </h3>
          <p style={{ fontSize: "0.9rem", color: "var(--text-muted)", margin: "4px 0 0 0" }}>
            Based on your remaining macros
          </p>
        </div>
        <button
          onClick={() => setRefreshKey((k) => k + 1)}
          style={{
            background: "transparent",
            border: "none",
            color: "var(--text-muted)",
            cursor: "pointer",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            padding: "8px",
            borderRadius: "50%"
          }}
          title="Refresh Suggestions"
        >
          <RefreshCw
            size={20}
            style={refreshKey > 0 ? { transform: "rotate(180deg)", transition: "transform 0.3s ease" } : { transition: "transform 0.3s ease" }}
          />
        </button>
      </div>

      {suggestions.length > 0 ? (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "16px" }}>
          {suggestions.map((recipe, idx) => (
            <RecipeCard key={`${recipe.id}-${idx}`} recipe={recipe} />
          ))}
        </div>
      ) : (
        <div style={{ textAlign: "center", padding: "32px 0", color: "var(--text-muted)" }}>
          <p style={{ margin: 0 }}>No meals fit within your current remaining budget.</p>
          <p style={{ fontSize: "0.9rem", marginTop: "4px" }}>
            Try eating a light snack or adjusting targets.
          </p>
        </div>
      )}
    </div>
  );
};
