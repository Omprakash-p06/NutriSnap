import React, { useState } from 'react';
import Card from '../common/Card';
import Button from '../common/Button';
import PortionSlider from './PortionSlider';
import type { AnalysisResponse, NutritionInfo } from '../../api/food';

interface FoodResultsProps {
    results: AnalysisResponse;
    onSave: (adjustedResults: AnalysisResponse) => void;
    onReset: () => void;
    saved: boolean;
}

const FoodResults: React.FC<FoodResultsProps> = ({ results, onSave, onReset, saved }) => {
    // Initialize adjusted results with estimated values
    const [adjustedResults, setAdjustedResults] = useState<AnalysisResponse>(() => ({
        ...results,
        detected_foods: results.detected_foods.map((food) => ({
            ...food,
            adjusted_grams: food.estimated_grams,
        })),
    }));

    const handlePortionChange = (index: number, newGrams: number) => {
        const updated = { ...adjustedResults };
        const food = updated.detected_foods[index];
        const originalFood = results.detected_foods[index];

        if (!originalFood.nutrition) return;

        // Calculate new nutrition based on adjusted portion
        // Using original estimation as baseline for ratio
        const ratio = newGrams / originalFood.estimated_grams;

        food.adjusted_grams = newGrams;
        food.nutrition = {
            calories: Math.round(originalFood.nutrition.calories * ratio),
            protein: Math.round(originalFood.nutrition.protein * ratio * 10) / 10,
            carbs: Math.round(originalFood.nutrition.carbs * ratio * 10) / 10,
            fats: Math.round(originalFood.nutrition.fats * ratio * 10) / 10,
        };

        // Recalculate totals
        updated.total_nutrition = updated.detected_foods.reduce(
            (acc, f) => ({
                calories: acc.calories + (f.nutrition?.calories || 0),
                protein: acc.protein + (f.nutrition?.protein || 0),
                carbs: acc.carbs + (f.nutrition?.carbs || 0),
                fats: acc.fats + (f.nutrition?.fats || 0),
            }),
            { calories: 0, protein: 0, carbs: 0, fats: 0 } as NutritionInfo
        );

        setAdjustedResults(updated);
    };

    if (!results.detected_foods?.length) {
        return (
            <Card className="text-center py-8">
                <p className="text-gray-400">No food items detected</p>
                <Button onClick={onReset} className="mt-4">
                    Try Again
                </Button>
            </Card>
        );
    }

    return (
        <div className="space-y-6">
            {/* Detected Foods */}
            <Card>
                <Card.Header>
                    <Card.Title>🍽️ Detected Foods</Card.Title>
                </Card.Header>
                <Card.Content className="space-y-4">
                    {adjustedResults.detected_foods.map((food, index) => (
                        <div
                            key={index}
                            className="p-4 bg-white/5 rounded-xl space-y-3 border border-white/5"
                        >
                            <div className="flex justify-between items-center">
                                <div>
                                    <h4 className="font-medium text-white capitalize text-lg">
                                        {food.food_class}
                                    </h4>
                                    <p className="text-sm text-gray-400">
                                        Confidence: {Math.round(food.confidence * 100)}%
                                    </p>
                                </div>
                                <div className="text-right">
                                    <p className="text-lg font-bold text-emerald-400">
                                        {food.nutrition?.calories} kcal
                                    </p>
                                </div>
                            </div>

                            <PortionSlider
                                value={food.adjusted_grams || food.estimated_grams}
                                min={10}
                                max={Math.max(food.estimated_grams * 3, 500)}
                                defaultValue={food.estimated_grams}
                                onChange={(val) => handlePortionChange(index, val)}
                            />

                            {/* Macros */}
                            <div className="flex space-x-4 text-sm mt-2 pt-2 border-t border-white/5">
                                <span className="text-emerald-400 font-medium">
                                    Protein: {food.nutrition?.protein}g
                                </span>
                                <span className="text-amber-400 font-medium">
                                    Carbs: {food.nutrition?.carbs}g
                                </span>
                                <span className="text-red-400 font-medium">
                                    Fats: {food.nutrition?.fats}g
                                </span>
                            </div>
                        </div>
                    ))}
                </Card.Content>
            </Card>

            {/* Total Nutrition */}
            <Card className="bg-gradient-to-br from-gray-800 to-gray-900 border-emerald-500/20">
                <Card.Header>
                    <Card.Title>📊 Total Nutrition</Card.Title>
                </Card.Header>
                <Card.Content>
                    <div className="grid grid-cols-4 gap-4 text-center">
                        <div>
                            <p className="text-2xl font-bold text-white">
                                {Math.round(adjustedResults.total_nutrition.calories)}
                            </p>
                            <p className="text-xs text-gray-400 uppercase tracking-wider">Calories</p>
                        </div>
                        <div>
                            <p className="text-2xl font-bold text-emerald-400">
                                {Math.round(adjustedResults.total_nutrition.protein)}g
                            </p>
                            <p className="text-xs text-gray-400 uppercase tracking-wider">Protein</p>
                        </div>
                        <div>
                            <p className="text-2xl font-bold text-amber-400">
                                {Math.round(adjustedResults.total_nutrition.carbs)}g
                            </p>
                            <p className="text-xs text-gray-400 uppercase tracking-wider">Carbs</p>
                        </div>
                        <div>
                            <p className="text-2xl font-bold text-red-400">
                                {Math.round(adjustedResults.total_nutrition.fats)}g
                            </p>
                            <p className="text-xs text-gray-400 uppercase tracking-wider">Fats</p>
                        </div>
                    </div>
                </Card.Content>
            </Card>

            {/* Actions */}
            <div className="flex space-x-4">
                {saved ? (
                    <div className="flex-1 text-center py-3 bg-emerald-500/20 border border-emerald-500/30 rounded-xl">
                        <span className="text-emerald-400 font-medium">✅ Meal Saved!</span>
                    </div>
                ) : (
                    <Button onClick={() => onSave(adjustedResults)} className="flex-1">
                        💾 Save Meal
                    </Button>
                )}
                <Button onClick={onReset} variant="outline">
                    ↩️ Scan Another
                </Button>
            </div>
        </div>
    );
};

export default FoodResults;
