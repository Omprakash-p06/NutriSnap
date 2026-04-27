import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';

export function useMealHistory() {
  const [meals, setMeals] = useState([]);
  const { currentUser: user } = useAuth();

  // Fetch strictly from Cloud DB instead of local browser memory!
  useEffect(() => {
    if (!user || !user.email) return;

    fetch(`/api/meals?email=${encodeURIComponent(user.email)}`)
      .then(res => res.json())
      .then(data => {
        if (!data.error) setMeals(data);
      })
      .catch(e => console.error('Failed to sync cloud meals', e));
  }, [user]);

  const addMeal = async (mealObj, multiplier = 1.0) => {
    if (!user) return; // Prevent logging if not signed in digitally

    const newMealPayload = {
      userEmail: user.email,
      title: mealObj.title || 'Unknown Meal',
      calories: Math.round(mealObj.calories * multiplier),
      protein: Math.round((mealObj.protein || 0) * multiplier),
      carbs: Math.round((mealObj.carbs || 0) * multiplier),
      fat: Math.round((mealObj.fat || 0) * multiplier),
      category: mealObj.category || 'Snacks',
      multiplier: multiplier,
      timestamp: new Date()
    };

    // Store Optimistically on Client
    const optimisticMeal = { _id: Date.now().toString(), ...newMealPayload };
    setMeals(prev => [optimisticMeal, ...prev]);

    // Push into MongoDB
    try {
      const response = await fetch('/api/meals', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(newMealPayload)
      });
      const savedDbRecord = await response.json();
      
      // Upgrade local record with true MongoDB _id quietly
      setMeals(prev => prev.map(m => m._id === optimisticMeal._id ? savedDbRecord : m));
    } catch(err) {
      console.error("Cloud push failed:", err);
      // Rollback optimistic save
      setMeals(prev => prev.filter(m => m._id !== optimisticMeal._id));
    }
  };

  const getTodayMeals = () => {
    const startOfToday = new Date();
    startOfToday.setHours(0, 0, 0, 0);
    
    // Parse MongoDB timestamp strings safely
    return meals.filter(meal => new Date(meal.timestamp).getTime() >= startOfToday.getTime());
  };

  const getTodayCalories = () => {
    return getTodayMeals().reduce((sum, meal) => sum + meal.calories, 0);
  };

  const getTodayMacros = () => {
    return getTodayMeals().reduce((acc, meal) => {
      acc.protein += meal.protein;
      acc.carbs += meal.carbs;
      acc.fat += meal.fat;
      return acc;
    }, { protein: 0, carbs: 0, fat: 0 });
  };

  const deleteMeal = async (mealId) => {
    // Determine target _id vs optimistic local id routing
    setMeals(prev => prev.filter(m => m._id !== mealId && m.id !== mealId));

    try {
      await fetch(`/api/meals/${mealId}`, { method: 'DELETE' });
    } catch(err) {
      console.error("Delete sync failed", err);
    }
  };

  return {
    allMeals: meals,
    todayMeals: getTodayMeals(),
    todayCalories: getTodayCalories(),
    todayMacros: getTodayMacros(),
    addMeal,
    deleteMeal
  };
}
