"""
Core Food Logger Logic
Contains all business logic for food logging, separate from API implementations.
"""

import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Protocol
from dataclasses import dataclass


@dataclass
class FoodData:
    """Data class for food information"""
    food_name: str
    serving_size: str
    serving_size_grams: float
    calories_per_serving: float
    protein_g: float
    carbs_g: float
    fat_g: float
    fiber_g: float
    sugar_g: float = 0.0
    sodium_mg: float = 0.0
    potassium_mg: float = 0.0
    calcium_mg: float = 0.0
    iron_mg: float = 0.0
    vitamin_c_mg: float = 0.0
    confidence: str = "medium"
    source_notes: str = ""


@dataclass
class NutritionCalculation:
    """Data class for calculated nutrition"""
    servings: float
    actual_grams: float
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float
    fiber_g: float


@dataclass
class ConsumptionEntry:
    """Data class for consumption log entry"""
    log_id: str
    date: str
    time: str
    food_id: str
    food_name: str
    description: str
    nutrition: NutritionCalculation


class FoodAnalyzer(Protocol):
    """Protocol for food analysis (Gemini API)"""
    def analyze_food(self, description: str) -> Optional[FoodData]:
        """Analyze food description and return nutrition data"""
        ...


class FoodDatabase(Protocol):
    """Protocol for food database operations (Google Sheets)"""
    def find_food(self, food_name: str) -> Optional[Tuple[str, FoodData]]:
        """Find existing food by name, return (food_id, food_data) if found"""
        ...
    
    def save_food(self, food_data: FoodData) -> str:
        """Save new food to database, return food_id"""
        ...
    
    def log_consumption(self, entry: ConsumptionEntry) -> None:
        """Log consumption entry to database"""
        ...


