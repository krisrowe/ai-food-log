"""
Unit Tests for Food Logger Core Logic
Tests all business logic independently of API implementations.
"""

import pytest
from unittest.mock import Mock
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from food_logger.core import (
    FoodData, NutritionCalculation, ConsumptionEntry,
    UnitConverter, NutritionCalculator, FoodLoggerCore,
    MockFoodAnalyzer, MockFoodDatabase
)


class TestFoodData:
    """Test FoodData dataclass"""
    
    def test_food_data_creation(self):
        """Test creating FoodData with required fields"""
        food = FoodData(
            food_name="Test Food",
            serving_size="100g",
            serving_size_grams=100.0,
            calories_per_serving=200.0,
            protein_g=20.0,
            carbs_g=30.0,
            fat_g=10.0,
            fiber_g=5.0
        )
        
        assert food.food_name == "Test Food"
        assert food.serving_size_grams == 100.0
        assert food.calories_per_serving == 200.0
        assert food.confidence == "medium"  # default value


class TestUnitConverter:
    """Test unit conversion functionality"""
    
    def test_grams_conversion(self):
        """Test converting grams (should be no change)"""
        result = UnitConverter.to_grams(100, "g")
        assert result == 100.0
        
        result = UnitConverter.to_grams(150, "grams")
        assert result == 150.0
    
    def test_ounces_conversion(self):
        """Test converting ounces to grams"""
        result = UnitConverter.to_grams(1, "oz")
        assert abs(result - 28.35) < 0.01
        
        result = UnitConverter.to_grams(2, "ounces")
        assert abs(result - 56.7) < 0.1
    
    def test_pounds_conversion(self):
        """Test converting pounds to grams"""
        result = UnitConverter.to_grams(1, "lb")
        assert abs(result - 453.59) < 0.01
    
    def test_kilograms_conversion(self):
        """Test converting kilograms to grams"""
        result = UnitConverter.to_grams(1, "kg")
        assert result == 1000.0
    
    def test_unknown_unit(self):
        """Test handling unknown units (should assume grams)"""
        result = UnitConverter.to_grams(100, "unknown_unit")
        assert result == 100.0
    
    @pytest.mark.parametrize("description,expected", [
        ("150g of chicken", (150.0, "g")),
        ("2.5 oz salmon", (2.5, "oz")),
        ("1 cup rice", (1.0, "cup")),
        ("just some food", None),
    ])
    def test_extract_amount_and_unit(self, description, expected):
        """Test extracting amount and unit from descriptions"""
        result = UnitConverter.extract_amount_and_unit(description)
        assert result == expected


class TestNutritionCalculator:
    """Test nutrition calculation logic"""
    
    @pytest.fixture
    def food_data(self):
        """Test food data fixture"""
        return FoodData(
            food_name="Test Food",
            serving_size="100g",
            serving_size_grams=100.0,
            calories_per_serving=200.0,
            protein_g=20.0,
            carbs_g=30.0,
            fat_g=10.0,
            fiber_g=5.0
        )
    
    def test_calculate_exact_serving(self, food_data):
        """Test calculation for exact serving size"""
        result = NutritionCalculator.calculate_nutrition(
            food_data, "100g of test food"
        )
        
        assert result.servings == 1.0
        assert result.actual_grams == 100.0
        assert result.calories == 200.0
        assert result.protein_g == 20.0
    
    def test_calculate_double_serving(self, food_data):
        """Test calculation for double serving size"""
        result = NutritionCalculator.calculate_nutrition(
            food_data, "200g of test food"
        )
        
        assert result.servings == 2.0
        assert result.actual_grams == 200.0
        assert result.calories == 400.0
        assert result.protein_g == 40.0
    
    def test_calculate_half_serving(self, food_data):
        """Test calculation for half serving size"""
        result = NutritionCalculator.calculate_nutrition(
            food_data, "50g of test food"
        )
        
        assert result.servings == 0.5
        assert result.actual_grams == 50.0
        assert result.calories == 100.0
        assert result.protein_g == 10.0
    
    def test_calculate_with_ounces(self, food_data):
        """Test calculation with ounce input"""
        # 1 oz = 28.35g, so for 100g serving, 1 oz = 0.2835 servings
        result = NutritionCalculator.calculate_nutrition(
            food_data, "1 oz of test food"
        )
        
        assert abs(result.servings - 0.28) < 0.01
        assert abs(result.actual_grams - 28.35) < 0.1
        assert abs(result.calories - 56.7) < 1.0
    
    def test_calculate_no_amount(self, food_data):
        """Test calculation when no amount is specified (assume 1 serving)"""
        result = NutritionCalculator.calculate_nutrition(
            food_data, "some test food"
        )
        
        assert result.servings == 1.0
        assert result.actual_grams == 100.0
        assert result.calories == 200.0


