#!/usr/bin/env python3
"""
Unit Tests for Food Logger Core Logic
Tests all business logic independently of API implementations.
"""

import unittest
from unittest.mock import Mock, patch
from food_logger_core import (
    FoodData, NutritionCalculation, ConsumptionEntry,
    UnitConverter, NutritionCalculator, FoodLoggerCore,
    MockFoodAnalyzer, MockFoodDatabase
)


class TestFoodData(unittest.TestCase):
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
        
        self.assertEqual(food.food_name, "Test Food")
        self.assertEqual(food.serving_size_grams, 100.0)
        self.assertEqual(food.calories_per_serving, 200.0)
        self.assertEqual(food.confidence, "medium")  # default value


class TestUnitConverter(unittest.TestCase):
    """Test unit conversion functionality"""
    
    def test_grams_conversion(self):
        """Test converting grams (should be no change)"""
        result = UnitConverter.to_grams(100, "g")
        self.assertEqual(result, 100.0)
        
        result = UnitConverter.to_grams(150, "grams")
        self.assertEqual(result, 150.0)
    
    def test_ounces_conversion(self):
        """Test converting ounces to grams"""
        result = UnitConverter.to_grams(1, "oz")
        self.assertAlmostEqual(result, 28.35, places=2)
        
        result = UnitConverter.to_grams(2, "ounces")
        self.assertAlmostEqual(result, 56.7, places=1)
    
    def test_pounds_conversion(self):
        """Test converting pounds to grams"""
        result = UnitConverter.to_grams(1, "lb")
        self.assertAlmostEqual(result, 453.59, places=2)
    
    def test_kilograms_conversion(self):
        """Test converting kilograms to grams"""
        result = UnitConverter.to_grams(1, "kg")
        self.assertEqual(result, 1000.0)
    
    def test_unknown_unit(self):
        """Test handling unknown units (should assume grams)"""
        result = UnitConverter.to_grams(100, "unknown_unit")
        self.assertEqual(result, 100.0)
    
    def test_extract_amount_and_unit(self):
        """Test extracting amount and unit from descriptions"""
        result = UnitConverter.extract_amount_and_unit("150g of chicken")
        self.assertEqual(result, (150.0, "g"))
        
        result = UnitConverter.extract_amount_and_unit("2.5 oz salmon")
        self.assertEqual(result, (2.5, "oz"))
        
        result = UnitConverter.extract_amount_and_unit("1 cup rice")
        self.assertEqual(result, (1.0, "cup"))
        
        result = UnitConverter.extract_amount_and_unit("just some food")
        self.assertIsNone(result)


class TestNutritionCalculator(unittest.TestCase):
    """Test nutrition calculation logic"""
    
    def setUp(self):
        """Set up test data"""
        self.food_data = FoodData(
            food_name="Test Food",
            serving_size="100g",
            serving_size_grams=100.0,
            calories_per_serving=200.0,
            protein_g=20.0,
            carbs_g=30.0,
            fat_g=10.0,
            fiber_g=5.0
        )
    
    def test_calculate_exact_serving(self):
        """Test calculation for exact serving size"""
        result = NutritionCalculator.calculate_nutrition(
            self.food_data, "100g of test food"
        )
        
        self.assertEqual(result.servings, 1.0)
        self.assertEqual(result.actual_grams, 100.0)
        self.assertEqual(result.calories, 200.0)
        self.assertEqual(result.protein_g, 20.0)
    
    def test_calculate_double_serving(self):
        """Test calculation for double serving size"""
        result = NutritionCalculator.calculate_nutrition(
            self.food_data, "200g of test food"
        )
        
        self.assertEqual(result.servings, 2.0)
        self.assertEqual(result.actual_grams, 200.0)
        self.assertEqual(result.calories, 400.0)
        self.assertEqual(result.protein_g, 40.0)
    
    def test_calculate_half_serving(self):
        """Test calculation for half serving size"""
        result = NutritionCalculator.calculate_nutrition(
            self.food_data, "50g of test food"
        )
        
        self.assertEqual(result.servings, 0.5)
        self.assertEqual(result.actual_grams, 50.0)
        self.assertEqual(result.calories, 100.0)
        self.assertEqual(result.protein_g, 10.0)
    
    def test_calculate_with_ounces(self):
        """Test calculation with ounce input"""
        # 1 oz = 28.35g, so for 100g serving, 1 oz = 0.2835 servings
        result = NutritionCalculator.calculate_nutrition(
            self.food_data, "1 oz of test food"
        )
        
        self.assertAlmostEqual(result.servings, 0.28, places=1)
        self.assertAlmostEqual(result.actual_grams, 28.35, places=1)
        self.assertAlmostEqual(result.calories, 56.7, places=0)
    
    def test_calculate_no_amount(self):
        """Test calculation when no amount is specified (assume 1 serving)"""
        result = NutritionCalculator.calculate_nutrition(
            self.food_data, "some test food"
        )
        
        self.assertEqual(result.servings, 1.0)
        self.assertEqual(result.actual_grams, 100.0)
        self.assertEqual(result.calories, 200.0)


