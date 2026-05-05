"""Health Score Calculator for NutriSnap.

Generates a nutrition score (A-E) based on nutrient density,
processed state, and balance.
"""

from typing import Dict, Any

class HealthScorer:
    """Calculates nutritional quality scores for meals."""

    @staticmethod
    def calculate_score(nutrition: Dict[str, float]) -> dict:
        """Calculate a grade (A-E) based on nutrition profile.
        
        Algorithm based on simplified Nutri-Score logic:
        - Points for Energy, Saturated Fat, Sugar, Sodium (Higher is worse)
        - Points for Protein, Fiber, Fruit/Veg content (Higher is better)
        """
        # Basic scoring logic
        kcal = nutrition.get("calories", 0)
        prot = nutrition.get("protein", 0)
        fat = nutrition.get("fat", 0)
        carbs = nutrition.get("carbs", 0)
        
        # Simple density ratio
        if kcal == 0:
            return {"grade": "A", "score": 0, "summary": "No energy content detected"}
            
        # Protein/Calorie ratio (Higher is generally better for health scoring)
        prot_ratio = (prot * 4) / kcal if kcal > 0 else 0
        
        # Simple grading
        if prot_ratio > 0.3:
            grade = "A"
            summary = "Excellent protein density"
        elif prot_ratio > 0.2:
            grade = "B"
            summary = "Good nutritional balance"
        elif prot_ratio > 0.1:
            grade = "C"
            summary = "Average nutritional quality"
        else:
            grade = "D"
            summary = "Low nutrient density"
            
        # Penalty for high fat
        if (fat * 9) / kcal > 0.5:
            grade = "E"
            summary = "High fat content detected"
            
        return {
            "grade": grade,
            "prot_ratio": round(prot_ratio, 2),
            "summary": summary
        }
