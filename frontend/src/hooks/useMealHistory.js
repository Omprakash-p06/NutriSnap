import { useAuth } from "../context/AuthContext";
import { useLiveQuery } from "dexie-react-hooks";
import { db } from "../services/db";
import { format } from "date-fns";

export function useMealHistory() {
  const { currentUser: user } = useAuth();
  const userId = user?.email || "guest";

  // Fetch from Dexie using live query
  const meals =
    useLiveQuery(
      () =>
        db.meals.where("userId").equals(userId).reverse().sortBy("timestamp"),
      [userId],
    ) || [];

  const addMeal = async (mealObj, multiplier = 1.0) => {
    const newMealPayload = {
      userId,
      title: mealObj.title || mealObj.name || "Unknown Meal",
      calories: Math.round(mealObj.calories * multiplier),
      protein: Math.round((mealObj.protein || 0) * multiplier),
      carbs: Math.round((mealObj.carbs || 0) * multiplier),
      fat: Math.round((mealObj.fat || 0) * multiplier),
      category: mealObj.category || "Snacks",
      multiplier: multiplier,
      timestamp: Date.now(),
    };

    // Add to meals table
    await db.meals.add(newMealPayload);

    // Update daily stats
    const dateStr = format(newMealPayload.timestamp, "yyyy-MM-dd");
    const statId = `${userId}+${dateStr}`;

    await db.transaction("rw", db.dailyStats, async () => {
      const stat = await db.dailyStats.get(statId);
      if (stat) {
        await db.dailyStats.update(statId, {
          totalCalories: stat.totalCalories + newMealPayload.calories,
          totalProtein: stat.totalProtein + newMealPayload.protein,
          totalCarbs: stat.totalCarbs + newMealPayload.carbs,
          totalFat: stat.totalFat + newMealPayload.fat,
        });
      } else {
        await db.dailyStats.add({
          id: statId, // we defined primary key as [userId+date] but we can just use composite key
          userId,
          date: dateStr,
          totalCalories: newMealPayload.calories,
          totalProtein: newMealPayload.protein,
          totalCarbs: newMealPayload.carbs,
          totalFat: newMealPayload.fat,
        });
      }
    });

    // Optionally try to sync to cloud in background
    if (user) {
      fetch("/api/meals", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...newMealPayload, userEmail: user.email }),
      }).catch((err) => console.error("Cloud push failed:", err));
    }
  };

  const getTodayMeals = () => {
    const startOfToday = new Date();
    startOfToday.setHours(0, 0, 0, 0);
    return meals.filter((meal) => meal.timestamp >= startOfToday.getTime());
  };

  const getTodayCalories = () => {
    return getTodayMeals().reduce((sum, meal) => sum + meal.calories, 0);
  };

  const getTodayMacros = () => {
    return getTodayMeals().reduce(
      (acc, meal) => {
        acc.protein += meal.protein;
        acc.carbs += meal.carbs;
        acc.fat += meal.fat;
        return acc;
      },
      { protein: 0, carbs: 0, fat: 0 },
    );
  };

  const deleteMeal = async (mealId) => {
    const meal = await db.meals.get(mealId);
    if (!meal) return;

    await db.meals.delete(mealId);

    // Update daily stats down
    const dateStr = format(meal.timestamp, "yyyy-MM-dd");
    const statId = `${userId}+${dateStr}`;

    await db.transaction("rw", db.dailyStats, async () => {
      const stat = await db.dailyStats.get(statId);
      if (stat) {
        await db.dailyStats.update(statId, {
          totalCalories: Math.max(0, stat.totalCalories - meal.calories),
          totalProtein: Math.max(0, stat.totalProtein - meal.protein),
          totalCarbs: Math.max(0, stat.totalCarbs - meal.carbs),
          totalFat: Math.max(0, stat.totalFat - meal.fat),
        });
      }
    });

    if (user) {
      fetch(`/api/meals/${mealId}`, { method: "DELETE" }).catch((e) =>
        console.error(e),
      );
    }
  };

  const calculateStreak = async () => {
    // A simple streak logic:
    // If today is logged, count back consecutive days.
    // Otherwise count back from yesterday.
    const allStats = await db.dailyStats.where("userId").equals(userId).reverse().sortBy("date");
    if (!allStats || allStats.length === 0) return 0;
    
    let currentStreak = 0;
    const today = format(new Date(), "yyyy-MM-dd");
    const yesterdayDate = new Date();
    yesterdayDate.setDate(yesterdayDate.getDate() - 1);
    const yesterday = format(yesterdayDate, "yyyy-MM-dd");

    // Start tracking from either today or yesterday
    let checkDate = new Date();
    const firstLogDate = allStats[0].date;
    
    if (firstLogDate === today) {
       checkDate = new Date();
    } else if (firstLogDate === yesterday) {
       checkDate = yesterdayDate;
    } else {
       return 0; // Streak broken
    }

    for (let stat of allStats) {
       const statDateStr = stat.date;
       const expectedDateStr = format(checkDate, "yyyy-MM-dd");
       
       if (statDateStr === expectedDateStr) {
           currentStreak++;
           checkDate.setDate(checkDate.getDate() - 1);
       } else {
           break;
       }
    }
    
    return currentStreak;
  };

  return {
    allMeals: meals,
    todayMeals: getTodayMeals(),
    todayCalories: getTodayCalories(),
    todayMacros: getTodayMacros(),
    addMeal,
    deleteMeal,
    calculateStreak,
  };
}
