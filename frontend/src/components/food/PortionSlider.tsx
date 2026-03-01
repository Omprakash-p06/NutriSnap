import React from 'react';

interface PortionSliderProps {
    value: number;
    min?: number;
    max?: number;
    defaultValue?: number;
    onChange: (value: number) => void;
}

const PortionSlider: React.FC<PortionSliderProps> = ({
    value,
    min = 10,
    max = 500,
    defaultValue,
    onChange,
}) => {
    const percentage = ((value - min) / (max - min)) * 100;

    return (
        <div className="space-y-2">
            <div className="flex justify-between text-sm">
                <span className="text-gray-400">Portion Size</span>
                <span className="font-medium text-white">{Math.round(value)}g</span>
            </div>

            <div className="relative">
                <input
                    type="range"
                    min={min}
                    max={max}
                    value={value}
                    onChange={(e) => onChange(parseInt(e.target.value))}
                    className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer
                     [&::-webkit-slider-thumb]:appearance-none
                     [&::-webkit-slider-thumb]:w-4
                     [&::-webkit-slider-thumb]:h-4
                     [&::-webkit-slider-thumb]:rounded-full
                     [&::-webkit-slider-thumb]:bg-emerald-500
                     [&::-webkit-slider-thumb]:cursor-pointer
                     [&::-webkit-slider-thumb]:shadow-lg
                     [&::-webkit-slider-thumb]:shadow-emerald-500/50"
                    style={{
                        background: `linear-gradient(to right, #22c55e ${percentage}%, #374151 ${percentage}%)`,
                    }}
                />
            </div>

            {/* Default indicator */}
            {defaultValue && (
                <div className="text-xs text-gray-500 text-center">
                    AI estimated: {Math.round(defaultValue)}g
                </div>
            )}
        </div>
    );
};

export default PortionSlider;
