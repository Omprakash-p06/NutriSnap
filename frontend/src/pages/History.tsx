import React, { useState, useEffect } from 'react';
import Card from '../components/common/Card';
import Loader from '../components/common/Loader';
import MealHistory from '../components/dashboard/MealHistory';
import { getMeals, deleteMeal } from '../api/meals';
import type { Meal } from '../api/meals';

const History: React.FC = () => {
    const [meals, setMeals] = useState<Meal[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        loadMeals();
    }, []);

    const loadMeals = async () => {
        try {
            setLoading(true);
            const data = await getMeals({ limit: 50 });
            setMeals(data);
        } catch (err) {
            setError('Failed to load meal history');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const handleDeleteMeal = async (mealId: number) => {
        if (!confirm('Delete this meal?')) return;

        try {
            await deleteMeal(mealId);
            setMeals(meals.filter((m) => m.id !== mealId));
        } catch (err) {
            setError('Failed to delete meal');
            alert('Failed to delete meal');
        }
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-[60vh]">
                <Loader size="lg" />
            </div>
        );
    }

    // Group meals by date
    const groupedMeals = meals.reduce((groups, meal) => {
        const date = new Date(meal.logged_at).toLocaleDateString('en-US', {
            weekday: 'long',
            month: 'short',
            day: 'numeric',
        });
        if (!groups[date]) groups[date] = [];
        groups[date].push(meal);
        return groups;
    }, {} as Record<string, Meal[]>);

    return (
        <div className="max-w-2xl mx-auto space-y-6 pb-20 md:pb-0">
            {/* Header */}
            <div className="text-center">
                <h1 className="text-3xl font-bold text-white mb-2">Meal History</h1>
                <p className="text-gray-400">
                    {meals.length} meals logged
                </p>
            </div>

            {error && (
                <div className="bg-red-500/10 border border-red-500/20 text-red-400 p-4 rounded-xl text-center">
                    {error}
                </div>
            )}

            {/* Grouped by date */}
            {Object.entries(groupedMeals).map(([date, dateMeals]) => (
                <div key={date}>
                    <h3 className="text-sm font-medium text-gray-400 mb-3 ml-1">{date}</h3>
                    <Card>
                        <MealHistory
                            meals={dateMeals}
                            limit={dateMeals.length}
                            onMealClick={(id) => handleDeleteMeal(id)}
                        />
                    </Card>
                </div>
            ))}

            {meals.length === 0 && (
                <Card className="text-center py-12">
                    <div className="bg-gray-700/30 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                        <span className="text-3xl">📅</span>
                    </div>
                    <p className="text-gray-400 text-lg">No meals logged yet</p>
                    <p className="text-gray-500 mt-2">
                        Start by scanning your first meal!
                    </p>
                </Card>
            )}
        </div>
    );
};

export default History;
