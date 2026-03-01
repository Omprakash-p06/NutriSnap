import client from './client';


export interface MealItem {
    food_class: string;
    confidence: number;
    ai_portion_grams: number;
    user_portion_grams: number;
    calories: number;
    protein: number;
    carbs: number;
    fats: number;
}

export interface Meal {
    id: number;
    total_calories: number;
    total_protein: number;
    total_carbs: number;
    total_fats: number;
    logged_at: string;
    food_items: MealItem[];
}

export interface CreateMealRequest {
    total_calories: number;
    total_protein: number;
    total_carbs: number;
    total_fats: number;
    food_items: MealItem[];
}

export interface DashboardStats {
    calories_consumed: number;
    calories_target: number;
    calories_remaining: number;
    protein: number;
    carbs: number;
    fats: number;
    meal_count: number;
}

export interface WeeklyTrend {
    day_name: string;
    calories: number;
}

/**
 * Create a new meal log
 */
export const createMeal = async (mealData: CreateMealRequest): Promise<Meal> => {
    const response = await client.post<Meal>('/api/v1/meals', mealData);
    return response.data;
};

/**
 * Get meal history
 */
export const getMeals = async ({ limit = 10, offset = 0 } = {}): Promise<Meal[]> => {
    const response = await client.get<Meal[]>('/api/v1/meals', {
        params: { limit, offset },
    });
    return response.data;
};

/**
 * Get a specific meal
 */
export const getMeal = async (mealId: number): Promise<Meal> => {
    const response = await client.get<Meal>(`/api/v1/meals/${mealId}`);
    return response.data;
};

/**
 * Update a meal
 */
export const updateMeal = async (mealId: number, updates: Partial<Meal>): Promise<Meal> => {
    const response = await client.put<Meal>(`/api/v1/meals/${mealId}`, updates);
    return response.data;
};

/**
 * Delete a meal
 */
export const deleteMeal = async (mealId: number): Promise<void> => {
    await client.delete(`/api/v1/meals/${mealId}`);
};

/**
 * Get dashboard statistics
 */
export const getDashboardStats = async (): Promise<DashboardStats> => {
    const response = await client.get<DashboardStats>('/api/v1/dashboard/stats');
    return response.data;
};

/**
 * Get weekly trend
 */
export const getWeeklyTrend = async (): Promise<WeeklyTrend[]> => {
    const response = await client.get<WeeklyTrend[]>('/api/v1/dashboard/weekly');
    return response.data;
};

export default {
    createMeal,
    getMeals,
    getMeal,
    updateMeal,
    deleteMeal,
    getDashboardStats,
    getWeeklyTrend,
};
