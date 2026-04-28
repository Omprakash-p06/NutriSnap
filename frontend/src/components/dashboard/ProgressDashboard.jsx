import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  ResponsiveContainer
} from 'recharts';

export const ProgressDashboard = ({ data, targetCalories }) => {
  if (!data || data.length === 0) {
    return (
      <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 flex items-center justify-center h-64 text-gray-500">
        No weekly data available.
      </div>
    );
  }

  return (
    <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 w-full h-80">
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-gray-900">Weekly Progress</h3>
        <p className="text-sm text-gray-500">Calorie intake over the last 7 days</p>
      </div>
      
      <div className="h-56 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={data}
            margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
          >
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f3f4f6" />
            <XAxis 
              dataKey="date" 
              axisLine={false}
              tickLine={false}
              tick={{ fill: '#6b7280', fontSize: 12 }}
              dy={10}
            />
            <YAxis 
              axisLine={false}
              tickLine={false}
              tick={{ fill: '#6b7280', fontSize: 12 }}
            />
            <Tooltip 
              cursor={{ fill: '#f9fafb' }}
              contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
            />
            {targetCalories && (
              <ReferenceLine 
                y={targetCalories} 
                stroke="#6366f1" 
                strokeDasharray="3 3" 
                label={{ position: 'top', value: 'Target', fill: '#6366f1', fontSize: 12 }}
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
