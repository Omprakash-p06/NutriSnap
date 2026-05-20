import React, { useState } from "react";
import {
  BarChart,
  Bar,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  ResponsiveContainer,
  Legend,
} from "recharts";

export const ProgressDashboard = ({ data, targetCalories }) => {
  const [activeTab, setActiveTab] = useState("calories");

  if (!Array.isArray(data) || data.length === 0) {
    return (
      <div className="glass-card" style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "320px", color: "var(--text-muted)" }}>
        No weekly data available.
      </div>
    );
  }

  // Ensure all data points have date defined
  const chartData = data.map((item) => ({
    ...item,
    date: item.date || item.day || "Day",
    calories: Math.round(item.calories || 0),
    protein: Math.round(item.protein || 0),
    carbs: Math.round(item.carbs || 0),
    fat: Math.round(item.fat || 0),
  }));

  const tabButtonStyle = (isActive) => ({
    padding: "6px 16px",
    borderRadius: "20px",
    fontSize: "0.85rem",
    fontWeight: 600,
    cursor: "pointer",
    transition: "all 0.2s ease",
    border: "none",
    background: isActive ? "rgba(16, 185, 129, 0.2)" : "transparent",
    color: isActive ? "#10b981" : "var(--text-muted)",
  });

  return (
    <div className="glass-card" style={{ width: "100%", minHeight: "380px", display: "flex", flexDirection: "column", padding: "20px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px", flexWrap: "wrap", gap: "10px" }}>
        <div>
          <h3 style={{ fontSize: "1.125rem", fontWeight: 600, color: "var(--text)", margin: 0 }}>Weekly Analytics</h3>
          <p style={{ fontSize: "0.875rem", color: "var(--text-muted)", margin: "4px 0 0 0" }}>
            {activeTab === "calories" ? "Calorie intake over the last 7 days" : "Macronutrient breakdown over the last 7 days"}
          </p>
        </div>
        
        {/* Segmented Control */}
        <div style={{ display: "flex", background: "rgba(255, 255, 255, 0.05)", padding: "4px", borderRadius: "24px" }}>
          <button
            onClick={() => setActiveTab("calories")}
            style={tabButtonStyle(activeTab === "calories")}
          >
            Calories
          </button>
          <button
            onClick={() => setActiveTab("macros")}
            style={tabButtonStyle(activeTab === "macros")}
          >
            Macronutrients
          </button>
        </div>
      </div>

      <div style={{ flex: 1, width: "100%", minHeight: "260px" }}>
        {activeTab === "calories" ? (
          <ResponsiveContainer width="100%" height={260}>
            <BarChart
              data={chartData}
              margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
            >
              <CartesianGrid
                strokeDasharray="3 3"
                vertical={false}
                stroke="rgba(255, 255, 255, 0.05)"
              />
              <XAxis
                dataKey="date"
                axisLine={false}
                tickLine={false}
                tick={{ fill: "var(--text-muted)", fontSize: 12 }}
                dy={10}
              />
              <YAxis
                axisLine={false}
                tickLine={false}
                tick={{ fill: "var(--text-muted)", fontSize: 12 }}
              />
              <Tooltip
                cursor={{ fill: "rgba(255, 255, 255, 0.02)" }}
                contentStyle={{
                  borderRadius: "12px",
                  backgroundColor: "rgba(24, 24, 27, 0.95)",
                  border: "1px solid rgba(255, 255, 255, 0.1)",
                  boxShadow: "0 10px 15px -3px rgb(0 0 0 / 0.5)",
                }}
              />
              {targetCalories && (
                <ReferenceLine
                  y={targetCalories}
                  stroke="#ef4444"
                  strokeDasharray="4 4"
                  label={{
                    position: "top",
                    value: `Goal: ${targetCalories} kcal`,
                    fill: "#ef4444",
                    fontSize: 11,
                    fontWeight: 600,
                  }}
                />
              )}
              <Bar
                dataKey="calories"
                fill="#10b981"
                radius={[6, 6, 0, 0]}
                maxBarSize={36}
                isAnimationActive={false}
              />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <ResponsiveContainer width="100%" height={260}>
            <AreaChart
              data={chartData}
              margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
            >
              <defs>
                <linearGradient id="colorProtein" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#10b981" stopOpacity={0.4}/>
                  <stop offset="95%" stopColor="#10b981" stopOpacity={0.0}/>
                </linearGradient>
                <linearGradient id="colorCarbs" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#34d399" stopOpacity={0.4}/>
                  <stop offset="95%" stopColor="#34d399" stopOpacity={0.0}/>
                </linearGradient>
                <linearGradient id="colorFat" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#6ee7b7" stopOpacity={0.4}/>
                  <stop offset="95%" stopColor="#6ee7b7" stopOpacity={0.0}/>
                </linearGradient>
              </defs>
              <CartesianGrid
                strokeDasharray="3 3"
                vertical={false}
                stroke="rgba(255, 255, 255, 0.05)"
              />
              <XAxis
                dataKey="date"
                axisLine={false}
                tickLine={false}
                tick={{ fill: "var(--text-muted)", fontSize: 12 }}
                dy={10}
              />
              <YAxis
                axisLine={false}
                tickLine={false}
                tick={{ fill: "var(--text-muted)", fontSize: 12 }}
              />
              <Tooltip
                contentStyle={{
                  borderRadius: "12px",
                  backgroundColor: "rgba(24, 24, 27, 0.95)",
                  border: "1px solid rgba(255, 255, 255, 0.1)",
                  boxShadow: "0 10px 15px -3px rgb(0 0 0 / 0.5)",
                }}
              />
              <Legend verticalAlign="top" height={36} iconType="circle" iconSize={8} wrapperStyle={{ fontSize: "0.85rem" }} />
              <Area
                type="monotone"
                dataKey="protein"
                name="Protein"
                stroke="#10b981"
                fillOpacity={1}
                fill="url(#colorProtein)"
                strokeWidth={2}
                isAnimationActive={false}
              />
              <Area
                type="monotone"
                dataKey="carbs"
                name="Carbs"
                stroke="#34d399"
                fillOpacity={1}
                fill="url(#colorCarbs)"
                strokeWidth={2}
                isAnimationActive={false}
              />
              <Area
                type="monotone"
                dataKey="fat"
                name="Fat"
                stroke="#6ee7b7"
                fillOpacity={1}
                fill="url(#colorFat)"
                strokeWidth={2}
                isAnimationActive={false}
              />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
};