class TestMockFoodAnalyzer:
    """Test mock food analyzer"""
    
    @pytest.fixture
    def analyzer(self):
        return MockFoodAnalyzer()
    
    def test_analyze_chicken_breast(self, analyzer):
        """Test analyzing chicken breast"""
        result = analyzer.analyze_food("grilled chicken breast")
        
        assert result is not None
        assert result.food_name == "Grilled Chicken Breast"
        assert result.serving_size_grams == 100
        assert result.protein_g > 25  # Chicken is high protein
        assert result.carbs_g == 0.0  # Chicken has no carbs
    
    def test_analyze_brown_rice(self, analyzer):
        """Test analyzing brown rice"""
        result = analyzer.analyze_food("brown rice")
        
        assert result is not None
        assert result.food_name == "Brown Rice (cooked)"
        assert result.carbs_g > 40  # Rice is high carb
        assert result.fiber_g > 3  # Brown rice has fiber
    
    def test_analyze_unknown_food(self, analyzer):
        """Test analyzing unknown food (should return generic)"""
        result = analyzer.analyze_food("some unknown exotic food")
        
        assert result is not None
        assert result.food_name == "Unknown Food Item"
        assert result.confidence == "low"


class TestMockFoodDatabase:
    """Test mock food database"""
    
    @pytest.fixture
    def database(self):
        return MockFoodDatabase()
    
    @pytest.fixture
    def food_data(self):
        return FoodData(
            food_name="Test Food",
            serving_size="100g",
            serving_size_grams=100.0,
            calories_per_serving=200.0,
            protein_g=20.0,
            carbs_g=30.0,
            fat_g=10.0,
            fiber_g=5.0
        )
    
    def test_save_and_find_food(self, database, food_data):
        """Test saving and finding food"""
        # Initially should not find the food
        result = database.find_food("Test Food")
        assert result is None
        
        # Save the food
        food_id = database.save_food(food_data)
        assert food_id is not None
        assert food_id.startswith("food_")
        
        # Now should find the food
        result = database.find_food("Test Food")
        assert result is not None
        found_id, found_data = result
        assert found_id == food_id
        assert found_data.food_name == "Test Food"
    
    def test_case_insensitive_search(self, database, food_data):
        """Test that food search is case insensitive"""
        food_id = database.save_food(food_data)
        
        # Should find with different cases
        result = database.find_food("test food")
        assert result is not None
        
        result = database.find_food("TEST FOOD")
        assert result is not None
    
    def test_log_consumption(self, database):
        """Test logging consumption"""
        nutrition = NutritionCalculation(
            servings=1.5,
            actual_grams=150.0,
            calories=300.0,
            protein_g=30.0,
            carbs_g=45.0,
            fat_g=15.0,
            fiber_g=7.5
        )
        
        entry = ConsumptionEntry(
            log_id="test_log",
            date="2024-01-01",
            time="12:00:00",
            food_id="food_1",
            food_name="Test Food",
            description="150g of test food",
            nutrition=nutrition
        )
        
        initial_count = database.get_log_count()
        database.log_consumption(entry)
        
        assert database.get_log_count() == initial_count + 1


