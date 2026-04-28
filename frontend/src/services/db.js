import Dexie from 'dexie';

export const db = new Dexie('NutriSnapDB');

db.version(1).stores({
  meals: '++id, userId, timestamp, name, calories, protein, carbs, fat',
  dailyStats: '[userId+date], userId, date, totalCalories, totalProtein, totalCarbs, totalFat'
});
