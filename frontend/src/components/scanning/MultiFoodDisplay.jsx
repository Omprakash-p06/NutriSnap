/**
 * MultiFoodDisplay — animated card grid for itemized multi-food results.
 * Consumes the result from usePrediction().
 */

import React from "react";

const macroColors = {
  calories: "#f97316",
  protein: "#3b82f6",
  carbs: "#22c55e",
  fat: "#a855f7",
};

function MacroBadge({ label, value, unit = "g", color }) {
  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "4px",
        padding: "2px 10px",
        borderRadius: "999px",
        fontSize: "0.75rem",
        fontWeight: 600,
        background: `${color}22`,
        color: color,
        border: `1px solid ${color}44`,
      }}
    >
      {label}: {typeof value === "number" ? value.toFixed(1) : value}
      {unit}
    </span>
  );
}

function HealthBadge({ score }) {
  if (!score) return null;

  const colors = {
    A: "#22c55e",
    B: "#84cc16",
    C: "#eab308",
    D: "#f97316",
    E: "#ef4444",
  };

  const color = colors[score.grade] || "#94a3b8";

  return (
    <div
      className="health-badge-container"
      style={{
        display: "flex",
        alignItems: "center",
        gap: "12px",
        marginTop: "12px",
        paddingTop: "12px",
        borderTop: "1px solid rgba(255,255,255,0.1)",
      }}
    >
      <div
        style={{
          width: "40px",
          height: "40px",
          borderRadius: "10px",
          background: color,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: "1.5rem",
          fontWeight: 900,
          color: "#fff",
          boxShadow: `0 4px 12px ${color}44`,
        }}
        title={score.summary}
      >
        {score.grade}
      </div>
      <div>
        <p style={{ margin: 0, fontSize: "0.85rem", fontWeight: 700, color: "#f8f8f8" }}>
          Health Grade: {score.grade}
        </p>
        <p style={{ margin: 0, fontSize: "0.75rem", color: "#94a3b8" }}>
          {score.summary} • <span style={{ fontStyle: "italic" }} title="Calculated based on nutrient density, fiber, and fat balance.">Why this grade?</span>
        </p>
      </div>
    </div>
  );
}

function FoodItemCard({ item, index }) {
  return (
    <div
      style={{
        background: "rgba(255,255,255,0.05)",
        border: "1px solid rgba(255,255,255,0.1)",
        borderRadius: "16px",
        padding: "16px 20px",
        animation: `fadeSlideIn 0.35s ease ${index * 0.07}s both`,
      }}
    >
      {/* Header */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "10px",
        }}
      >
        <h4
          style={{
            margin: 0,
            fontSize: "1rem",
            fontWeight: 700,
            color: "#f8f8f8",
            textTransform: "capitalize",
          }}
        >
          {item.label}
        </h4>
        <span style={{ fontSize: "0.75rem", color: "#94a3b8" }}>
          {item.confidence
            ? `${(item.confidence * 100).toFixed(0)}% conf.`
            : ""}
        </span>
      </div>

      {/* Mass */}
      <p style={{ margin: "0 0 8px", fontSize: "0.85rem", color: "#94a3b8" }}>
        Estimated mass:{" "}
        <strong style={{ color: "#f8f8f8" }}>
          {item.mass_g?.toFixed(0)} g
        </strong>
      </p>

      {/* Macros */}
      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          gap: "6px",
          marginBottom: "10px",
        }}
      >
        <MacroBadge
          label="Cal"
          value={item.calories}
          unit=" kcal"
          color={macroColors.calories}
        />
        <MacroBadge
          label="Protein"
          value={item.protein}
          color={macroColors.protein}
        />
        <MacroBadge
          label="Carbs"
          value={item.carbs}
          color={macroColors.carbs}
        />
        <MacroBadge label="Fat" value={item.fat} color={macroColors.fat} />
      </div>

      {/* Ingredients */}
      {item.ingredients && (
        <p
          style={{
            margin: 0,
            fontSize: "0.78rem",
            color: "#64748b",
            fontStyle: "italic",
          }}
        >
          {item.ingredients}
        </p>
      )}
    </div>
  );
}

