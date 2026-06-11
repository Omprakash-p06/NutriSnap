/**
 * MultiFoodDisplay — animated card grid for itemized multi-food results.
 * Includes a serving size control so users can log their actual portion.
 */

import React, { useState, useMemo } from "react";

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

function FoodItemCard({ item, multiplier, index }) {
  const m = multiplier || 1;
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
          {((item.mass_g || 0) * m).toFixed(0)} g
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
          value={(item.calories || 0) * m}
          unit=" kcal"
          color={macroColors.calories}
        />
        <MacroBadge
          label="Protein"
          value={(item.protein || 0) * m}
          color={macroColors.protein}
        />
        <MacroBadge
          label="Carbs"
          value={(item.carbs || 0) * m}
          color={macroColors.carbs}
        />
        <MacroBadge label="Fat" value={(item.fat || 0) * m} color={macroColors.fat} />
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

/** Serving Size Control — gram input with quick-tap presets */
function ServingSizeControl({ baseGrams, servingGrams, onChange }) {
  const PRESETS = [50, 100, 150, 200, 250, 300];

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
      <label
        style={{
          fontSize: "0.75rem",
          color: "#94a3b8",
          fontWeight: 600,
          textTransform: "uppercase",
          letterSpacing: "0.05em",
        }}
      >
        How much did you have?
      </label>

      {/* Gram input + stepper */}
      <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
        <button
          id="serving-dec-btn"
          onClick={() => onChange(Math.max(10, servingGrams - 25))}
          style={stepperStyle}
          title="Decrease by 25g"
        >
          −
        </button>
        <div style={{ position: "relative", flex: 1 }}>
          <input
            id="serving-grams-input"
            type="number"
            min={10}
            max={2000}
            value={servingGrams}
            onChange={(e) => {
              const v = parseInt(e.target.value, 10);
              if (!isNaN(v) && v >= 10) onChange(v);
            }}
            style={{
              width: "100%",
              background: "rgba(0,0,0,0.3)",
              border: "1px solid rgba(255,255,255,0.15)",
              borderRadius: "10px",
              padding: "10px 38px 10px 14px",
              color: "#f8f8f8",
              fontSize: "1rem",
              fontWeight: 700,
              outline: "none",
              textAlign: "center",
              boxSizing: "border-box",
            }}
          />
          <span
            style={{
              position: "absolute",
              right: "12px",
              top: "50%",
              transform: "translateY(-50%)",
              color: "#64748b",
              fontSize: "0.8rem",
            }}
          >
            g
          </span>
        </div>
        <button
          id="serving-inc-btn"
          onClick={() => onChange(Math.min(2000, servingGrams + 25))}
          style={stepperStyle}
          title="Increase by 25g"
        >
          +
        </button>
      </div>

      {/* Quick preset chips */}
      <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
        {PRESETS.map((p) => (
          <button
            key={p}
            id={`preset-${p}g-btn`}
            onClick={() => onChange(p)}
            style={{
              padding: "4px 12px",
              borderRadius: "999px",
              fontSize: "0.75rem",
              fontWeight: 600,
              cursor: "pointer",
              border: servingGrams === p
                ? "1px solid #6366f1"
                : "1px solid rgba(255,255,255,0.12)",
              background: servingGrams === p
                ? "rgba(99,102,241,0.2)"
                : "rgba(255,255,255,0.05)",
              color: servingGrams === p ? "#a5b4fc" : "#94a3b8",
              transition: "all 0.15s ease",
            }}
          >
            {p}g
          </button>
        ))}
        {baseGrams && !PRESETS.includes(baseGrams) && (
          <button
            id={`preset-detected-btn`}
            onClick={() => onChange(baseGrams)}
            style={{
              padding: "4px 12px",
              borderRadius: "999px",
              fontSize: "0.75rem",
              fontWeight: 600,
              cursor: "pointer",
              border: servingGrams === baseGrams
                ? "1px solid #f97316"
                : "1px solid rgba(249,115,22,0.3)",
              background: servingGrams === baseGrams
                ? "rgba(249,115,22,0.15)"
                : "rgba(249,115,22,0.06)",
              color: "#f97316",
              transition: "all 0.15s ease",
            }}
          >
            {baseGrams}g (detected)
          </button>
        )}
      </div>

      {baseGrams && baseGrams !== 100 && (
        <p style={{ margin: 0, fontSize: "0.72rem", color: "#475569", fontStyle: "italic" }}>
          Nutrition shown is scaled from the detected {baseGrams}g portion.
          Adjust above to match what you actually ate.
        </p>
      )}
      {(!baseGrams || baseGrams === 100) && (
        <p style={{ margin: 0, fontSize: "0.72rem", color: "#475569", fontStyle: "italic" }}>
          Nutrition is per 100g. Adjust above to match your actual serving.
        </p>
      )}
    </div>
  );
}

