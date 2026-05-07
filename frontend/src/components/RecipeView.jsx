import React, { useState } from "react";

const COLORS = {
  bg: "rgba(15, 23, 42, 0.97)",
  surface: "rgba(30, 41, 59, 0.9)",
  border: "rgba(99, 102, 241, 0.3)",
  accent: "#6366f1",
  accentLight: "#a5b4fc",
  text: "#f1f5f9",
  subtle: "#94a3b8",
  cardBg: "rgba(30, 41, 59, 0.6)",
};

function RecipeCard({ recipe }) {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div
      style={{
        background: COLORS.cardBg,
        border: `1px solid ${COLORS.border}`,
        borderRadius: "14px",
        padding: "14px",
        marginBottom: "12px",
        transition: "all 0.3s ease",
      }}
    >
      <div 
        style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", cursor: "pointer" }}
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div style={{ flex: 1 }}>
          <h4 style={{ margin: "0 0 6px 0", color: COLORS.text, fontSize: "0.95rem" }}>{recipe.title}</h4>
          <div style={{ display: "flex", gap: "8px", fontSize: "0.7rem", color: COLORS.subtle }}>
            <span>⏱ {recipe.time}</span>
            <span>📊 {recipe.difficulty}</span>
          </div>
        </div>
        <div style={{ textAlign: "right" }}>
          <div style={{ fontSize: "0.85rem", fontWeight: "700", color: COLORS.accentLight }}>
            {recipe.nutrition.calories} kcal
          </div>
          <div style={{ fontSize: "0.65rem", color: COLORS.subtle }}>
            P: {recipe.nutrition.protein}g | C: {recipe.nutrition.carbs}g
          </div>
        </div>
      </div>

      {isExpanded && (
        <div style={{ marginTop: "14px", borderTop: `1px solid ${COLORS.border}`, paddingTop: "12px", animation: "fadeIn 0.3s ease" }}>
          <div style={{ marginBottom: "12px" }}>
            <div style={{ fontSize: "0.8rem", fontWeight: "700", color: COLORS.subtle, marginBottom: "4px" }}>INGREDIENTS</div>
            <ul style={{ margin: 0, paddingLeft: "18px", fontSize: "0.82rem", color: COLORS.text }}>
              {recipe.ingredients.map((ing, i) => <li key={i} style={{ marginBottom: "2px" }}>{ing}</li>)}
            </ul>
          </div>
          <div>
            <div style={{ fontSize: "0.8rem", fontWeight: "700", color: COLORS.subtle, marginBottom: "4px" }}>INSTRUCTIONS</div>
            <ol style={{ margin: 0, paddingLeft: "18px", fontSize: "0.82rem", color: COLORS.text }}>
              {recipe.instructions.map((step, i) => <li key={i} style={{ marginBottom: "6px" }}>{step}</li>)}
            </ol>
          </div>
        </div>
      )}
    </div>
  );
}

export default function RecipeView({ token }) {
  const [ingredients, setIngredients] = useState("");
  const [cuisine, setCuisine] = useState("Indian"); // Default to Indian as requested
  const [recipes, setRecipes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const generateRecipes = async () => {
    if (!ingredients.trim()) return;
    setLoading(true);
    setError("");
    
    try {
      const response = await fetch("/api/recipes/generate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({
          ingredients: ingredients.replace(/,/g, " ").split(" ").map(i => i.trim()).filter(i => i),
          cuisine: cuisine
        })
      });

      if (!response.ok) throw new Error("Failed to generate recipes");
      
      const data = await response.json();
      setRecipes(data.recipes);
    } catch (err) {
      setError("AI was unable to cook up recipes. Try again!");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%", padding: "14px" }}>
      {/* Input Section */}
      <div style={{ marginBottom: "16px" }}>
        <div style={{ fontSize: "0.75rem", color: COLORS.subtle, marginBottom: "6px", fontWeight: "600" }}>
          ENTER INGREDIENTS (comma separated)
        </div>
        <div style={{ display: "flex", gap: "8px" }}>
          <input
            type="text"
            value={ingredients}
            onChange={(e) => setIngredients(e.target.value)}
            placeholder="e.g. egg, potato, onion..."
            style={{
              flex: 1,
              background: COLORS.surface,
              border: `1px solid ${COLORS.border}`,
              borderRadius: "10px",
              padding: "10px 12px",
              color: COLORS.text,
              fontSize: "0.85rem",
              outline: "none",
            }}
            onKeyDown={(e) => e.key === "Enter" && generateRecipes()}
          />
          <button
            onClick={generateRecipes}
            disabled={loading || !ingredients.trim()}
            style={{
              background: loading ? COLORS.border : `linear-gradient(135deg, ${COLORS.accent}, #8b5cf6)`,
              border: "none",
              borderRadius: "10px",
              padding: "0 14px",
              color: "#fff",
              cursor: loading ? "not-allowed" : "pointer",
              fontSize: "14px",
              fontWeight: "600",
              transition: "transform 0.2s",
            }}
          >
            {loading ? "..." : "Cook"}
          </button>
        </div>
      </div>

      {/* Cuisine Selector */}
      <div style={{ display: "flex", gap: "10px", marginBottom: "16px" }}>
        {["Indian", "Any"].map((c) => (
          <button
            key={c}
            onClick={() => setCuisine(c)}
            style={{
              padding: "4px 10px",
              borderRadius: "20px",
              fontSize: "0.7rem",
              background: cuisine === c ? COLORS.accent : COLORS.surface,
              border: `1px solid ${cuisine === c ? COLORS.accent : COLORS.border}`,
              color: cuisine === c ? "#fff" : COLORS.subtle,
              cursor: "pointer",
              transition: "all 0.2s",
            }}
          >
            {c}
          </button>
        ))}
      </div>

      {/* Results Section */}
      <div style={{ flex: 1, overflowY: "auto", scrollbarWidth: "thin" }}>
        {error && (
          <div style={{ color: "#f87171", fontSize: "0.8rem", textAlign: "center", marginTop: "20px" }}>
            {error}
          </div>
        )}
        
        {!loading && recipes.length === 0 && !error && (
          <div style={{ textAlign: "center", marginTop: "40px", color: COLORS.subtle }}>
            <div style={{ fontSize: "32px", marginBottom: "12px" }}>👨‍🍳</div>
            <div style={{ fontSize: "0.85rem" }}>Enter your ingredients to see what you can cook!</div>
          </div>
        )}

        {loading && (
          <div style={{ textAlign: "center", marginTop: "40px" }}>
            <div className="chef-loader">🍲</div>
            <div style={{ color: COLORS.subtle, fontSize: "0.8rem", marginTop: "12px" }}>
              AI Chef is thinking...
            </div>
          </div>
        )}

        {recipes.map((r, i) => (
          <RecipeCard key={i} recipe={r} />
        ))}
      </div>

      <style>{`
        .chef-loader {
          font-size: 40px;
          animation: stir 1.5s infinite ease-in-out;
        }
        @keyframes stir {
          0%, 100% { transform: rotate(0deg) translateX(0); }
          25% { transform: rotate(10deg) translateX(5px); }
          75% { transform: rotate(-10deg) translateX(-5px); }
        }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(5px); } to { opacity: 1; transform: translateY(0); } }
      `}</style>
    </div>
  );
}
