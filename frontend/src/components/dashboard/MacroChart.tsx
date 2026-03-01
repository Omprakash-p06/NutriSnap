import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';

interface MacroChartProps {
    protein: number;
    carbs: number;
    fats: number;
}

const COLORS = {
    protein: '#34d399',  // emerald-400
    carbs: '#fbbf24',    // amber-400
    fats: '#f87171',     // red-400
};

const MacroChart: React.FC<MacroChartProps> = ({ protein, carbs, fats }) => {
    const total = protein + carbs + fats;

    const data = [
        { name: 'Protein', value: protein, color: COLORS.protein },
        { name: 'Carbs', value: carbs, color: COLORS.carbs },
        { name: 'Fats', value: fats, color: COLORS.fats },
    ];

    if (total === 0) {
        return (
            <div className="flex flex-col items-center justify-center h-48">
                <p className="text-gray-400">No data yet</p>
                <p className="text-sm text-gray-500">Scan a meal to see macros</p>
            </div>
        );
    }

    return (
        <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                    <Pie
                        data={data}
                        cx="50%"
                        cy="50%"
                        innerRadius={40}
                        outerRadius={60}
                        paddingAngle={5}
                        dataKey="value"
                    >
                        {data.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                    </Pie>
                    <Tooltip
                        contentStyle={{
                            backgroundColor: 'rgba(31, 41, 55, 0.9)',
                            border: '1px solid rgba(255, 255, 255, 0.1)',
                            borderRadius: '8px',
                            color: 'white',
                        }}
                        formatter={(value: number | undefined) => [value ? `${value}g` : '', ''] as [string, string]}
                    />
                    <Legend
                        verticalAlign="bottom"
                        height={36}
                        formatter={(value) => (
                            <span className="text-gray-300 text-sm">{value}</span>
                        )}
                    />
                </PieChart>
            </ResponsiveContainer>

            {/* Macro values */}
            <div className="flex justify-around mt-2">
                <div className="text-center">
                    <span className="text-emerald-400 font-bold">{protein}g</span>
                    <p className="text-xs text-gray-500">Protein</p>
                </div>
                <div className="text-center">
                    <span className="text-amber-400 font-bold">{carbs}g</span>
                    <p className="text-xs text-gray-500">Carbs</p>
                </div>
                <div className="text-center">
                    <span className="text-red-400 font-bold">{fats}g</span>
                    <p className="text-xs text-gray-500">Fats</p>
                </div>
            </div>
        </div>
    );
};

export default MacroChart;
