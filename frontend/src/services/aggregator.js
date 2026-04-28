import { subDays, format, startOfDay } from 'date-fns';
import fitnessCalc from 'fitness-calc';

export function calculateDailyTotal(meals) {
  return meals.reduce(
    (acc, meal) => {
      acc.totalCalories += meal.calories || 0;
      acc.totalProtein += meal.protein || 0;
      acc.totalCarbs += meal.carbs || 0;
      acc.totalFat += meal.fat || 0;
      return acc;
    },
    { totalCalories: 0, totalProtein: 0, totalCarbs: 0, totalFat: 0 }
  );
}

export async function getWeeklySummary(db, userId) {
  const today = startOfDay(new Date());
  const summary = [];

  for (let i = 6; i >= 0; i--) {
    const date = subDays(today, i);
    const dateStr = format(date, 'yyyy-MM-dd');
    
    // Look up the dailyStats table
    const stat = await db.dailyStats.get(`${userId}+${dateStr}`);
    
    summary.push({
      date: format(date, 'EEE'), // e.g. Mon, Tue
      fullDate: dateStr,
      calories: stat ? stat.totalCalories : 0,
      protein: stat ? stat.totalProtein : 0,
      carbs: stat ? stat.totalCarbs : 0,
      fat: stat ? stat.totalFat : 0
    });
  }

  return summary;
}

export function calculateTDEE(profile) {
  if (!profile || !profile.gender || !profile.age || !profile.height || !profile.weight || !profile.activityLevel) {
    return 2000; // Default fallback
  }

  const bmr = fitnessCalc.BMR(
    profile.gender,
    profile.age,
    profile.height,
    profile.weight
  );
  
  // activityLevel string to multiplier mapping could be added here
  // Assuming activityLevel is already a multiplier or 'sedentary'
  let multiplier = 1.2;
  if (profile.activityLevel === 'light') multiplier = 1.375;
  if (profile.activityLevel === 'moderate') multiplier = 1.55;
  if (profile.activityLevel === 'active') multiplier = 1.725;
  if (profile.activityLevel === 'very_active') multiplier = 1.9;

  return Math.round(bmr * multiplier);
}
