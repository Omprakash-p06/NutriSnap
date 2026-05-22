import React from "react";
import { motion } from "framer-motion";

export const RecipeCard = ({ recipe }) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-card"
      style={{
        padding: 0,
        overflow: "hidden",
        display: "flex",
        flexDirection: "column",
        height: "100%",
        cursor: "pointer"
      }}
    >
      <div
        style={{
          height: "140px",
          backgroundColor: "rgba(0,0,0,0.05)",
          backgroundSize: "cover",
          backgroundPosition: "center",
          backgroundImage: recipe.image ? `url(${recipe.image})` : "none"
        }}
      />
      <div style={{ padding: "16px", flex: 1, display: "flex", flexDirection: "column" }}>
        <h4 style={{ fontWeight: 600, color: "var(--text)", margin: "0 0 8px 0", fontSize: "1.1rem" }}>
          {recipe.name}
        </h4>
        <div style={{ display: "flex", flexWrap: "wrap", gap: "6px", marginBottom: "16px" }}>
          {recipe.tags &&
            recipe.tags.slice(0, 2).map((tag) => (
              <span
                key={tag}
                style={{
                  padding: "4px 10px",
                  backgroundColor: "rgba(99, 102, 241, 0.1)",
                  color: "#6366f1",
                  fontSize: "0.75rem",
                  borderRadius: "20px",
                  fontWeight: 600
                }}
              >
                {tag}
              </span>
            ))}
        </div>
        <div style={{
          marginTop: "auto",
          paddingTop: "16px",
          borderTop: "1px solid var(--border)",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-end"
        }}>
          <div>
            <p style={{ fontSize: "0.75rem", color: "var(--text-muted)", textTransform: "uppercase", margin: "0 0 4px 0", letterSpacing: "0.05em" }}>
              Calories
            </p>
            <p style={{ fontWeight: 600, color: "var(--text)", margin: 0 }}>{recipe.calories} kcal</p>
          </div>
          <div style={{ textAlign: "right" }}>
            <p style={{ fontSize: "0.75rem", color: "var(--text-muted)", textTransform: "uppercase", margin: "0 0 4px 0", letterSpacing: "0.05em" }}>
              Protein
            </p>
            <p style={{ fontWeight: 600, color: "var(--accent-mint)", margin: 0 }}>{recipe.protein}g</p>
          </div>
        </div>
      </div>
    </motion.div>
  );
};