class TestFoodLoggerCore:
    """Test the core food logger logic"""
    
    @pytest.fixture
    def core(self):
        analyzer = MockFoodAnalyzer()
        database = MockFoodDatabase()
        return FoodLoggerCore(analyzer, database)
    
    def test_process_new_food_entry(self, core):
        """Test processing a new food entry"""
        result = core.process_food_entry("150g of grilled chicken breast")
        
        assert result['success'] is True
        assert result['food_data'] is not None
        assert result['nutrition'] is not None
        assert result['food_id'] is not None
        assert result['is_new_food'] is True
        
        # Check nutrition calculation
        nutrition = result['nutrition']
        assert nutrition.actual_grams == 150.0
        assert nutrition.servings == 1.5  # 150g / 100g serving
        
        # Check database was updated
        assert core.database.get_foods_count() == 1
        assert core.database.get_log_count() == 1
    
    def test_process_existing_food_entry(self, core):
        """Test processing an existing food entry"""
        # First entry - should be new
        result1 = core.process_food_entry("100g of grilled chicken breast")
        assert result1['is_new_food'] is True
        
        # Second entry - should use existing
        result2 = core.process_food_entry("200g of grilled chicken breast")
        assert result2['is_new_food'] is False
        assert result2['food_id'] == result1['food_id']
        
        # Should have 1 food, 2 log entries
        assert core.database.get_foods_count() == 1
        assert core.database.get_log_count() == 2
    
    def test_process_analyzer_failure(self):
        """Test handling analyzer failure"""
        # Mock analyzer to return None
        mock_analyzer = Mock()
        mock_analyzer.analyze_food.return_value = None
        database = MockFoodDatabase()
        
        core = FoodLoggerCore(mock_analyzer, database)
        result = core.process_food_entry("some food")
        
        assert result['success'] is False
        assert result['error'] is not None
        assert "Failed to analyze" in result['error']
    
    def test_process_database_exception(self):
        """Test handling database exceptions"""
        # Mock database to raise exception
        analyzer = MockFoodAnalyzer()
        mock_database = Mock()
        mock_database.find_food.side_effect = Exception("Database error")
        
        core = FoodLoggerCore(analyzer, mock_database)
        result = core.process_food_entry("chicken breast")
        
        assert result['success'] is False
        assert result['error'] is not None
        assert "Database error" in result['error']


@pytest.mark.integration
class TestIntegration:
    """Integration tests using mock implementations"""
    
    @pytest.fixture
    def core(self):
        return FoodLoggerCore(MockFoodAnalyzer(), MockFoodDatabase())
    
    def test_full_workflow(self, core):
        """Test complete workflow from input to database storage"""
        # Process multiple different foods
        foods = [
            "150g of grilled chicken breast",
            "1 cup of brown rice",
            "3 oz of salmon fillet",
            "100g of grilled chicken breast"  # Same as first, should reuse
        ]
        
        results = []
        for food in foods:
            result = core.process_food_entry(food)
            results.append(result)
            assert result['success'] is True, f"Failed to process: {food}"
        
        # Should have 3 unique foods (chicken, rice, salmon)
        assert core.database.get_foods_count() == 3
        
        # Should have 4 log entries
        assert core.database.get_log_count() == 4
        
        # Fourth entry should reuse first food
        assert results[3]['food_id'] == results[0]['food_id']
        assert results[3]['is_new_food'] is False
    
    @pytest.mark.parametrize("description,expected_grams,expected_servings", [
        ("100g of chicken breast", 100.0, 1.0),
        ("3.5 oz of chicken breast", 99.225, 0.99),  # 3.5 * 28.35
        ("0.22 lb of chicken breast", 99.79, 1.0),   # 0.22 * 453.59
    ])
    def test_unit_conversions_workflow(self, core, description, expected_grams, expected_servings):
        """Test workflow with various unit conversions"""
        result = core.process_food_entry(description)
        assert result['success'] is True
        
        nutrition = result['nutrition']
        assert abs(nutrition.actual_grams - expected_grams) < 1.0
        assert abs(nutrition.servings - expected_servings) < 0.1