class UnitConverter:
    """Handles unit conversions"""
    
    # Conversion factors to grams
    CONVERSIONS = {
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
    
    @classmethod
    def to_grams(cls, amount: float, unit: str) -> float:
        """Convert amount in given unit to grams"""
        unit_clean = unit.lower().strip()
        if unit_clean in cls.CONVERSIONS:
            return amount * cls.CONVERSIONS[unit_clean]
        else:
            # If unit not recognized, assume grams
            return amount
    
    @classmethod
    def extract_amount_and_unit(cls, description: str) -> Optional[Tuple[float, str]]:
        """Extract amount and unit from description (e.g., "150g" -> (150.0, "g"))"""
        match = re.search(r'(\d+\.?\d*)\s*([a-zA-Z]+)', description)
        if match:
            amount = float(match.group(1))
            unit = match.group(2)
            return amount, unit
        return None


class NutritionCalculator:
    """Handles nutrition calculations based on serving sizes"""
    
    @staticmethod
    def calculate_nutrition(food_data: FoodData, consumed_description: str) -> NutritionCalculation:
        """Calculate actual nutrition based on consumed amount vs standard serving"""
        
        # Extract amount from description
        amount_info = UnitConverter.extract_amount_and_unit(consumed_description)
        
        if not amount_info:
            # No specific amount found, assume 1 serving
            return NutritionCalculation(
                servings=1.0,
                actual_grams=food_data.serving_size_grams,
                calories=food_data.calories_per_serving,
                protein_g=food_data.protein_g,
                carbs_g=food_data.carbs_g,
                fat_g=food_data.fat_g,
                fiber_g=food_data.fiber_g
            )
        
        consumed_amount, consumed_unit = amount_info
        
        # Convert consumed amount to grams
        consumed_grams = UnitConverter.to_grams(consumed_amount, consumed_unit)
        
        # Calculate serving ratio
        serving_ratio = consumed_grams / food_data.serving_size_grams
        
        # Calculate actual nutrition
        return NutritionCalculation(
            servings=round(serving_ratio, 2),
            actual_grams=consumed_grams,
            calories=round(food_data.calories_per_serving * serving_ratio, 1),
            protein_g=round(food_data.protein_g * serving_ratio, 1),
            carbs_g=round(food_data.carbs_g * serving_ratio, 1),
            fat_g=round(food_data.fat_g * serving_ratio, 1),
            fiber_g=round(food_data.fiber_g * serving_ratio, 1)
        )


class FoodLoggerCore:
    """Core food logging logic - independent of API implementations"""
    
    def __init__(self, analyzer: FoodAnalyzer, database: FoodDatabase):
        self.analyzer = analyzer
        self.database = database
        self.calculator = NutritionCalculator()
    
    def process_food_entry(self, food_description: str) -> Dict:
        """
        Main method to process a food entry
        Returns dict with results for display/further processing
        """
        result = {
            'success': False,
            'food_data': None,
            'nutrition': None,
            'food_id': None,
            'is_new_food': False,
            'error': None
        }
        
        try:
            # Step 1: Analyze food with AI
            food_data = self.analyzer.analyze_food(food_description)
            if not food_data:
                result['error'] = "Failed to analyze food description"
                return result
            
            result['food_data'] = food_data
            
            # Step 2: Check if food exists in database
            existing_food = self.database.find_food(food_data.food_name)
            
            if existing_food:
                food_id, existing_food_data = existing_food
                result['food_id'] = food_id
                result['is_new_food'] = False
                # Use existing food data for calculations
                food_data_for_calc = existing_food_data
            else:
                # Save new food to database
                food_id = self.database.save_food(food_data)
                result['food_id'] = food_id
                result['is_new_food'] = True
                food_data_for_calc = food_data
            
            # Step 3: Calculate actual nutrition
            nutrition = self.calculator.calculate_nutrition(food_data_for_calc, food_description)
            result['nutrition'] = nutrition
            
            # Step 4: Log consumption
            now = datetime.now()
            consumption_entry = ConsumptionEntry(
                log_id=f"log_{int(now.timestamp())}",
                date=now.strftime('%Y-%m-%d'),
                time=now.strftime('%H:%M:%S'),
                food_id=food_id,
                food_name=food_data.food_name,
                description=food_description,
                nutrition=nutrition
            )
            
            self.database.log_consumption(consumption_entry)
            
            result['success'] = True
            return result
            
        except Exception as e:
            result['error'] = str(e)
            return result
    
    def get_daily_summary(self, date: str = None) -> Dict:
        """Get nutrition summary for a specific date (defaults to today)"""
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')
        
        # This would need to be implemented in the database protocol
        # For now, return a placeholder
        return {
            'date': date,
            'total_calories': 0,
            'total_protein': 0,
            'total_carbs': 0,
            'total_fat': 0,
            'total_fiber': 0,
            'entries_count': 0
        }


class MockFoodAnalyzer:
    """Mock implementation of FoodAnalyzer for testing"""
    
    MOCK_FOODS = {
        'chicken breast': FoodData(
            food_name="Grilled Chicken Breast",
            serving_size="100g",
            serving_size_grams=100,
            calories_per_serving=165,
            protein_g=31.0,
            carbs_g=0.0,
            fat_g=3.6,
            fiber_g=0.0,
            confidence="high",
            source_notes="USDA FoodData Central"
        ),
        'brown rice': FoodData(
            food_name="Brown Rice (cooked)",
            serving_size="1 cup (195g)",
            serving_size_grams=195,
            calories_per_serving=216,
            protein_g=5.0,
            carbs_g=45.0,
            fat_g=1.8,
            fiber_g=3.5,
            confidence="high",
            source_notes="USDA FoodData Central"
        ),
        'salmon': FoodData(
            food_name="Atlantic Salmon Fillet",
            serving_size="100g",
            serving_size_grams=100,
            calories_per_serving=208,
            protein_g=25.4,
            carbs_g=0.0,
            fat_g=12.4,
            fiber_g=0.0,
            confidence="high",
            source_notes="USDA FoodData Central"
        )
    }
    
    def analyze_food(self, description: str) -> Optional[FoodData]:
        """Mock food analysis"""
        description_lower = description.lower()
        
        for key, food_data in self.MOCK_FOODS.items():
            if key in description_lower:
                return food_data
        
        # Generic fallback
        return FoodData(
            food_name="Unknown Food Item",
            serving_size="100g",
            serving_size_grams=100,
            calories_per_serving=150,
            protein_g=10.0,
            carbs_g=15.0,
            fat_g=5.0,
            fiber_g=2.0,
            confidence="low",
            source_notes="Estimated values"
        )


class MockFoodDatabase:
    """Mock implementation of FoodDatabase for testing"""
    
    def __init__(self):
        self.foods = {}  # food_id -> FoodData
        self.food_name_to_id = {}  # food_name -> food_id
        self.consumption_log = []  # List of ConsumptionEntry
        self._next_food_id = 1
    
    def find_food(self, food_name: str) -> Optional[Tuple[str, FoodData]]:
        """Find existing food by name"""
        food_id = self.food_name_to_id.get(food_name.lower())
        if food_id:
            return food_id, self.foods[food_id]
        return None
    
    def save_food(self, food_data: FoodData) -> str:
        """Save new food to database"""
        food_id = f"food_{self._next_food_id}"
        self._next_food_id += 1
        
        self.foods[food_id] = food_data
        self.food_name_to_id[food_data.food_name.lower()] = food_id
        
        return food_id
    
    def log_consumption(self, entry: ConsumptionEntry) -> None:
        """Log consumption entry"""
        self.consumption_log.append(entry)
    
    def get_foods_count(self) -> int:
        """Get number of foods in database"""
        return len(self.foods)
    
    def get_log_count(self) -> int:
        """Get number of log entries"""
        return len(self.consumption_log)
