import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Camera } from 'lucide-react';
import Card from '../components/common/Card';
import Button from '../components/common/Button';
import Loader from '../components/common/Loader';
import CalorieGauge from '../components/dashboard/CalorieGauge';
import MacroChart from '../components/dashboard/MacroChart';
import MealHistory from '../components/dashboard/MealHistory';
import { getDashboardStats, getMeals } from '../api/meals';
import type { DashboardStats, Meal } from '../api/meals';

const Home: React.FC = () => {
    const [stats, setStats] = useState<DashboardStats | null>(null);
    const [recentMeals, setRecentMeals] = useState<Meal[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        loadDashboardData();
    }, []);

    const loadDashboardData = async () => {
        try {
            setLoading(true);
            const [statsData, meals] = await Promise.all([
                getDashboardStats(),
                getMeals({ limit: 5 }),
            ]);
            setStats(statsData);
            setRecentMeals(meals);
        } catch (err) {
            setError('Failed to load dashboard data');
            console.error(err);
            // Mock data for demo if backend fails or empty
            setStats({
                calories_consumed: 0,
                calories_target: 2000,
                calories_remaining: 2000,
                protein: 0,
                carbs: 0,
                fats: 0,
                meal_count: 0,
            });
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-[60vh]">
                <Loader size="lg" />
            </div>
        );
    }

    return (
        <div className="space-y-8 pb-20 md:pb-0">
            {/* Header */}
            <div className="text-center space-y-2">
                <h1 className="text-4xl font-bold bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">
                    Welcome to NutriSnap
                </h1>
                <p className="text-gray-400">
                    Track your nutrition with AI-powered food detection
                </p>
                {error && (
                    <p className="text-red-400 text-sm mt-2">{error}</p>
                )}
            </div>

            {/* Quick Action */}
            <div className="flex justify-center">
                <Link to="/scan">
                    <Button size="lg" className="shadow-emerald-500/20 shadow-lg hover:shadow-emerald-500/40 transform hover:-translate-y-1 transition-all">
                        <Camera className="mr-2" />
                        Scan Food
                    </Button>
                </Link>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Calorie Gauge */}
                <Card>
                    <Card.Header>
                        <Card.Title>Today's Calories</Card.Title>
                    </Card.Header>
                    <Card.Content>
                        <CalorieGauge
                            consumed={stats?.calories_consumed || 0}
                            target={stats?.calories_target || 2000}
                        />
                    </Card.Content>
                </Card>

                {/* Macro Chart */}
                <Card>
                    <Card.Header>
                        <Card.Title>Macros Breakdown</Card.Title>
                    </Card.Header>
                    <Card.Content>
                        <MacroChart
                            protein={stats?.protein || 0}
                            carbs={stats?.carbs || 0}
                            fats={stats?.fats || 0}
                        />
                    </Card.Content>
                </Card>

                {/* Quick Stats */}
                <Card>
                    <Card.Header>
                        <Card.Title>Today's Summary</Card.Title>
                    </Card.Header>
                    <Card.Content className="space-y-6">
                        <div className="flex justify-between items-center p-3 bg-white/5 rounded-xl">
                            <span className="text-gray-400">Meals Logged</span>
                            <span className="text-2xl font-bold text-emerald-400">
                                {stats?.meal_count || 0}
                            </span>
                        </div>
                        <div className="flex justify-between items-center p-3 bg-white/5 rounded-xl">
                            <span className="text-gray-400">Calories Remaining</span>
                            <span className="text-2xl font-bold text-amber-400">
                                {stats?.calories_remaining || 0}
                            </span>
                        </div>
                        <div className="flex justify-between items-center p-3 bg-white/5 rounded-xl">
                            <span className="text-gray-400">Progress</span>
                            <span className="text-lg font-medium text-white">
                                {Math.round((stats?.calories_consumed! / stats?.calories_target!) * 100 || 0)}%
                            </span>
                        </div>
                    </Card.Content>
                </Card>
            </div>

            {/* Recent Meals */}
            <Card>
                <Card.Header className="flex justify-between items-center">
                    <Card.Title>Recent Meals</Card.Title>
                    <Link to="/history" className="text-emerald-400 hover:text-emerald-300 text-sm font-medium">
                        View All →
                    </Link>
                </Card.Header>
                <Card.Content>
                    <MealHistory meals={recentMeals} limit={3} />
                </Card.Content>
            </Card>
        </div>
    );
};

export default Home;
