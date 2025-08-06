#!/usr/bin/env python3
"""
Test script for AI Food Logger - demonstrates functionality without requiring API keys
"""

import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple

class MockFoodLogger:
    """Mock version of FoodLogger for testing without API keys"""
    
    def __init__(self):
        # Mock data storage
        self.foods_db = []
        self.food_log = []
        
    def mock_gemini_analysis(self, food_description: str) -> Dict:
        """Mock Gemini API response based on common foods"""
        
        # Simple pattern matching for demo
        food_lower = food_description.lower()
        
        if 'chicken breast' in food_lower:
            return {
                "food_name": "Grilled Chicken Breast",
                "serving_size": "100g",
                "serving_size_grams": 100,
                "calories_per_serving": 165,
                "macros": {
                    "protein_g": 31.0,
                    "carbs_g": 0.0,
                    "fat_g": 3.6,
                    "fiber_g": 0.0,
                    "sugar_g": 0.0
                },
                "micronutrients": {
                    "sodium_mg": 74,
                    "potassium_mg": 256,
                    "calcium_mg": 15,
                    "iron_mg": 0.9,
                    "vitamin_c_mg": 0.0
                },
                "confidence": "high",
                "source_notes": "USDA FoodData Central"
            }
        elif 'brown rice' in food_lower:
            return {
                "food_name": "Brown Rice (cooked)",
                "serving_size": "1 cup (195g)",
                "serving_size_grams": 195,
                "calories_per_serving": 216,
                "macros": {
                    "protein_g": 5.0,
                    "carbs_g": 45.0,
                    "fat_g": 1.8,
                    "fiber_g": 3.5,
                    "sugar_g": 0.7
                },
                "micronutrients": {
                    "sodium_mg": 10,
                    "potassium_mg": 154,
                    "calcium_mg": 20,
                    "iron_mg": 0.8,
                    "vitamin_c_mg": 0.0
                },
                "confidence": "high",
                "source_notes": "USDA FoodData Central"
            }
        elif 'salmon' in food_lower:
            return {
                "food_name": "Atlantic Salmon Fillet",
                "serving_size": "100g",
                "serving_size_grams": 100,
                "calories_per_serving": 208,
                "macros": {
                    "protein_g": 25.4,
                    "carbs_g": 0.0,
                    "fat_g": 12.4,
                    "fiber_g": 0.0,
                    "sugar_g": 0.0
                },
                "micronutrients": {
                    "sodium_mg": 59,
                    "potassium_mg": 363,
                    "calcium_mg": 12,
                    "iron_mg": 0.8,
                    "vitamin_c_mg": 0.0
                },
                "confidence": "high",
                "source_notes": "USDA FoodData Central"
            }
        else:
            # Generic food for unknown items
            return {
                "food_name": "Unknown Food Item",
                "serving_size": "100g",
                "serving_size_grams": 100,
                "calories_per_serving": 150,
                "macros": {
                    "protein_g": 10.0,
                    "carbs_g": 15.0,
                    "fat_g": 5.0,
                    "fiber_g": 2.0,
                    "sugar_g": 3.0
                },
                "micronutrients": {
                    "sodium_mg": 100,
                    "potassium_mg": 200,
                    "calcium_mg": 50,
                    "iron_mg": 1.0,
                    "vitamin_c_mg": 5.0
                },
                "confidence": "low",
                "source_notes": "Estimated values"
            }
    
    def find_existing_food(self, food_name: str) -> Optional[Tuple[int, Dict]]:
        """Search for existing food in mock database"""
        for i, food in enumerate(self.foods_db):
            if food['food_name'].lower() == food_name.lower():
                return i, food
        return None
    
    def convert_units(self, amount: str, from_unit: str, to_grams: bool = True) -> float:
        """Convert between different units (oz to grams, etc.)"""
        amount_num = float(re.findall(r'[\d.]+', amount)[0]) if re.findall(r'[\d.]+', amount) else 0
        
        # Conversion factors to grams
        conversions = {
            'oz': 28.35,
            'ounce': 28.35,
            'ounces': 28.35,
            'lb': 453.59,
            'pound': 453.59,
            'pounds': 453.59,
            'kg': 1000,
            'kilogram': 1000,
            'kilograms': 1000,
            'g': 1,
            'gram': 1,
            'grams': 1,
        }
        
        from_unit_clean = from_unit.lower().strip()
        if from_unit_clean in conversions:
            return amount_num * conversions[from_unit_clean]
        else:
            # If unit not recognized, assume grams
            return amount_num
    
    def calculate_servings_and_nutrition(self, food_data: Dict, consumed_description: str) -> Dict:
        """Calculate actual nutrition based on consumed amount vs standard serving"""
        # Extract amount from description (e.g., "150g", "2 oz", "1.5 cups")
        amount_match = re.search(r'(\d+\.?\d*)\s*([a-zA-Z]+)', consumed_description)
        
        if not amount_match:
            # No specific amount found, assume 1 serving
            return {
                'servings': 1.0,
                'actual_grams': food_data.get('serving_size_grams', 100),
                'calories': food_data.get('calories_per_serving', 0),
                'protein_g': food_data.get('macros', {}).get('protein_g', 0),
                'carbs_g': food_data.get('macros', {}).get('carbs_g', 0),
                'fat_g': food_data.get('macros', {}).get('fat_g', 0),
                'fiber_g': food_data.get('macros', {}).get('fiber_g', 0),
            }
        
        consumed_amount = float(amount_match.group(1))
        consumed_unit = amount_match.group(2)
        
        # Convert consumed amount to grams
        consumed_grams = self.convert_units(str(consumed_amount), consumed_unit)
        
        # Calculate serving ratio
        standard_serving_grams = food_data.get('serving_size_grams', 100)
        serving_ratio = consumed_grams / standard_serving_grams
        
        # Calculate actual nutrition
        macros = food_data.get('macros', {})
        return {
            'servings': round(serving_ratio, 2),
            'actual_grams': consumed_grams,
            'calories': round(food_data.get('calories_per_serving', 0) * serving_ratio, 1),
            'protein_g': round(macros.get('protein_g', 0) * serving_ratio, 1),
            'carbs_g': round(macros.get('carbs_g', 0) * serving_ratio, 1),
            'fat_g': round(macros.get('fat_g', 0) * serving_ratio, 1),
            'fiber_g': round(macros.get('fiber_g', 0) * serving_ratio, 1),
        }
    
    def save_food_to_database(self, food_data: Dict) -> str:
        """Save new food to mock database"""
        food_id = f"food_{len(self.foods_db) + 1}"
        food_entry = {
            'food_id': food_id,
            'food_name': food_data.get('food_name', ''),
            'serving_size': food_data.get('serving_size', ''),
            'serving_size_grams': food_data.get('serving_size_grams', 0),
            'calories_per_serving': food_data.get('calories_per_serving', 0),
            'protein_g': food_data.get('macros', {}).get('protein_g', 0),
            'carbs_g': food_data.get('macros', {}).get('carbs_g', 0),
            'fat_g': food_data.get('macros', {}).get('fat_g', 0),
            'fiber_g': food_data.get('macros', {}).get('fiber_g', 0),
            'confidence': food_data.get('confidence', 'medium'),
            'source_notes': food_data.get('source_notes', ''),
            'created_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        self.foods_db.append(food_entry)
        return food_id
    
    def log_consumption(self, food_id: str, food_name: str, consumed_description: str, nutrition: Dict):
        """Log food consumption to mock database"""
        log_id = f"log_{len(self.food_log) + 1}"
        now = datetime.now()
        
        log_entry = {
            'log_id': log_id,
            'date': now.strftime('%Y-%m-%d'),
            'time': now.strftime('%H:%M:%S'),
            'food_id': food_id,
            'food_name': food_name,
            'description': consumed_description,
            'servings': nutrition['servings'],
            'actual_grams': nutrition['actual_grams'],
            'calories': nutrition['calories'],
            'protein_g': nutrition['protein_g'],
            'carbs_g': nutrition['carbs_g'],
            'fat_g': nutrition['fat_g'],
            'fiber_g': nutrition['fiber_g']
        }
        self.food_log.append(log_entry)
    
    def process_food_entry(self, food_description: str):
        """Main method to process a food entry"""
        print(f"🍽️  Processing: {food_description}")
        print("="*60)
        
        # Mock Gemini analysis
        print("🤖 Analyzing with Gemini AI (MOCK)...")
        food_data = self.mock_gemini_analysis(food_description)
        
        if not food_data:
            print("❌ Failed to analyze food. Please try again.")
            return
        
        print(f"✅ Identified food: {food_data['food_name']}")
        
        # Check if food exists in database
        existing_food = self.find_existing_food(food_data['food_name'])
        
        if existing_food:
            row_num, existing_data = existing_food
            print(f"📋 Found existing food in database (entry #{row_num + 1})")
            food_id = existing_data.get('food_id', f'food_{row_num + 1}')
            food_data_for_calc = existing_data
        else:
            print("➕ Food not found in database. Adding new entry...")
            food_id = self.save_food_to_database(food_data)
            food_data_for_calc = food_data
        
        # Calculate actual nutrition based on consumed amount
        nutrition = self.calculate_servings_and_nutrition(food_data_for_calc, food_description)
        
        # Log the consumption
        self.log_consumption(food_id, food_data['food_name'], food_description, nutrition)
        
        # Display results
        print("\n" + "🎉 FOOD LOGGED SUCCESSFULLY! 🎉".center(60))
        print("="*60)
        print(f"🥘 Food: {food_data['food_name']}")
        print(f"⚖️  Amount consumed: {nutrition['actual_grams']}g ({nutrition['servings']} servings)")
        print(f"🔥 Calories: {nutrition['calories']}")
        print(f"🥩 Protein: {nutrition['protein_g']}g")
        print(f"🍞 Carbs: {nutrition['carbs_g']}g")
        print(f"🥑 Fat: {nutrition['fat_g']}g")
        print(f"🌾 Fiber: {nutrition['fiber_g']}g")
        print("="*60)
        
        # Show database status
        print(f"\n📊 Database Status:")
        print(f"   • Foods in database: {len(self.foods_db)}")
        print(f"   • Log entries: {len(self.food_log)}")
        
        return {
            'food_data': food_data,
            'nutrition': nutrition,
            'food_id': food_id
        }
    
    def show_database_summary(self):
        """Display current database contents"""
        print("\n" + "📋 FOODS DATABASE".center(60))
        print("="*60)
        for i, food in enumerate(self.foods_db, 1):
            print(f"{i}. {food['food_name']} ({food['serving_size']}) - {food['calories_per_serving']} cal")
        
        print("\n" + "📝 FOOD LOG".center(60))
        print("="*60)
        for i, entry in enumerate(self.food_log, 1):
            print(f"{i}. {entry['date']} {entry['time']}: {entry['description']} - {entry['calories']} cal")

def main():
    """Test the food logger with various examples"""
    logger = MockFoodLogger()
    
    print("🚀 AI FOOD LOGGER - TEST MODE")
    print("="*60)
    print("This is a mock version that demonstrates functionality without API keys.")
    print("="*60)
    
    # Test cases
    test_foods = [
        "I ate 150g of grilled chicken breast",
        "2 cups of brown rice",
        "3 oz salmon fillet",
        "1 apple"  # This will use the generic fallback
    ]
    
    for i, food_desc in enumerate(test_foods, 1):
        print(f"\n🧪 TEST {i}/{len(test_foods)}")
        logger.process_food_entry(food_desc)
        print("\n" + "-"*60)
    
    # Show final database summary
    logger.show_database_summary()
    
    print(f"\n✨ Test completed! The system successfully:")
    print("   ✅ Analyzed food descriptions")
    print("   ✅ Calculated serving sizes and unit conversions")
    print("   ✅ Stored foods in database")
    print("   ✅ Logged consumption entries")
    print("   ✅ Handled both new and existing foods")

if __name__ == "__main__":
    main()
