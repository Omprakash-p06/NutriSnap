import { useState, useEffect } from "react";

export default function PortionSlider({ baseNutrition, onMultiplierChange }) {
  const [multiplier, setMultiplier] = useState(1.0);

  const handleSlider = (e) => {
    const val = parseFloat(e.target.value);
    setMultiplier(val);
    if (onMultiplierChange) {
      onMultiplierChange(val);
    }
  };

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <span style={{ fontWeight: "600" }}>Adjust Portion:</span>
        <span className="clay-badge" style={styles.badge}>
          {multiplier.toFixed(2)}x
        </span>
      </div>

      <input
        type="range"
        min="0.25"
        max="3"
        step="0.25"
        value={multiplier}
        onChange={handleSlider}
        className="custom-slider"
        style={styles.slider}
      />

      {/* Real-time Math Feedback */}
      <div style={styles.mathFeedback}>
        <span>Base Calories: {baseNutrition?.calories || 0}</span>
        <span>→</span>
        <span style={{ color: "var(--primary-coral)", fontWeight: "bold" }}>
          {Math.round((baseNutrition?.calories || 0) * multiplier)} Cal
        </span>
      </div>
    </div>
  );
}

// Inline styles for the container.
// We will rely on index.css for the tricky input[type="range"] browser pseudo-selectors
const styles = {
  container: {
    marginTop: "20px",
    padding: "15px",
    borderTop: "1px solid var(--border)",
    display: "flex",
    flexDirection: "column",
    gap: "15px",
  },
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
  },
  badge: {
    width: "auto",
    height: "32px",
    padding: "0 12px",
    fontSize: "0.9rem",
    backgroundColor: "var(--primary-amber)",
  },
  slider: {
    width: "100%",
    cursor: "pointer",
  },
  mathFeedback: {
    display: "flex",
    justifyContent: "space-between",
    fontSize: "0.9rem",
    opacity: 0.8,
  },
};