class TestMockFoodAnalyzer(unittest.TestCase):
    """Test mock food analyzer"""
    
    def setUp(self):
        self.analyzer = MockFoodAnalyzer()
    
    def test_analyze_chicken_breast(self):
        """Test analyzing chicken breast"""
        result = self.analyzer.analyze_food("grilled chicken breast")
        
        self.assertIsNotNone(result)
        self.assertEqual(result.food_name, "Grilled Chicken Breast")
        self.assertEqual(result.serving_size_grams, 100)
        self.assertGreater(result.protein_g, 25)  # Chicken is high protein
        self.assertEqual(result.carbs_g, 0.0)  # Chicken has no carbs
    
    def test_analyze_brown_rice(self):
        """Test analyzing brown rice"""
        result = self.analyzer.analyze_food("brown rice")
        
        self.assertIsNotNone(result)
        self.assertEqual(result.food_name, "Brown Rice (cooked)")
        self.assertGreater(result.carbs_g, 40)  # Rice is high carb
        self.assertGreater(result.fiber_g, 3)  # Brown rice has fiber
    
    def test_analyze_unknown_food(self):
        """Test analyzing unknown food (should return generic)"""
        result = self.analyzer.analyze_food("some unknown exotic food")
        
        self.assertIsNotNone(result)
        self.assertEqual(result.food_name, "Unknown Food Item")
        self.assertEqual(result.confidence, "low")


class TestMockFoodDatabase(unittest.TestCase):
    """Test mock food database"""
    
    def setUp(self):
        self.database = MockFoodDatabase()
        self.food_data = FoodData(
            food_name="Test Food",
            serving_size="100g",
            serving_size_grams=100.0,
            calories_per_serving=200.0,
            protein_g=20.0,
            carbs_g=30.0,
            fat_g=10.0,
            fiber_g=5.0
        )
    
    def test_save_and_find_food(self):
        """Test saving and finding food"""
        # Initially should not find the food
        result = self.database.find_food("Test Food")
        self.assertIsNone(result)
        
        # Save the food
        food_id = self.database.save_food(self.food_data)
        self.assertIsNotNone(food_id)
        self.assertTrue(food_id.startswith("food_"))
        
        # Now should find the food
        result = self.database.find_food("Test Food")
        self.assertIsNotNone(result)
        found_id, found_data = result
        self.assertEqual(found_id, food_id)
        self.assertEqual(found_data.food_name, "Test Food")
    
    def test_case_insensitive_search(self):
        """Test that food search is case insensitive"""
        food_id = self.database.save_food(self.food_data)
        
        # Should find with different cases
        result = self.database.find_food("test food")
        self.assertIsNotNone(result)
        
        result = self.database.find_food("TEST FOOD")
        self.assertIsNotNone(result)
    
    def test_log_consumption(self):
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
        
        initial_count = self.database.get_log_count()
        self.database.log_consumption(entry)
        
        self.assertEqual(self.database.get_log_count(), initial_count + 1)


