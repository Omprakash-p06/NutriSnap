import React, { useState, useEffect } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip,
  ResponsiveContainer, Cell
} from 'recharts';
import { useAuth } from '../context/AuthContext';

export default function WeeklyChart() {
  const { currentUser, userSettings } = useAuth();
  const [weekData, setWeekData] = useState([]);

  useEffect(() => {
    if (!currentUser?.email) return;
    fetch(`/api/meals/weekly?email=${encodeURIComponent(currentUser.email)}`)
      .then(res => res.json())
      .then(data => {
        if (!data.error) setWeekData(data);
      })
      .catch(err => console.error('Weekly chart fetch error:', err));
  }, [currentUser]);

  const goal = userSettings?.dailyCalorieGoal || 2000;

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      const kcal = payload[0].value;
      const pct = Math.round((kcal / goal) * 100);
      return (
        <div style={tooltipStyle}>
          <p style={{ margin: 0, fontWeight: '700' }}>{label}</p>
          <p style={{ margin: '4px 0 0', color: 'var(--primary-coral)' }}>{kcal} kcal</p>
          <p style={{ margin: '2px 0 0', fontSize: '0.75rem', opacity: 0.7 }}>{pct}% of goal</p>
        </div>
      );
    }
    return null;
  };

  if (weekData.every(d => d.calories === 0)) return null; // Hide if no data yet

  return (
    <div style={chartContainer}>
      <h3 style={{ margin: '0 0 16px 0', opacity: 0.85, fontSize: '1rem' }}>7-Day Calories</h3>
      <ResponsiveContainer width="100%" height={120}>
        <BarChart data={weekData} barSize={22}>
          <XAxis
            dataKey="day"
            stroke="var(--text-muted)"
            tick={{ fontSize: 11 }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis hide />
          <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,107,90,0.06)' }} />
          <Bar dataKey="calories" radius={[6, 6, 0, 0]}>
            {weekData.map((entry, index) => (
              <Cell
                key={index}
                fill={entry.calories >= goal
                  ? '#FF6B5A'
                  : 'url(#barGrad)'}
              />
            ))}
          </Bar>
          <defs>
            <linearGradient id="barGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#FFB347" />
              <stop offset="100%" stopColor="#FF6B5A" stopOpacity={0.6} />
            </linearGradient>
          </defs>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

const chartContainer = {
  width: '100%',
  padding: '16px 0 0',
  borderTop: '1px solid var(--border)',
  marginTop: '16px'
};

const tooltipStyle = {
  background: 'var(--glass-bg)',
  border: '1px solid var(--glass-border)',
  borderRadius: '10px',
  padding: '10px 14px',
  fontSize: '0.85rem',
  backdropFilter: 'blur(8px)',
  boxShadow: '0 4px 12px rgba(0,0,0,0.1)'
};
