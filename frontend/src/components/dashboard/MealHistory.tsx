import React from 'react';
import { formatDate, formatCalories } from '../../utils/formatters';
import type { Meal } from '../../api/meals';

interface MealHistoryProps {
    meals?: Meal[];
    limit?: number;
    onMealClick?: (mealId: number) => void;
}

const MealHistory: React.FC<MealHistoryProps> = ({ meals = [], limit = 5, onMealClick }) => {
    const displayMeals = meals.slice(0, limit);

    if (displayMeals.length === 0) {
        return (
            <div className="text-center py-8">
                <p className="text-gray-400">No meals logged yet</p>
                <p className="text-sm text-gray-500">Scan your first meal to get started!</p>
            </div>
        );
    }

    return (
        <div className="space-y-3">
            {displayMeals.map((meal) => (
                <div
                    key={meal.id}
                    className="flex items-center justify-between p-4 bg-white/5 rounded-xl hover:bg-white/10 transition-colors cursor-pointer"
                    onClick={() => onMealClick?.(meal.id)}
                >
                    <div className="flex items-center space-x-4">
                        {/* Meal icon */}
                        <div className="w-12 h-12 bg-emerald-500/20 rounded-lg flex items-center justify-center">
                            <span className="text-2xl">🍽️</span>
                        </div>

                        {/* Meal info */}
                        <div>
                            <p className="font-medium text-white">
                                {meal.food_items?.length || 0} items
                            </p>
                            <p className="text-sm text-gray-400">
                                {formatDate(meal.logged_at)}
                            </p>
                        </div>
                    </div>

                    {/* Calories */}
                    <div className="text-right">
                        <p className="text-lg font-bold text-emerald-400">
                            {formatCalories(meal.total_calories)}
                        </p>
                        <p className="text-xs text-gray-500">kcal</p>
                    </div>
                </div>
            ))}
        </div>
    );
};

export default MealHistory;
