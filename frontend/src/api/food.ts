import client from './client';

export interface NutritionInfo {
    calories: number;
    protein: number;
    carbs: number;
    fats: number;
}

export interface DetectedFood {
    food_class: string;
    confidence: number;
    bbox: number[];
    estimated_grams: number;
    portion_unit?: string;
    portion_amount?: number;
    portion_display?: string;
    nutrition: NutritionInfo;
    adjusted_grams?: number; // Optional mainly for frontend state logic
}

export interface AnalysisResponse {
    success: boolean;
    image_id: string;
    detected_foods: DetectedFood[];
    total_nutrition: NutritionInfo;
}

/**
 * Analyze a food image
 */
export const analyzeFood = async (imageFile: File): Promise<AnalysisResponse> => {
    const formData = new FormData();
    formData.append('file', imageFile);

    const response = await client.post<AnalysisResponse>('/api/v1/analyze', formData, {
        headers: {
            'Content-Type': 'multipart/form-data',
        },
    });
    return response.data;
};

/**
 * Get nutrition info for a food class
 */
export const getNutrition = async (foodClass: string, grams: number = 100): Promise<NutritionInfo> => {
    const response = await client.get<NutritionInfo>('/api/v1/nutrition', {
        params: { food_class: foodClass, grams },
    });
    return response.data;
};

export default {
    analyzeFood,
    getNutrition,
};
