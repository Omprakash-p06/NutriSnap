import React from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  ResponsiveContainer,
} from "recharts";

export const ProgressDashboard = ({ data, targetCalories }) => {
  if (!Array.isArray(data) || data.length === 0) {
    return (
      <div className="glass-card" style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "256px", color: "var(--text-muted)" }}>
        No weekly data available.
      </div>
    );
  }

  return (
    <div className="glass-card" style={{ width: "100%", height: "320px", display: "flex", flexDirection: "column" }}>
      <div style={{ marginBottom: "16px" }}>
        <h3 style={{ fontSize: "1.125rem", fontWeight: 600, color: "var(--text)", margin: 0 }}>Weekly Progress</h3>
        <p style={{ fontSize: "0.875rem", color: "var(--text-muted)", margin: "4px 0 0 0" }}>
          Calorie intake over the last 7 days
        </p>
      </div>

      <div style={{ flex: 1, width: "100%", minHeight: 0 }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={data}
            margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
          >
            <CartesianGrid
              strokeDasharray="3 3"
              vertical={false}
              stroke="#f3f4f6"
            />
            <XAxis
              dataKey="date"
              axisLine={false}
              tickLine={false}
              tick={{ fill: "#6b7280", fontSize: 12 }}
              dy={10}
            />
            <YAxis
              axisLine={false}
              tickLine={false}
              tick={{ fill: "#6b7280", fontSize: 12 }}
            />
            <Tooltip
              cursor={{ fill: "#f9fafb" }}
              contentStyle={{
                borderRadius: "8px",
                border: "none",
                boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1)",
              }}
            />
            {targetCalories && (
              <ReferenceLine
                y={targetCalories}
                stroke="#6366f1"
                strokeDasharray="3 3"
                label={{
                  position: "top",
                  value: "Target",
                  fill: "#6366f1",
                  fontSize: 12,
                }}
              />
            )}
            <Bar
              dataKey="calories"
              fill="#10b981"
              radius={[4, 4, 0, 0]}
              maxBarSize={40}
              isAnimationActive={false}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
