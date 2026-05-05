import React from "react";
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
  Legend,
} from "recharts";

const COLORS = {
  Protein: "#10b981", // Emerald 500
  Carbs: "#34d399", // Emerald 400
  Fat: "#6ee7b7", // Emerald 300
};

export const MacroBreakdown = ({ macros }) => {
  if (
    !macros ||
    (macros.protein === 0 && macros.carbs === 0 && macros.fat === 0)
  ) {
    return (
      <div className="glass-card" style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", height: "256px" }}>
        <p style={{ color: "var(--text-muted)", margin: 0 }}>No macro data for today yet.</p>
      </div>
    );
  }

  const data = [
    { name: "Protein", value: macros.protein },
    { name: "Carbs", value: macros.carbs },
    { name: "Fat", value: macros.fat },
  ];

  const total = macros.protein + macros.carbs + macros.fat;

  const CustomLegend = (props) => {
    const { payload } = props;
    return (
      <ul style={{ display: "flex", flexDirection: "column", gap: "8px", paddingTop: "16px", paddingLeft: 0, margin: 0, listStyle: "none" }}>
        {payload.map((entry, index) => {
          const pct = Math.round((entry.payload.value / total) * 100);
          return (
            <li
              key={`item-${index}`}
              style={{ display: "flex", alignItems: "center", justifyContent: "space-between", fontSize: "0.875rem" }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <span
                  style={{ width: "12px", height: "12px", borderRadius: "50%", backgroundColor: entry.color }}
                />
                <span style={{ color: "var(--text-muted)", fontWeight: 500 }}>{entry.value}</span>
              </div>
              <div style={{ display: "flex", gap: "12px", textAlign: "right" }}>
                <span style={{ fontWeight: 600, color: "var(--text)" }}>
                  {entry.payload.value}g
                </span>
                <span style={{ color: "var(--text-muted)", width: "32px" }}>{pct}%</span>
              </div>
            </li>
          );
        })}
      </ul>
    );
  };

  return (
    <div className="glass-card" style={{ width: "100%" }}>
      <div style={{ marginBottom: "8px" }}>
        <h3 style={{ fontSize: "1.125rem", fontWeight: 600, color: "var(--text)", margin: 0 }}>Today's Macros</h3>
        <p style={{ fontSize: "0.875rem", color: "var(--text-muted)", margin: "4px 0 0 0" }}>Macronutrient distribution</p>
      </div>

      <div style={{ height: "192px", width: "100%", position: "relative" }}>
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={50}
              outerRadius={70}
              paddingAngle={5}
              dataKey="value"
              isAnimationActive={false}
            >
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[entry.name]} />
              ))}
            </Pie>
            <Tooltip
              formatter={(value) => [`${value}g`, ""]}
              contentStyle={{
                borderRadius: "8px",
                border: "none",
                boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1)",
              }}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>

      <CustomLegend
        payload={data.map((d) => ({
          value: d.name,
          color: COLORS[d.name],
          payload: d,
        }))}
      />
    </div>
  );
};
