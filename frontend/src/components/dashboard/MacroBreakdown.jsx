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
      <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 flex flex-col items-center justify-center h-64">
        <p className="text-gray-500">No macro data for today yet.</p>
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
      <ul className="flex flex-col gap-2 pt-4">
        {payload.map((entry, index) => {
          const pct = Math.round((entry.payload.value / total) * 100);
          return (
            <li
              key={`item-${index}`}
              className="flex items-center justify-between text-sm"
            >
              <div className="flex items-center gap-2">
                <span
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: entry.color }}
                />
                <span className="text-gray-600 font-medium">{entry.value}</span>
              </div>
              <div className="flex gap-3 text-right">
                <span className="font-semibold text-gray-900">
                  {entry.payload.value}g
                </span>
                <span className="text-gray-400 w-8">{pct}%</span>
              </div>
            </li>
          );
        })}
      </ul>
    );
  };

  return (
    <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 w-full">
      <div className="mb-2">
        <h3 className="text-lg font-semibold text-gray-900">Today's Macros</h3>
        <p className="text-sm text-gray-500">Macronutrient distribution</p>
      </div>

      <div className="h-48 w-full relative">
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