export default function MultiFoodDisplay({
  result,
  handleSaveToDiary,
  category,
  setCategory,
}) {
  if (!result) return null;

  const {
    items = [],
    total_calories,
    total_mass_g,
    total_protein,
    total_carbs,
    total_fat,
    validation_summary,
  } = result;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
      {/* Validation warning */}
      {validation_summary && !validation_summary.is_valid && (
        <div
          style={{
            background: "#f97316AA",
            borderRadius: "12px",
            padding: "10px 16px",
            fontSize: "0.82rem",
            color: "#fff",
          }}
        >
          ⚠ {validation_summary.reasoning}
        </div>
      )}

      {/* Totals row */}
      <div
        style={{
          background: "linear-gradient(135deg, #1e293b, #0f172a)",
          borderRadius: "16px",
          padding: "16px 20px",
          border: "1px solid rgba(99,102,241,0.3)",
        }}
      >
        <p
          style={{
            margin: "0 0 8px",
            fontWeight: 700,
            color: "#a5b4fc",
            fontSize: "0.85rem",
            letterSpacing: "0.08em",
            textTransform: "uppercase",
          }}
        >
          Meal Totals
        </p>
        <p
          style={{
            margin: "0 0 10px",
            fontSize: "1.6rem",
            fontWeight: 800,
            color: "#f8f8f8",
          }}
        >
          {total_calories?.toFixed(0)}{" "}
          <span style={{ fontSize: "1rem", fontWeight: 400, color: "#94a3b8" }}>
            kcal
          </span>
          &nbsp;·&nbsp;{total_mass_g?.toFixed(0)}{" "}
          <span style={{ fontSize: "1rem", fontWeight: 400, color: "#94a3b8" }}>
            g
          </span>
        </p>
        <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
          <MacroBadge
            label="Protein"
            value={total_protein}
            color={macroColors.protein}
          />
          <MacroBadge
            label="Carbs"
            value={total_carbs}
            color={macroColors.carbs}
          />
          <MacroBadge
            label="Fat"
            value={total_fat}
            color={macroColors.fat}
          />
          </div>

          {/* Health Score */}
          {validation_summary?.health_score && (
          <HealthBadge score={validation_summary.health_score} />
          )}
          </div>

      {/* Per-item cards */}
      <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
        {items.map((item, i) => (
          <FoodItemCard key={`${item.label}-${i}`} item={item} index={i} />
        ))}
      </div>

      {/* Action Section */}
      <div
        style={{
          marginTop: "20px",
          padding: "20px",
          background: "rgba(255,255,255,0.03)",
          borderRadius: "20px",
          border: "1px solid rgba(255,255,255,0.08)",
          display: "flex",
          flexDirection: "column",
          gap: "15px",
          animation: "fadeSlideIn 0.5s ease 0.3s both",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <div style={{ flex: 1 }}>
            <label
              style={{
                display: "block",
                fontSize: "0.75rem",
                color: "#94a3b8",
                marginBottom: "6px",
                fontWeight: 600,
                textTransform: "uppercase",
                letterSpacing: "0.05em",
              }}
            >
              Meal Category
            </label>
            <select
              value={category || "Snacks"}
              onChange={(e) => setCategory && setCategory(e.target.value)}
              className="category-select"
              style={{
                width: "100%",
                background: "rgba(0,0,0,0.2)",
                border: "1px solid rgba(255,255,255,0.1)",
                borderRadius: "10px",
                padding: "10px",
                color: "#f8f8f8",
                fontSize: "0.9rem",
                outline: "none",
              }}
            >
              <option>Breakfast</option>
              <option>Lunch</option>
              <option>Dinner</option>
              <option>Snacks</option>
            </select>
          </div>
        </div>

        <button
          onClick={handleSaveToDiary}
          className="clay-btn"
          style={{
            margin: 0,
            width: "100%",
            background: "linear-gradient(135deg, #6366f1, #4f46e5)",
            boxShadow: "0 8px 20px rgba(79, 70, 229, 0.3)",
            padding: "14px",
            fontSize: "1rem",
            fontWeight: 700,
            border: "none",
            borderRadius: "12px",
            color: "#fff",
            cursor: "pointer",
          }}
        >
          Save to Food Diary
        </button>
      </div>

      <style>{`
        @keyframes fadeSlideIn {
          from { opacity: 0; transform: translateY(12px); }
          to   { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </div>
  );
}
