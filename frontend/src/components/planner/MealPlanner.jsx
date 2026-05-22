import React, { useState, useEffect } from "react";
import { RefreshCw } from "lucide-react";
import { RecipeCard } from "./RecipeCard";
import { useAuth } from "../../context/AuthContext";
import { recipes as fallbackRecipes } from "../../services/planner/recipes";

export const MealPlanner = ({ currentIntake, targets }) => {
  const [suggestions, setSuggestions] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [refreshKey, setRefreshKey] = useState(0);
  const [selectedRecipe, setSelectedRecipe] = useState(null);
  const [recipeDetails, setRecipeDetails] = useState(null);
  const [isRecipeLoading, setIsRecipeLoading] = useState(false);
  const [recipeError, setRecipeError] = useState(null);
  const { token } = useAuth();

  const normalizeName = (value) =>
    (value || "")
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, " ")
      .trim();

  const pickFallbackImage = (recipe) => {
    if (!fallbackRecipes.length) return null;
    const normalized = normalizeName(recipe?.name);
    const directMatch = fallbackRecipes.find((item) => {
      const itemName = normalizeName(item.name);
      return itemName && normalized && (itemName.includes(normalized) || normalized.includes(itemName));
    });
    if (directMatch?.image) return directMatch.image;

    const type = recipe?.type ? recipe.type.toLowerCase() : "";
    const typeMatch = fallbackRecipes.find((item) =>
      (item.tags || []).some((tag) => tag.toLowerCase() === type)
    );
    if (typeMatch?.image) return typeMatch.image;

    return fallbackRecipes[0]?.image || null;
  };

  const withImages = (items) =>
    items.map((item, index) => ({
      ...item,
      id: item.id || `suggestion-${index}`,
      image: item.image || item.image_url || pickFallbackImage(item),
    }));

  useEffect(() => {
    const fetchSuggestions = async () => {
      if (!token) return;
      setIsLoading(true);
      setError(null);
      try {
        const res = await fetch("/api/planning/suggest", {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });
        if (!res.ok) {
          throw new Error("Failed to fetch suggestions");
        }
        const data = await res.json();
        setSuggestions(withImages(Array.isArray(data) ? data : []));
      } catch (err) {
        setError(err.message);
      } finally {
        setIsLoading(false);
      }
    };

    fetchSuggestions();
  }, [token, refreshKey]);

  const handleRecipeClick = async (recipe) => {
    if (selectedRecipe?.id === recipe.id) {
      setSelectedRecipe(null);
      setRecipeDetails(null);
      setRecipeError(null);
      setIsRecipeLoading(false);
      return;
    }

    setSelectedRecipe(recipe);
    setRecipeDetails(null);
    setRecipeError(null);

    if (!token) {
      return;
    }

    setIsRecipeLoading(true);
    try {
      const res = await fetch("/api/planning/recipe-details", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          name: recipe.name,
          type: recipe.type,
          calories: recipe.calories,
          protein: recipe.protein,
          carbs: recipe.carbs,
          fat: recipe.fat,
        }),
      });

      if (!res.ok) {
        throw new Error("Failed to fetch recipe details");
      }

      const details = await res.json();
      setRecipeDetails({ ...recipe, ...details });
    } catch (err) {
      setRecipeError(err.message || "Failed to fetch recipe details");
    } finally {
      setIsRecipeLoading(false);
    }
  };

  const handleCloseModal = () => {
    setSelectedRecipe(null);
    setRecipeDetails(null);
    setRecipeError(null);
    setIsRecipeLoading(false);
  };

  if (isLoading) {
    return <div>Loading suggestions...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  const activeRecipe = recipeDetails || selectedRecipe;
  const nutrition = activeRecipe?.nutrition || {};
  const calories = nutrition.calories ?? activeRecipe?.calories;
  const protein = nutrition.protein ?? activeRecipe?.protein;
  const carbs = nutrition.carbs ?? activeRecipe?.carbs;
  const fat = nutrition.fat ?? activeRecipe?.fat;

  return (
    <div className="glass-card" style={{ padding: "24px" }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "24px" }}>
        <div>
          <h3 style={{ fontSize: "1.2rem", fontWeight: 600, color: "var(--text)", margin: 0 }}>
            Suggested Meals
          </h3>
          <p style={{ fontSize: "0.9rem", color: "var(--text-muted)", margin: "4px 0 0 0" }}>
            Based on your profile and remaining macros
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
            <div key={`${recipe.id}-${idx}`} onClick={() => handleRecipeClick(recipe)}>
              <RecipeCard recipe={recipe} />
            </div>
          ))}
        </div>
      ) : (
        <div style={{ textAlign: "center", padding: "32px 0", color: "var(--text-muted)" }}>
          <p style={{ margin: 0 }}>No meal suggestions available at the moment.</p>
        </div>
      )}
      {selectedRecipe ? (
        <div
          style={{
            marginTop: "24px",
            padding: "20px",
            borderRadius: "16px",
            border: "1px solid var(--border)",
            background: "rgba(17, 17, 17, 0.85)",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
            <div>
              <h4 style={{ margin: 0, color: "var(--text)", fontSize: "1.1rem" }}>{activeRecipe?.name || "Recipe Details"}</h4>
              {activeRecipe?.summary ? (
                <p style={{ margin: "6px 0 0 0", color: "var(--text-muted)", fontSize: "0.9rem" }}>{activeRecipe.summary}</p>
              ) : activeRecipe?.why ? (
                <p style={{ margin: "6px 0 0 0", color: "var(--text-muted)", fontSize: "0.9rem" }}>{activeRecipe.why}</p>
              ) : null}
            </div>
            <button
              onClick={handleCloseModal}
              style={{
                background: "transparent",
                border: "none",
                color: "var(--text-muted)",
                cursor: "pointer",
                fontSize: "0.9rem",
              }}
            >
              Close
            </button>
          </div>

          {isRecipeLoading ? (
            <p style={{ color: "var(--text-muted)" }}>Loading recipe details...</p>
          ) : (
            <>
              {recipeError ? (
                <p style={{ color: "#ff7a7a", fontWeight: 600 }}>{recipeError}</p>
              ) : null}
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "16px" }}>
                <div>
                  <h5 style={{ margin: "0 0 8px 0", color: "var(--text)" }}>Ingredients</h5>
                  {activeRecipe?.ingredients && activeRecipe.ingredients.length > 0 ? (
                    <ul style={{ margin: 0, paddingLeft: "18px", color: "var(--text-muted)", fontSize: "0.9rem" }}>
                      {activeRecipe.ingredients.map((ing, i) => (
                        <li key={i}>{ing}</li>
                      ))}
                    </ul>
                  ) : (
                    <p style={{ margin: 0, color: "var(--text-muted)", fontSize: "0.9rem" }}>
                      Recipe details are not available for this suggestion yet.
                    </p>
                  )}
                </div>
                <div>
                  <h5 style={{ margin: "0 0 8px 0", color: "var(--text)" }}>Steps</h5>
                  {activeRecipe?.steps && activeRecipe.steps.length > 0 ? (
                    <ol style={{ margin: 0, paddingLeft: "18px", color: "var(--text-muted)", fontSize: "0.9rem" }}>
                      {activeRecipe.steps.map((step, i) => (
                        <li key={i}>{step}</li>
                      ))}
                    </ol>
                  ) : (
                    <p style={{ margin: 0, color: "var(--text-muted)", fontSize: "0.9rem" }}>
                      Steps will appear once the recipe is ready.
                    </p>
                  )}
                </div>
              </div>

              <div style={{ marginTop: "16px", display: "flex", flexWrap: "wrap", gap: "16px" }}>
                <div>
                  <p style={{ margin: 0, fontSize: "0.75rem", color: "var(--text-muted)", textTransform: "uppercase" }}>Calories</p>
                  <p style={{ margin: 0, fontWeight: 600, color: "var(--text)" }}>{calories ?? "-"} kcal</p>
                </div>
                <div>
                  <p style={{ margin: 0, fontSize: "0.75rem", color: "var(--text-muted)", textTransform: "uppercase" }}>Protein</p>
                  <p style={{ margin: 0, fontWeight: 600, color: "var(--text)" }}>{protein ?? "-"} g</p>
                </div>
                <div>
                  <p style={{ margin: 0, fontSize: "0.75rem", color: "var(--text-muted)", textTransform: "uppercase" }}>Carbs</p>
                  <p style={{ margin: 0, fontWeight: 600, color: "var(--text)" }}>{carbs ?? "-"} g</p>
                </div>
                <div>
                  <p style={{ margin: 0, fontSize: "0.75rem", color: "var(--text-muted)", textTransform: "uppercase" }}>Fat</p>
                  <p style={{ margin: 0, fontWeight: 600, color: "var(--text)" }}>{fat ?? "-"} g</p>
                </div>
              </div>
            </>
          )}
        </div>
      ) : null}
    </div>
  );
};
