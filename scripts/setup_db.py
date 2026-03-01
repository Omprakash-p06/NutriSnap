"""Database Setup Script.

Creates database tables and optionally seeds with sample data.
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database import create_tables, SessionLocal
from backend.models import User, Meal, FoodItem


def setup_database() -> None:
    """Create all database tables."""
    print("Creating database tables...")
    create_tables()
    print("✓ Database tables created successfully")


def seed_sample_data() -> None:
    """Add sample data for development."""
    print("Seeding sample data...")
    
    db = SessionLocal()
    try:
        # Check if sample user exists
        existing_user = db.query(User).filter(User.email == "demo@nutrisnap.ai").first()
        if existing_user:
            print("  Sample data already exists, skipping...")
            return
        
        # Create sample user
        user = User(
            email="demo@nutrisnap.ai",
            name="Demo User",
            height=170.0,
            weight=70.0,
            age=25,
            activity_level="moderate",
            daily_calorie_target=2000,
        )
        db.add(user)
        db.flush()
        
        # Create sample meals
        meal1 = Meal(
            user_id=user.id,
            total_calories=450,
            total_protein=18.0,
            total_carbs=65.0,
            total_fats=12.0,
        )
        db.add(meal1)
        db.flush()
        
        # Add food items
        db.add(FoodItem(
            meal_id=meal1.id,
            food_class="rice",
            confidence=0.92,
            ai_portion_grams=150.0,
            user_portion_grams=150.0,
            calories=195,
            protein=4.1,
            carbs=42.3,
            fats=0.5,
        ))
        db.add(FoodItem(
            meal_id=meal1.id,
            food_class="dal",
            confidence=0.88,
            ai_portion_grams=180.0,
            user_portion_grams=180.0,
            calories=234,
            protein=13.5,
            carbs=27.0,
            fats=10.8,
        ))
        
        db.commit()
        print("✓ Sample data seeded successfully")
        
    except Exception as e:
        db.rollback()
        print(f"✗ Error seeding data: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Database setup")
    parser.add_argument("--seed", action="store_true", help="Seed sample data")
    
    args = parser.parse_args()
    
    setup_database()
    
    if args.seed:
        seed_sample_data()
    
    print("\nDatabase setup complete!")
