import React from 'react';

interface CalorieGaugeProps {
    consumed: number;
    target: number;
}

const CalorieGauge: React.FC<CalorieGaugeProps> = ({ consumed, target }) => {
    const percentage = Math.min((consumed / target) * 100, 100);
    const remaining = Math.max(target - consumed, 0);

    // Determine color based on percentage
    const getColor = () => {
        if (percentage < 50) return 'text-emerald-400';
        if (percentage < 80) return 'text-amber-400';
        return 'text-red-400';
    };

    const getStrokeColor = () => {
        if (percentage < 50) return '#34d399'; // emerald-400
        if (percentage < 80) return '#fbbf24'; // amber-400
        return '#f87171'; // red-400
    };

    return (
        <div className="flex flex-col items-center">
            {/* Circular Progress */}
            <div className="relative w-40 h-40">
                <svg className="w-full h-full transform -rotate-90">
                    {/* Background circle */}
                    <circle
                        cx="80"
                        cy="80"
                        r="70"
                        stroke="currentColor"
                        strokeWidth="12"
                        fill="none"
                        className="text-gray-700"
                    />
                    {/* Progress circle */}
                    <circle
                        cx="80"
                        cy="80"
                        r="70"
                        stroke={getStrokeColor()}
                        strokeWidth="12"
                        fill="none"
                        strokeLinecap="round"
                        strokeDasharray={`${percentage * 4.4} 440`}
                        className="transition-all duration-500 ease-out"
                    />
                </svg>

                {/* Center text */}
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                    <span className={`text-3xl font-bold ${getColor()}`}>
                        {Math.round(consumed)}
                    </span>
                    <span className="text-sm text-gray-400">kcal</span>
                </div>
            </div>

            {/* Stats */}
            <div className="mt-4 grid grid-cols-2 gap-4 w-full">
                <div className="text-center">
                    <p className="text-sm text-gray-400">Target</p>
                    <p className="text-lg font-semibold text-white">{target}</p>
                </div>
                <div className="text-center">
                    <p className="text-sm text-gray-400">Remaining</p>
                    <p className="text-lg font-semibold text-emerald-400">{remaining}</p>
                </div>
            </div>
        </div>
    );
};

export default CalorieGauge;
