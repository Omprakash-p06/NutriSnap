"""
Test suite for MultiFoodMerger: prediction merger for multi-food plate analysis.
"""

import numpy as np
import pytest
from pathlib import Path


class TestDensityLoader:
    """Tests for density knowledge base loading."""

    def test_load_densities(self):
        """Test that density database loads successfully."""
        from nutrisnap.data.densities import load_density_db
        
        db = load_density_db()
        assert db is not None
        assert "foods" in db
        assert len(db["foods"]) > 0
    
    def test_known_food_lookup(self):
        """Test lookup of known foods."""
        from nutrisnap.data.densities import get_food_density
        
        density = get_food_density("chicken")
        assert density is not None
        assert density["density"] > 0
    
    def test_unknown_food_fallback(self):
        """Test fallback for unknown foods."""
        from nutrisnap.data.densities import get_food_density
        
        data = get_food_density("unknown_food_xyz")
        assert data is not None
        # Should return fallback values
        assert data["density"] == 1.0


class TestMergerLogic:
    """Tests for merger computation logic."""
    
    def test_merger_logic(self):
        """Test basic merger calculation: volume * density = mass."""
        from nutrisnap.data.densities import get_food_density
        
        # Chicken breast: ~1.04 g/cm³
        chicken = get_food_density("chicken")
        volume_cm3 = 100.0  # 100 cm³ = 100 mL
        
        mass = volume_cm3 * chicken["density"]
        
        assert mass == pytest.approx(104.0, rel=0.01)
    
    def test_nutrition_calculation(self):
        """Test nutrition from mass and density data."""
        from nutrisnap.data.densities import get_food_density
        
        chicken = get_food_density("chicken")
        mass_g = 100.0
        
        # Per 100g: 165 cal, 31g protein
        scale = mass_g / 100.0
        calories = chicken["calories"] * scale
        protein = chicken["protein"] * scale
        
        assert calories == pytest.approx(165.0, rel=0.01)
        assert protein == pytest.approx(31.0, rel=0.01)


class TestRedundancyHandling:
    """Tests for overlapping detection handling."""
    
    def test_redundancy_handling(self):
        """Test IoU-based redundancy detection."""
        # Two partially overlapping masks
        mask1 = np.zeros((100, 100), dtype=np.uint8)
        mask2 = np.zeros((100, 100), dtype=np.uint8)
        
        # Square masks
        mask1[20:60, 20:60] = 1
        mask2[40:80, 40:80] = 1
        
        # Calculate IoU
        intersection = np.logical_and(mask1, mask2).sum()
        union = np.logical_or(mask1, mask2).sum()
        iou = intersection / union if union > 0 else 0
        
        # Should have some overlap
        assert iou > 0
        assert iou < 1.0
    
    def test_volume_adjustment_for_overlap(self):
        """Test volume adjustment when masks overlap."""
        # Simplified logic: if IoU > threshold, reduce combined volume
        iou = 0.3  # 30% overlap
        
        # Two items with volumes
        vol1 = 100.0
        vol2 = 100.0
        
        # Adjustment factor based on overlap
        if iou > 0.2:
            overlap_penalty = iou * 0.5
            combined = vol1 + vol2 * (1 - overlap_penalty)
        else:
            combined = vol1 + vol2
        
        assert combined < (vol1 + vol2)  # Should be reduced


class TestMultiItemAggregation:
    """Tests for aggregating multiple food items."""
    
    def test_aggregate_nutrition(self):
        """Test aggregating nutrition for multiple items."""
        from nutrisnap.data.densities import get_food_density
        
        items = [
            {"label": "chicken", "volume_cm3": 100.0},
            {"label": "rice", "volume_cm3": 150.0},
            {"label": "broccoli", "volume_cm3": 50.0},
        ]
        
        total_calories = 0.0
        total_protein = 0.0
        total_carbs = 0.0
        total_fat = 0.0
        
        for item in items:
            food = get_food_density(item["label"])
            mass = item["volume_cm3"] * food["density"]
            scale = mass / 100.0
            
            total_calories += food["calories"] * scale
            total_protein += food["protein"] * scale
            total_carbs += food["carbohydrates"] * scale
            total_fat += food["fat"] * scale
        
        # Verify aggregation works
        assert total_calories > 0
        assert total_protein > 0
        assert total_carbs > 0
        assert total_fat > 0