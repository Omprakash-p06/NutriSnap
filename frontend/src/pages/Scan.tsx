import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import CameraCapture from '../components/food/CameraCapture';
import FoodResults from '../components/food/FoodResults';
import Loader from '../components/common/Loader';
import { analyzeFood } from '../api/food';
import type { AnalysisResponse } from '../api/food';
import { createMeal } from '../api/meals';
import type { CreateMealRequest } from '../api/meals';

const Scan: React.FC = () => {
    const navigate = useNavigate();
    const [step, setStep] = useState<'capture' | 'analyzing' | 'results'>('capture');
    const [results, setResults] = useState<AnalysisResponse | null>(null);
    const [saved, setSaved] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleCapture = async (file: File | string) => {
        let imageFile: File;

        if (typeof file === 'string') {
            // Convert base64 to File
            const res = await fetch(file);
            const blob = await res.blob();
            imageFile = new File([blob], 'capture.jpg', { type: 'image/jpeg' });
        } else {
            imageFile = file;
        }

        analyzeImage(imageFile);
    };

    const analyzeImage = async (file: File) => {
        try {
            setStep('analyzing');
            setError(null);
            const data = await analyzeFood(file);

            if (data.success) {
                setResults(data);
                setStep('results');
            } else {
                setError('Failed to analyze food. Please try again.');
                setStep('capture');
            }
        } catch (err) {
            console.error(err);
            setError('Server error during analysis.');
            setStep('capture');
        }
    };

    const handleSaveMeal = async (finalResults: AnalysisResponse) => {
        try {
            const mealData: CreateMealRequest = {
                total_calories: finalResults.total_nutrition.calories,
                total_protein: finalResults.total_nutrition.protein,
                total_carbs: finalResults.total_nutrition.carbs,
                total_fats: finalResults.total_nutrition.fats,
                food_items: finalResults.detected_foods.map((food) => ({
                    food_class: food.food_class,
                    confidence: food.confidence,
                    ai_portion_grams: food.estimated_grams,
                    user_portion_grams: food.adjusted_grams || food.estimated_grams,
                    calories: food.nutrition.calories,
                    protein: food.nutrition.protein,
                    carbs: food.nutrition.carbs,
                    fats: food.nutrition.fats,
                })),
            };

            await createMeal(mealData);
            setSaved(true);

            // Redirect to history after short delay
            setTimeout(() => {
                navigate('/history');
            }, 1500);
        } catch (err) {
            console.error(err);
            alert('Failed to save meal');
        }
    };

    const handleReset = () => {
        setStep('capture');
        setResults(null);
        setSaved(false);
        setError(null);
    };

    return (
        <div className="max-w-xl mx-auto space-y-6 pb-20 md:pb-0">
            {/* Header */}
            <div className="text-center">
                <h1 className="text-3xl font-bold text-white mb-2">Scan Food</h1>
                <p className="text-gray-400">
                    {step === 'capture' && 'Take a photo or upload an image'}
                    {step === 'analyzing' && 'Analyzing your food...'}
                    {step === 'results' && 'Review and save your meal'}
                </p>
            </div>

            {error && (
                <div className="bg-red-500/10 border border-red-500/20 text-red-400 p-4 rounded-xl text-center">
                    {error}
                </div>
            )}

            {step === 'capture' && (
                <div className="fade-in">
                    <CameraCapture onCapture={handleCapture} />
                </div>
            )}

            {step === 'analyzing' && (
                <div className="flex flex-col items-center justify-center py-12 fade-in">
                    <Loader size="lg" />
                    <p className="mt-4 text-gray-400 animate-pulse">
                        Identifying food items...
                    </p>
                </div>
            )}

            {step === 'results' && results && (
                <div className="fade-in">
                    <FoodResults
                        results={results}
                        onSave={handleSaveMeal}
                        onReset={handleReset}
                        saved={saved}
                    />
                </div>
            )}
        </div>
    );
};

export default Scan;