const stepperStyle = {
  width: "38px",
  height: "38px",
  borderRadius: "10px",
  border: "1px solid rgba(255,255,255,0.12)",
  background: "rgba(255,255,255,0.07)",
  color: "#f8f8f8",
  fontSize: "1.3rem",
  fontWeight: 700,
  cursor: "pointer",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  flexShrink: 0,
  lineHeight: 1,
};

export default function MultiFoodDisplay({
  result,
  handleSaveToDiary,
  category,
  setCategory,
  multiplier,
  setMultiplier,
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

  // Base serving = detected mass (or 100g for search results)
  const baseGrams = Math.round(total_mass_g || 100);

  // servingGrams is the local display state; multiplier is the canonical ratio
  const [servingGrams, setServingGrams] = useState(baseGrams);

  const m = multiplier || 1;

  const handleServingChange = (grams) => {
    const clamped = Math.max(10, Math.min(2000, grams));
    setServingGrams(clamped);
    if (setMultiplier) {
      setMultiplier(parseFloat((clamped / baseGrams).toFixed(4)));
    }
  };

  // Scaled totals for live preview
  const scaledCal = (total_calories || 0) * m;
  const scaledMass = baseGrams * m;
  const scaledProtein = (total_protein || 0) * m;
  const scaledCarbs = (total_carbs || 0) * m;
  const scaledFat = (total_fat || 0) * m;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
      {/* Totals row — live scaled */}
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
          {m !== 1 && (
            <span style={{ color: "#f97316", marginLeft: "8px", fontWeight: 500, fontSize: "0.78rem" }}>
              (×{m.toFixed(2)} serving)
            </span>
          )}
        </p>
        <p
          style={{
            margin: "0 0 10px",
            fontSize: "1.6rem",
            fontWeight: 800,
            color: "#f8f8f8",
            transition: "all 0.2s ease",
          }}
        >
          {scaledCal.toFixed(0)}{" "}
          <span style={{ fontSize: "1rem", fontWeight: 400, color: "#94a3b8" }}>
            kcal
          </span>
          &nbsp;·&nbsp;{scaledMass.toFixed(0)}{" "}
          <span style={{ fontSize: "1rem", fontWeight: 400, color: "#94a3b8" }}>
            g
          </span>
        </p>
        <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
          <MacroBadge
            label="Protein"
            value={scaledProtein}
            color={macroColors.protein}
          />
          <MacroBadge
            label="Carbs"
            value={scaledCarbs}
            color={macroColors.carbs}
          />
          <MacroBadge
            label="Fat"
            value={scaledFat}
            color={macroColors.fat}
          />
          </div>

          {/* Health Score */}
          {validation_summary?.health_score && (
          <HealthBadge score={validation_summary.health_score} />
          )}
          </div>

      {/* Per-item cards — scaled */}
      <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
        {items.map((item, i) => (
          <FoodItemCard key={`${item.label}-${i}`} item={item} multiplier={m} index={i} />
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
          gap: "16px",
          animation: "fadeSlideIn 0.5s ease 0.3s both",
        }}
      >
        {/* Serving Size Control */}
        <ServingSizeControl
          baseGrams={baseGrams}
          servingGrams={servingGrams}
          onChange={handleServingChange}
        />

        {/* Divider */}
        <div style={{ borderTop: "1px solid rgba(255,255,255,0.06)" }} />

        {/* Meal Category */}
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
              id="meal-category-select"
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
          id="save-to-diary-btn"
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
          Save {scaledCal.toFixed(0)} kcal to Food Diary
        </button>
      </div>

      <style>{`
        @keyframes fadeSlideIn {
          from { opacity: 0; transform: translateY(12px); }
          to   { opacity: 1; transform: translateY(0); }
        }
        input[type=number]::-webkit-inner-spin-button,
        input[type=number]::-webkit-outer-spin-button { opacity: 0.4; }
      `}</style>
    </div>
  );
}
