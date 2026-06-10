import { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import { useMealHistory } from "../hooks/useMealHistory";
import { RefreshCw, Loader2, Brain, Zap, ChevronDown, ChevronUp } from "lucide-react";
import { recipes as fallbackRecipes } from "../services/planner/recipes";

function RecipeDetail({ mealId, token }) {
  const [details, setDetails] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!mealId) return;

    const fetchDetails = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await fetch(`/api/planning/recipe-details/${mealId}`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!res.ok) {
          throw new Error('Failed to fetch recipe details.');
        }
        const data = await res.json();
        setDetails(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchDetails();
  }, [mealId, token]);

  if (loading) return <div className="text-center p-8"><Loader2 className="animate-spin inline-block text-zinc-500" /></div>;
  if (error) return <div className="text-center p-8 text-red-400">{error}</div>;
  if (!details) return null;

  return (
    <div className="bg-zinc-950 p-6 rounded-b-2xl border-t border-zinc-800">
      <h4 className="text-lg font-bold text-foreground mb-4">Recipe & Nutrition</h4>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <h5 className="text-sm font-semibold text-zinc-400 mb-2">Ingredients</h5>
          <ul className="list-disc list-inside text-zinc-300 text-sm space-y-1">
            {details.ingredients?.map((ing, i) => <li key={i}>{ing}</li>)}
          </ul>
        </div>
        <div>
          <h5 className="text-sm font-semibold text-zinc-400 mb-2">Instructions</h5>
          <p className="text-zinc-300 text-sm">{details.instructions}</p>
        </div>
      </div>
    </div>
  );
}


const pickFallbackImage = (name, type) => {
  if (!fallbackRecipes || !fallbackRecipes.length) {
    return "https://images.unsplash.com/photo-1498837167922-ddd27525d352?auto=format&fit=crop&w=500&q=80";
  }
  const normalizeName = (val) => (val || "").toLowerCase().replace(/[^a-z0-9]+/g, " ").trim();
  const normalized = normalizeName(name);
  const directMatch = fallbackRecipes.find((item) => {
    const itemName = normalizeName(item.name);
    return itemName && normalized && (itemName.includes(normalized) || normalized.includes(itemName));
  });
  if (directMatch?.image) return directMatch.image;

  const mealType = type ? type.toLowerCase() : "";
  const typeMatch = fallbackRecipes.find((item) =>
    (item.tags || []).some((tag) => tag.toLowerCase() === mealType)
  );
  if (typeMatch?.image) return typeMatch.image;

  return fallbackRecipes[0]?.image || "https://images.unsplash.com/photo-1498837167922-ddd27525d352?auto=format&fit=crop&w=500&q=80";
};

function AIMealCard({ meal, onSelect, isSelected }) {
  const [imgSrc, setImgSrc] = useState(meal.image_url);
  const [hasError, setHasError] = useState(false);

  useEffect(() => {
    setImgSrc(meal.image_url);
    setHasError(false);
  }, [meal.image_url]);

  const handleImageError = () => {
    setHasError(true);
  };

  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-2xl flex flex-col gap-2 hover:border-zinc-700 transition-colors">
      <div onClick={() => onSelect(meal.id)} className="p-5 cursor-pointer">
        {imgSrc && !hasError && (
          <img
            src={imgSrc}
            alt={meal.name}
            onError={handleImageError}
            className="w-full h-40 object-cover rounded-lg mb-4"
          />
        )}
        <div className="flex items-center justify-between gap-2">
          <span className="text-xs font-bold uppercase tracking-wider text-zinc-500">{meal.type}</span>
          <span className="text-xs text-zinc-600">{meal.calories} kcal</span>
        </div>
        <h3 className="text-foreground font-bold text-base leading-tight mt-1">{meal.name}</h3>
        {meal.why && (
          <p className="text-zinc-500 text-xs leading-relaxed mt-2">{meal.why}</p>
        )}
        <div className="flex gap-3 mt-3 pt-3 border-t border-zinc-800">
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
         <div className="flex justify-center items-center mt-4 text-zinc-500">
            {isSelected ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
            <span className="text-xs ml-2">{isSelected ? 'Hide' : 'Show'} Recipe</span>
         </div>
      </div>
      {isSelected && <RecipeDetail mealId={meal.id} token={meal.token} />}
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
  const [selectedMeal, setSelectedMeal] = useState(null);

  const handleSelectMeal = (mealId) => {
    setSelectedMeal(prev => prev === mealId ? null : mealId);
  };

  const fetchSuggestions = async () => {
    setLoading(true);
    setError(null);
    setIsAI(false);
    setSelectedMeal(null);

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
            setMeals(data.map(m => ({ ...m, token })));
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
        <h1 className="text-4xl font-bold text-foreground tracking-tight mb-2">Meal Planner</h1>
        <p className="text-zinc-400 text-base">AI-generated meal plan tailored to your goals</p>
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
          className="flex items-center gap-2 px-4 py-2 bg-zinc-900 border border-zinc-800 text-zinc-300 rounded-xl hover:bg-zinc-800 hover:text-foreground transition-all text-sm font-medium disabled:opacity-50"
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
            <AIMealCard key={meal.id || i} meal={meal} onSelect={handleSelectMeal} isSelected={selectedMeal === meal.id} />
          ))}
        </div>
      )}
    </div>
  );
}
