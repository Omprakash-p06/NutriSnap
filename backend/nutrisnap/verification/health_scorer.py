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
        - Points for Energy, Saturated Fat, Sugar (Higher is worse)
        - Points for Protein, Fiber (Higher is better)
        """
        # Basic scoring logic
        kcal = nutrition.get("calories", 0)
        saturated_fat = nutrition.get("saturated_fat", 0)
        sugars = nutrition.get("sugars", 0)
        fiber = nutrition.get("fiber", 0)
        protein = nutrition.get("protein", 0)
        
        if kcal == 0:
            return {"grade": "A", "score": 0, "summary": "No energy content detected"}

        # Points for energy (0-10)
        # Roughly 80 kcal per point
        energy_points = min(10, int(kcal / 80))
        
        # Points for sugar (0-10)
        # > 45g is 10 points
        sugar_points = min(10, int(sugars / 4.5))
        
        # Points for saturated fat (0-10)
        # > 10g is 10 points
        sat_fat_points = min(10, int(saturated_fat / 1))
        
        negative_points = energy_points + sugar_points + sat_fat_points
        
        # Points for fiber (0-5)
        # > 4.7g is 5 points
        fiber_points = min(5, int(fiber / 0.94))
        
        # Points for protein (0-5)
        # > 8g is 5 points
        protein_points = min(5, int(protein / 1.6))
        
        positive_points = fiber_points + protein_points
        
        total_score = negative_points - positive_points
        
        # Simple grading based on total score
        if total_score <= -1:
            grade = "A"
            summary = "Excellent nutritional value"
        elif total_score <= 2:
            grade = "B"
            summary = "Good nutritional balance"
        elif total_score <= 10:
            grade = "C"
            summary = "Moderate nutritional value"
        elif total_score <= 18:
            grade = "D"
            summary = "Low nutritional value"
        else:
            grade = "E"
            summary = "Poor nutritional value"
            
        return {
            "grade": grade,
            "total_score": total_score,
            "summary": summary,
            "details": {
                "negative_points": negative_points,
                "positive_points": positive_points,
                "energy_pts": energy_points,
                "sugar_pts": sugar_points,
                "sat_fat_pts": sat_fat_points,
                "fiber_pts": fiber_points,
                "protein_pts": protein_points
            }
        }
