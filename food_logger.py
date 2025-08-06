#!/usr/bin/env python3
"""
AI Food Logger - Command Line Interface
Thin CLI wrapper around the core food logging logic.
"""

import sys
import os
from dotenv import load_dotenv

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from food_logger.core import FoodLoggerCore, MockFoodAnalyzer, MockFoodDatabase
from food_logger.gemini_client import GeminiClient
from food_logger.sheets_client import SheetsClient

# Load environment variables
load_dotenv()


def create_food_logger(use_mock: bool = False) -> FoodLoggerCore:
    """Factory function to create FoodLoggerCore with appropriate clients"""
    
    if use_mock:
        # Use mock implementations for testing
        analyzer = MockFoodAnalyzer()
        database = MockFoodDatabase()
    else:
        # Use real API clients
        try:
            analyzer = GeminiClient()
            database = SheetsClient()
        except ValueError as e:
            print(f"Error setting up APIs: {e}")
            print("Using mock implementations instead...")
            analyzer = MockFoodAnalyzer()
            database = MockFoodDatabase()
    
    return FoodLoggerCore(analyzer, database)


def display_result(result: dict):
    """Display the food logging result in a nice format"""
    if not result['success']:
        print(f"❌ Error: {result['error']}")
        return
    
    food_data = result['food_data']
    nutrition = result['nutrition']
    
    print("\n" + "🎉 FOOD LOGGED SUCCESSFULLY! 🎉".center(60))
    print("="*60)
    print(f"🥘 Food: {food_data.food_name}")
    print(f"⚖️  Amount consumed: {nutrition.actual_grams}g ({nutrition.servings} servings)")
    print(f"🔥 Calories: {nutrition.calories}")
    print(f"🥩 Protein: {nutrition.protein_g}g")
    print(f"🍞 Carbs: {nutrition.carbs_g}g")
    print(f"🥑 Fat: {nutrition.fat_g}g")
    print(f"🌾 Fiber: {nutrition.fiber_g}g")
    
    if result['is_new_food']:
        print(f"➕ Added new food to database (ID: {result['food_id']})")
    else:
        print(f"📋 Used existing food from database (ID: {result['food_id']})")
    
    print("="*60)


def main():
    """Main CLI entry point"""
    if len(sys.argv) < 2:
        print("🍽️  AI Food Logger - Command Line Interface")
        print("="*50)
        print("Usage:")
        print("  python food_logger.py \"<food description>\"")
        print("  python food_logger.py --mock \"<food description>\"")
        print()
        print("Examples:")
        print("  python food_logger.py \"I ate 150g of grilled chicken breast\"")
        print("  python food_logger.py \"2 slices of whole wheat bread\"")
        print("  python food_logger.py \"1 cup of brown rice\"")
        print("  python food_logger.py --mock \"3 oz salmon fillet\"")
        print()
        print("Options:")
        print("  --mock    Use mock implementations (no API calls required)")
        sys.exit(1)
    
    # Check for mock flag
    use_mock = '--mock' in sys.argv
    if use_mock:
        sys.argv.remove('--mock')
    
    if len(sys.argv) < 2:
        print("Error: Food description is required")
        sys.exit(1)
    
    food_description = " ".join(sys.argv[1:])
    
    print(f"🍽️  Processing: {food_description}")
    if use_mock:
        print("🧪 Using mock implementations (no API calls)")
    print("="*60)
    
    try:
        # Create food logger with appropriate clients
        logger = create_food_logger(use_mock)
        
        # Process the food entry
        result = logger.process_food_entry(food_description)
        
        # Display results
        display_result(result)
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