class TestFoodLoggerCore(unittest.TestCase):
    """Test the core food logger logic"""
    
    def setUp(self):
        self.analyzer = MockFoodAnalyzer()
        self.database = MockFoodDatabase()
        self.core = FoodLoggerCore(self.analyzer, self.database)
    
    def test_process_new_food_entry(self):
        """Test processing a new food entry"""
        result = self.core.process_food_entry("150g of grilled chicken breast")
        
        self.assertTrue(result['success'])
        self.assertIsNotNone(result['food_data'])
        self.assertIsNotNone(result['nutrition'])
        self.assertIsNotNone(result['food_id'])
        self.assertTrue(result['is_new_food'])
        
        # Check nutrition calculation
        nutrition = result['nutrition']
        self.assertEqual(nutrition.actual_grams, 150.0)
        self.assertEqual(nutrition.servings, 1.5)  # 150g / 100g serving
        
        # Check database was updated
        self.assertEqual(self.database.get_foods_count(), 1)
        self.assertEqual(self.database.get_log_count(), 1)
    
    def test_process_existing_food_entry(self):
        """Test processing an existing food entry"""
        # First entry - should be new
        result1 = self.core.process_food_entry("100g of grilled chicken breast")
        self.assertTrue(result1['is_new_food'])
        
        # Second entry - should use existing
        result2 = self.core.process_food_entry("200g of grilled chicken breast")
        self.assertFalse(result2['is_new_food'])
        self.assertEqual(result2['food_id'], result1['food_id'])
        
        # Should have 1 food, 2 log entries
        self.assertEqual(self.database.get_foods_count(), 1)
        self.assertEqual(self.database.get_log_count(), 2)
    
    def test_process_analyzer_failure(self):
        """Test handling analyzer failure"""
        # Mock analyzer to return None
        mock_analyzer = Mock()
        mock_analyzer.analyze_food.return_value = None
        
        core = FoodLoggerCore(mock_analyzer, self.database)
        result = core.process_food_entry("some food")
        
        self.assertFalse(result['success'])
        self.assertIsNotNone(result['error'])
        self.assertIn("Failed to analyze", result['error'])
    
    def test_process_database_exception(self):
        """Test handling database exceptions"""
        # Mock database to raise exception
        mock_database = Mock()
        mock_database.find_food.side_effect = Exception("Database error")
        
        core = FoodLoggerCore(self.analyzer, mock_database)
        result = core.process_food_entry("chicken breast")
        
        self.assertFalse(result['success'])
        self.assertIsNotNone(result['error'])
        self.assertIn("Database error", result['error'])


class TestIntegration(unittest.TestCase):
    """Integration tests using mock implementations"""
    
    def test_full_workflow(self):
        """Test complete workflow from input to database storage"""
        core = FoodLoggerCore(MockFoodAnalyzer(), MockFoodDatabase())
        
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
            self.assertTrue(result['success'], f"Failed to process: {food}")
        
        # Should have 3 unique foods (chicken, rice, salmon)
        self.assertEqual(core.database.get_foods_count(), 3)
        
        # Should have 4 log entries
        self.assertEqual(core.database.get_log_count(), 4)
        
        # Fourth entry should reuse first food
        self.assertEqual(results[3]['food_id'], results[0]['food_id'])
        self.assertFalse(results[3]['is_new_food'])
    
    def test_unit_conversions_workflow(self):
        """Test workflow with various unit conversions"""
        core = FoodLoggerCore(MockFoodAnalyzer(), MockFoodDatabase())
        
        # Test different units for the same food
        entries = [
            ("100g of chicken breast", 100.0, 1.0),
            ("3.5 oz of chicken breast", 99.225, 0.99),  # 3.5 * 28.35
            ("0.22 lb of chicken breast", 99.79, 1.0),   # 0.22 * 453.59
        ]
        
        for description, expected_grams, expected_servings in entries:
            result = core.process_food_entry(description)
            self.assertTrue(result['success'])
            
            nutrition = result['nutrition']
            self.assertAlmostEqual(nutrition.actual_grams, expected_grams, places=0)
            self.assertAlmostEqual(nutrition.servings, expected_servings, places=1)


def run_tests():
    """Run all tests and display results"""
    # Create test suite
    test_classes = [
        TestFoodData,
        TestUnitConverter,
        TestNutritionCalculator,
        TestMockFoodAnalyzer,
        TestMockFoodDatabase,
        TestFoodLoggerCore,
        TestIntegration
    ]
    
    suite = unittest.TestSuite()
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print(f"\nFAILURES:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print(f"\nERRORS:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    print(f"\nResult: {'✅ ALL TESTS PASSED' if success else '❌ SOME TESTS FAILED'}")
    
    return success


if __name__ == "__main__":
    run_tests()
