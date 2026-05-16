import { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import { useMealHistory } from "../hooks/useMealHistory";
import { RefreshCw, Loader2, Brain } from "lucide-react";

function AIMealCard({ meal }) {
  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-5 flex flex-col gap-2 hover:border-zinc-700 transition-colors">
      <div className="flex items-center justify-between gap-2">
        <span className="text-xs font-bold uppercase tracking-wider text-zinc-500">{meal.type}</span>
        <span className="text-xs text-zinc-600">{meal.calories} kcal</span>
      </div>
      <h3 className="text-white font-bold text-base leading-tight">{meal.name}</h3>
      {meal.why && (
        <p className="text-zinc-500 text-xs leading-relaxed">{meal.why}</p>
      )}
      <div className="flex gap-3 mt-1 pt-2 border-t border-zinc-800">
        <div className="text-center flex-1">
          <div className="text-[10px] uppercase tracking-wider text-zinc-600">Protein</div>
          <div className="text-sm font-bold text-emerald-400">{Math.round(meal.protein)}g</div>
        </div>
        <div className="text-center flex-1">
          <div className="text-[10px] uppercase tracking-wider text-zinc-600">Carbs</div>
          <div className="text-sm font-bold text-sky-400">{Math.round(meal.carbs)}g</div>
        </div>
        <div className="text-center flex-1">
          <div className="text-[10px] uppercase tracking-wider text-zinc-600">Fat</div>
          <div className="text-sm font-bold text-amber-400">{Math.round(meal.fat)}g</div>
        </div>
      </div>
    </div>
  );
}

export default function PlannerPage() {
  const { token, userSettings } = useAuth();
  const { todayCalories, todayMacros } = useMealHistory();
  const [meals, setMeals] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isAI, setIsAI] = useState(false);

  const fetchSuggestions = async () => {
    setLoading(true);
    setError(null);
    setIsAI(false);

    if (token) {
      // Try backend Gemma-4 suggestions
      try {
        const res = await fetch("/api/planning/suggest", {
          method: "POST",
          headers: { Authorization: `Bearer ${token}` },
        });
        if (res.ok) {
          const data = await res.json();
          if (Array.isArray(data) && data.length > 0) {
            setMeals(data);
            setIsAI(true);
            setLoading(false);
            return;
          }
        }
      } catch (err) {
        console.warn("Backend planning unavailable, using local engine:", err);
      }
    }

    // Local fallback: generate from macros
    const targets = {
      calories: userSettings?.dailyCalorieGoal || 2000,
      protein: userSettings?.proteinGoal || 150,
      carbs: userSettings?.carbsGoal || 200,
      fat: userSettings?.fatGoal || 70,
    };
    const remaining = {
      calories: Math.max(0, targets.calories - (todayCalories || 0)),
      protein: Math.max(0, targets.protein - (todayMacros?.protein || 0)),
      carbs: Math.max(0, targets.carbs - (todayMacros?.carbs || 0)),
      fat: Math.max(0, targets.fat - (todayMacros?.fat || 0)),
    };
    const split = [0.28, 0.32, 0.28, 0.12];
    const templates = [
      { type: "Breakfast", name: "High-protein yogurt bowl", why: "Light, quick breakfast to preserve your calorie budget." },
      { type: "Lunch", name: "Grilled chicken rice bowl", why: "Balanced protein and carbs to anchor your midday energy." },
      { type: "Dinner", name: "Vegetable dal and roti", why: "Filling dinner without overshooting your calorie goal." },
      { type: "Snack", name: "Fruit and nuts", why: "Small satiety boost with healthy fats." },
    ];
    setMeals(templates.map((t, i) => ({
      ...t,
      id: `local-${i}`,
      calories: Math.round(remaining.calories * split[i]),
      protein: Math.round(Math.max(8, remaining.calories * split[i] * 0.08)),
      carbs: Math.round(Math.max(12, remaining.calories * split[i] * 0.12)),
      fat: Math.round(Math.max(4, remaining.calories * split[i] * 0.04)),
    })));
    setLoading(false);
  };

  useEffect(() => {
    fetchSuggestions();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="page-container page-planner max-w-4xl mx-auto pt-6 px-4 pb-28">
      <div className="text-center mb-8 mt-4">
        <h1 className="text-4xl font-bold text-white tracking-tight mb-2">Meal Planner</h1>
        <p className="text-gray-400 text-base">AI-generated meal plan tailored to your goals</p>
      </div>

      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          {isAI ? (
            <span className="flex items-center gap-1.5 text-xs font-bold text-emerald-400 bg-emerald-400/10 border border-emerald-400/20 px-3 py-1.5 rounded-full">
              <Brain size={12} />
              Powered by Gemma 4 (Local)
            </span>
          ) : (
            <span className="text-xs text-zinc-600 bg-zinc-900 border border-zinc-800 px-3 py-1.5 rounded-full">
              Local suggestions (log in for Gemma AI)
            </span>
          )}
        </div>
        <button
          onClick={fetchSuggestions}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 bg-zinc-900 border border-zinc-800 text-zinc-300 rounded-xl hover:bg-zinc-800 hover:text-white transition-all text-sm font-medium disabled:opacity-50"
        >
          {loading ? <Loader2 size={16} className="animate-spin" /> : <RefreshCw size={16} />}
          {loading ? "Generating..." : "Refresh"}
        </button>
      </div>

      {loading ? (
        <div className="flex flex-col items-center justify-center py-20 gap-4">
          <Loader2 size={40} className="text-zinc-600 animate-spin" />
          <p className="text-zinc-500 text-sm">{token ? "Asking Gemma 4 for your meal plan..." : "Loading suggestions..."}</p>
        </div>
      ) : error ? (
        <div className="bg-red-950/30 border border-red-900/50 rounded-2xl p-6 text-center">
          <p className="text-red-400">{error}</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {meals.map((meal, i) => (
            <AIMealCard key={meal.id || i} meal={meal} />
          ))}
        </div>
      )}
    </div>
  );
}
