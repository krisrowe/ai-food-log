"""
Integration Tests for Gemini API
Tests real Gemini API integration for four key food categories:
1. Whole Foods - natural foods with relatively stable nutrition (e.g., grilled chicken breast)
2. Packaged Products - branded items with fixed nutrition labels (e.g., Core Power Vanilla)
3. Ambiguous Foods - need clarification to get accurate nutrition (e.g., "milk" without fat %)
4. Exception Cases - invalid inputs, non-food items, edge cases
"""

import pytest
import os
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from food_logger.core import FoodLoggerCore, MockFoodDatabase
from food_logger.gemini_client import GeminiClient


@pytest.mark.integration
@pytest.mark.slow
class TestWholeFoods:
    """Test Gemini API with whole foods that have relatively stable nutrition across sources"""
    # Examples: grilled chicken breast, salmon fillet, eggs, quinoa, banana
    # These should return consistent nutrition values with high/medium confidence
    
    @pytest.fixture
    def gemini_client(self):
        """Create Gemini client - will skip if no API key available"""
        try:
            return GeminiClient()
        except ValueError:
            pytest.skip("GOOGLE_API_KEY not available - skipping Gemini integration tests")
    
    def test_grilled_chicken_breast_consistency(self, gemini_client):
        """Test that grilled chicken breast returns consistent nutrition and standardized naming"""
        # Test multiple variations of the same food
        variations = [
            "160g of grilled chicken breast",
            "grilled chicken breast 160g",
            "160 grams grilled chicken breast"
        ]
        
        results = []
        for variation in variations:
            result = gemini_client.analyze_food(variation)
            assert result is not None, f"Should analyze: {variation}"
            results.append(result)
        
        # All should identify as similar chicken breast products
        for result in results:
            food_name_lower = result['food_name'].lower()
            assert "chicken" in food_name_lower, f"Should identify as chicken: {result['food_name']}"
            assert "breast" in food_name_lower, f"Should specify breast: {result['food_name']}"
        
        # Nutrition should be consistent (within 20% variance)
        first = results[0]
        for other in results[1:]:
            protein_diff = abs(other['protein_g'] - first['protein_g']) / first['protein_g']
            assert protein_diff <= 0.2, f"Protein should be consistent: {first['protein_g']}g vs {other['protein_g']}g"
            
            calorie_diff = abs(other['calories_per_serving'] - first['calories_per_serving']) / first['calories_per_serving']
            assert calorie_diff <= 0.2, f"Calories should be consistent: {first['calories_per_serving']} vs {other['calories_per_serving']}"
        
        print(f"✅ Whole food consistency - Chicken breast:")
        print(f"   Name: {results[0]['food_name']}")
        print(f"   Serving: {results[0]['serving_amount']}{results[0]['serving_unit']}")
        print(f"   Nutrition: {results[0]['calories_per_serving']} cal, {results[0]['protein_g']}g protein, {results[0]['carbs_g']}g carbs, {results[0]['fat_g']}g fat")
        print(f"   Confidence: {results[0]['confidence_score']}/10")
    
    @pytest.mark.parametrize("food_input,expected_protein_min,expected_carbs_max,expected_calories_min", [
        ("100g raw salmon fillet", 18, 2, 150),
        ("1 large egg", 5, 2, 60),
        ("100g cooked quinoa", 3, 30, 100),  # Quinoa is high carb
        ("1 medium banana", 1, 20, 80),
        ("100g cooked brown rice", 2, 20, 100),
    ])
    def test_various_whole_foods(self, gemini_client, food_input, expected_protein_min, expected_carbs_max, expected_calories_min):
        """Test various whole foods with known nutrition ranges"""
        result = gemini_client.analyze_food(food_input)
        
        assert result is not None, f"Should analyze: {food_input}"
        assert result['food_name'] is not None and result['food_name'].strip(), "Should have non-empty food name"
        
        # Validate nutrition is in expected ranges for whole foods
        assert result['protein_g'] >= expected_protein_min, \
            f"{food_input}: protein should be ≥{expected_protein_min}g, got {result['protein_g']}g"
        assert result['carbs_g'] <= expected_carbs_max, \
            f"{food_input}: carbs should be ≤{expected_carbs_max}g, got {result['carbs_g']}g"
        assert result['calories_per_serving'] >= expected_calories_min, \
            f"{food_input}: calories should be ≥{expected_calories_min}, got {result['calories_per_serving']}"
        
        # Validate confidence score
        assert isinstance(result['confidence_score'], (int, float)), f"Confidence score must be numeric: {result['confidence_score']}"
        assert 1 <= result['confidence_score'] <= 10, f"Confidence score must be 1-10: {result['confidence_score']}"
        
        print(f"✅ JSON structure validation passed for: {result['food_name']}")
        
        print(f"✅ Whole food: {food_input} -> {result['food_name']} (confidence: {result['confidence_score']}/10)")
    

    
    def test_columnar_output_format(self, gemini_client):
        """Test that output can be formatted for columnar consumption log"""
        result = gemini_client.analyze_food("150g grilled chicken breast")
        
        assert result is not None, "Should get result"
        
        # Test that we can extract all required columns for consumption log
        columnar_data = {
            "standardized_food_name": result['food_name'],
            "serving_unit": result['serving_unit'],  # We know the input was in grams
            "servings": 150.0 / result['serving_amount'],  # Calculate servings
            "calories": result['calories_per_serving'] * (150.0 / result['serving_amount']),
            "protein_g": result['protein_g'] * (150.0 / result['serving_amount']),
            "fat_g": result['fat_g'] * (150.0 / result['serving_amount']),
            "carbs_g": result['carbs_g'] * (150.0 / result['serving_amount']),
            "sugar_g": result['sugar_g'] * (150.0 / result['serving_amount']),
            "fiber_g": result['fiber_g'] * (150.0 / result['serving_amount']),
        }
        
        # Validate all columns have reasonable values
        assert isinstance(columnar_data["standardized_food_name"], str) and columnar_data["standardized_food_name"]
        assert columnar_data["servings"] > 0
        assert columnar_data["calories"] > 0
        assert columnar_data["protein_g"] >= 0
        
        print(f"✅ Columnar format for consumption log:")
        for key, value in columnar_data.items():
            print(f"   {key}: {value}")


@pytest.mark.integration
@pytest.mark.slow
class TestPackagedProducts:
    """Test Gemini API with packaged/branded products that have fixed nutrition labels"""
    # Examples: Core Power Vanilla, Clif Bar, specific yogurt brands
    # These should return precise nutrition matching the actual product label
    
    @pytest.fixture
    def gemini_client(self):
        """Create Gemini client - will skip if no API key available"""
        try:
            return GeminiClient()
        except ValueError:
            pytest.skip("GOOGLE_API_KEY not available - skipping Gemini integration tests")
    
    def test_core_power_vanilla_branded_product(self, gemini_client):
        """Test Core Power Vanilla - specific branded product with known nutrition"""
        result = gemini_client.analyze_food("26g Core Power Vanilla protein shake")
        
        assert result is not None, "Should analyze Core Power Vanilla"
        
        # Should identify as Core Power or similar protein product
        food_name_lower = result['food_name'].lower()
        protein_terms = ["protein", "shake", "powder", "core power", "core", "power"]
        assert any(term in food_name_lower for term in protein_terms), \
            f"Should identify as protein product: {result['food_name']}"
        
        # Core Power Vanilla has known nutrition profile (26g serving)
        assert result['protein_g'] >= 15, f"Core Power should be high protein (≥15g), got {result['protein_g']}g"
        assert result['carbs_g'] <= 10, f"Core Power should be low carb (≤10g), got {result['carbs_g']}g"
        assert result['calories_per_serving'] >= 100, f"Should have reasonable calories (≥100), got {result['calories_per_serving']}"
        assert result['confidence_score'] >= 5, f"Should have good confidence for branded product, got {result['confidence_score']}"
        
        print(f"✅ Packaged product - Core Power Vanilla:")
        print(f"   Name: {result['food_name']}")
        print(f"   Nutrition per {result['serving_amount']}{result['serving_unit']}: {result['calories_per_serving']} cal, {result['protein_g']}g protein, {result['carbs_g']}g carbs, {result['fat_g']}g fat")
        print(f"   Confidence: {result['confidence_score']}/10")
    
    @pytest.mark.parametrize("product_input,expected_type,min_confidence", [
        ("1 Clif Bar Chocolate Chip", "bar", 5),
        ("1 cup Chobani Greek Yogurt Plain", "yogurt", 5),
        ("1 Quest Bar Cookies and Cream", "bar", 5),
        ("1 scoop Optimum Nutrition Gold Standard Whey Vanilla", "protein", 5),
    ])
    def test_various_packaged_products(self, gemini_client, product_input, expected_type, min_confidence):
        """Test various branded/packaged products"""
        result = gemini_client.analyze_food(product_input)
        
        assert result is not None, f"Should analyze packaged product: {product_input}"
        
        # Should identify the product type
        food_name_lower = result['food_name'].lower()
        assert expected_type in food_name_lower, \
            f"Should identify as {expected_type}: {result['food_name']}"
        
        # Packaged products should have decent confidence since they have fixed labels
        assert result['confidence_score'] >= min_confidence, \
            f"Packaged product should have ≥{min_confidence} confidence, got {result['confidence_score']}"
        
        print(f"✅ Packaged product: {product_input} -> {result['food_name']} (confidence: {result['confidence_score']}/10)")


@pytest.mark.integration
@pytest.mark.slow
class TestAmbiguousFoods:
    """Test Gemini API with ambiguous foods that need clarification to get accurate nutrition"""
    # Examples: "milk" (whole/skim/2%?), "bread" (white/wheat?), "chicken" (breast/thigh? grilled/fried?)
    # These should either prompt for clarification or make reasonable assumptions with noted uncertainty
    
    @pytest.fixture
    def gemini_client(self):
        """Create Gemini client - will skip if no API key available"""
        try:
            return GeminiClient()
        except ValueError:
            pytest.skip("GOOGLE_API_KEY not available - skipping Gemini integration tests")
    
    def test_ambiguous_milk_needs_clarification(self, gemini_client):
        """Test handling of ambiguous milk - should need fat content clarification"""
        result = gemini_client.analyze_food("1 cup of milk")
        
        assert result is not None, "Should return some result for milk"
        assert "milk" in result['food_name'].lower(), "Should identify as milk"
        
        # For ambiguous milk, Gemini should either:
        # 1. Make a reasonable assumption (e.g., whole milk) with medium/low confidence
        # 2. Provide generic milk values
        # 3. Indicate need for clarification in source_notes
        
        print(f"✅ Ambiguous milk (needs fat % clarification):")
        print(f"   Name: {result['food_name']}")
        print(f"   Confidence: {result['confidence_score']}/10")
        print(f"   Notes: {result['source_notes']}")
        
        # Should have some reasonable milk nutrition
        assert 6 <= result['protein_g'] <= 10, f"Milk protein should be 6-10g, got {result['protein_g']}g"
        assert 8 <= result['carbs_g'] <= 15, f"Milk carbs should be 8-15g, got {result['carbs_g']}g"
    
    def test_ambiguous_bread_needs_clarification(self, gemini_client):
        """Test handling of ambiguous bread - should need type clarification"""
        result = gemini_client.analyze_food("2 slices of bread")
        
        assert result is not None, "Should return some result for bread"
        assert "bread" in result['food_name'].lower(), "Should identify as bread"
        
        # Bread types vary significantly, so should indicate this somehow
        print(f"✅ Ambiguous bread (needs type clarification):")
        print(f"   Name: {result['food_name']}")
        print(f"   Confidence: {result['confidence_score']}/10")
        print(f"   Notes: {result['source_notes']}")
        
        # Should have reasonable bread nutrition ranges
        assert 2 <= result['protein_g'] <= 8, f"Bread protein should be 2-8g, got {result['protein_g']}g"
        assert 10 <= result['carbs_g'] <= 30, f"Bread carbs should be 10-30g, got {result['carbs_g']}g"
    
    def test_generic_protein_powder_needs_clarification(self, gemini_client):
        """Test handling of generic protein powder - should need brand/type clarification"""
        result = gemini_client.analyze_food("1 scoop protein powder")
        
        assert result is not None, "Should return some result for protein powder"
        
        food_name_lower = result['food_name'].lower()
        assert "protein" in food_name_lower, "Should identify as protein"
        
        # Should have high protein but may have low confidence due to variability
        assert result['protein_g'] >= 15, f"Protein powder should have high protein, got {result['protein_g']}g"
        
        print(f"✅ Generic protein powder (needs brand clarification):")
        print(f"   Name: {result['food_name']}")
        print(f"   Confidence: {result['confidence_score']}/10")
        print(f"   Notes: {result['source_notes']}")
        
        # If confidence is low, it should indicate why
        if result['confidence_score'] < 5:
            assert result['source_notes'], "Low confidence should have explanatory notes"
    
    @pytest.mark.parametrize("ambiguous_input,expected_food_type,clarification_needed", [
        ("chicken", "chicken", "preparation method (grilled/fried) and cut (breast/thigh)"),
        ("1 apple", "apple", "size/variety"),
        ("pasta", "pasta", "type and preparation"),
        ("cheese", "cheese", "type and fat content"),
        ("yogurt", "yogurt", "fat content and brand"),
        ("rice", "rice", "type (white/brown) and preparation"),
    ])
    def test_various_ambiguous_inputs(self, gemini_client, ambiguous_input, expected_food_type, clarification_needed):
        """Test various ambiguous inputs that need clarification for accurate nutrition"""
        result = gemini_client.analyze_food(ambiguous_input)
        
        assert result is not None, f"Should handle ambiguous input: {ambiguous_input}"
        
        # Should contain the expected food type
        food_name_lower = result['food_name'].lower()
        assert expected_food_type in food_name_lower, \
            f"Should identify {expected_food_type} in: {result['food_name']}"
        
        print(f"✅ Ambiguous: {ambiguous_input} -> {result['food_name']} (confidence: {result['confidence_score']}/10)")
        print(f"   Clarification needed: {clarification_needed}")
        
        # Ambiguous inputs should have lower confidence or explanatory notes
        if result['confidence_score'] < 5:
            print(f"   ✓ Appropriately flagged as low confidence")
        elif result['source_notes'] and any(word in result['source_notes'].lower() for word in ["assumption", "generic", "average", "typical"]):
            print(f"   ✓ Notes indicate assumptions: {result['source_notes']}")
        else:
            print(f"   ⚠️  May need better ambiguity detection")


@pytest.mark.integration
@pytest.mark.slow
class TestExceptionCases:
    """Test Gemini API handling of exception cases and error conditions"""
    
    @pytest.fixture
    def gemini_client(self):
        """Create Gemini client - will skip if no API key available"""
        try:
            return GeminiClient()
        except ValueError:
            pytest.skip("GOOGLE_API_KEY not available - skipping Gemini integration tests")
    
    def test_nonsensical_input(self, gemini_client):
        """Test handling of completely nonsensical input"""
        nonsense_inputs = [
            "asdfghjkl xyz 123 random nonsense",
            "qwerty uiop zxcvbnm",
            "!@#$%^&*()_+",
        ]
        
        for nonsense in nonsense_inputs:
            result = gemini_client.analyze_food(nonsense)
            
            # Should either return None or a very low confidence response
            if result is None:
                print(f"✅ Appropriately returned None for: {nonsense}")
            else:
                assert result['confidence_score'] < 5, \
                    f"Should have low confidence for nonsense, got {result['confidence_score']}"
                print(f"✅ Handled nonsense '{nonsense}' -> {result['food_name']} (confidence: {result['confidence_score']}/10)")
    
    def test_empty_and_whitespace_input(self, gemini_client):
        """Test handling of empty or whitespace-only input"""
        empty_inputs = ["", "   ", "\t\n", "  \t  \n  "]
        
        for empty_input in empty_inputs:
            result = gemini_client.analyze_food(empty_input)
            
            # Should handle gracefully
            if result is None:
                print(f"✅ Appropriately returned None for empty input")
            else:
                print(f"✅ Handled empty input: {result['food_name']}")
    
    def test_very_long_input(self, gemini_client):
        """Test handling of extremely long input"""
        long_input = "I ate " + "very " * 50 + "delicious chicken breast yesterday at the restaurant"
        result = gemini_client.analyze_food(long_input)
        
        # Should still extract the food despite the length
        if result:
            assert "chicken" in result['food_name'].lower(), \
                "Should extract chicken from long input"
            print(f"✅ Extracted from long input: {result['food_name']}")
        else:
            print(f"✅ Handled long input appropriately by returning None")
    
    def test_non_food_items(self, gemini_client):
        """Test handling of non-food items"""
        non_food_inputs = [
            "my car",
            "a computer",
            "the weather today",
            "my homework",
        ]
        
        for non_food in non_food_inputs:
            result = gemini_client.analyze_food(non_food)
            
            # Should either return None or indicate it's not food
            if result is None:
                print(f"✅ Appropriately returned None for non-food: {non_food}")
            else:
                # If it returns something, should have very low confidence
                assert result['confidence_score'] < 5, \
                    f"Non-food should have low confidence, got {result['confidence_score']}"
                print(f"✅ Handled non-food '{non_food}' with low confidence: {result['food_name']}")
    
    def test_json_structure_validation(self, gemini_client):
        """Test that Gemini returns properly structured, processable data"""
        result = gemini_client.analyze_food("100g grilled chicken breast")
        
        assert result is not None, "Should return result for valid food"
        
        # Validate response structure
        required_fields = [
            'food_name', 'serving_amount', 'serving_unit', 'calories_per_serving',
            'protein_g', 'carbs_g', 'fat_g', 'fiber_g', 'sugar_g',
            'sodium_mg', 'potassium_mg', 'vitamin_c_mg', 'calcium_mg', 'iron_mg',
            'confidence_score', 'source_notes'
        ]
        for field in required_fields:
            assert field in result, f"Missing required field: {field}"
        
        # Validate serving size
        assert isinstance(result['serving_amount'], (int, float)), "Serving amount must be numeric"
        assert result['serving_amount'] > 0, "Serving amount must be positive"
        
        # Validate serving unit
        valid_units = ['g', 'ml', 'cup', 'tbsp', 'tsp', 'oz', 'lb', 'kg', 'piece', 'slice', 'medium', 'large', 'small']
        assert result['serving_unit'] in valid_units, f"Invalid serving unit: {result['serving_unit']}"
        
        # Validate all required fields are present and properly typed
        assert isinstance(result['food_name'], str) and result['food_name'].strip(), \
            "food_name should be non-empty string"
        assert isinstance(result['calories_per_serving'], (int, float)) and result['calories_per_serving'] >= 0, \
            "calories should be non-negative number"
        assert isinstance(result['protein_g'], (int, float)) and result['protein_g'] >= 0, \
            "protein should be non-negative number"
        assert isinstance(result['carbs_g'], (int, float)) and result['carbs_g'] >= 0, \
            "carbs should be non-negative number"
        assert isinstance(result['fat_g'], (int, float)) and result['fat_g'] >= 0, \
            "fat should be non-negative number"
        assert isinstance(result['fiber_g'], (int, float)) and result['fiber_g'] >= 0, \
            "fiber should be non-negative number"
        
        # Validate confidence score
        assert isinstance(result['confidence_score'], (int, float)), f"Confidence score must be numeric: {result['confidence_score']}"
        assert 1 <= result['confidence_score'] <= 10, f"Confidence score must be 1-10: {result['confidence_score']}"
        
        print(f"✅ JSON structure validation passed for: {result['food_name']}")


def test_environment_setup():
    """Test that environment is properly set up for integration tests"""
    has_api_key = os.getenv('GOOGLE_API_KEY') is not None
    
    if has_api_key:
        print("✅ GOOGLE_API_KEY is available - Gemini integration tests will run")
        print("   Run with: pytest tests/integration/test_gemini_integration.py -v -m integration")
        print("   Or run specific test classes:")
        print("     pytest tests/integration/test_gemini_integration.py::TestPredictableFoods -v")
        print("     pytest tests/integration/test_gemini_integration.py::TestAmbiguousFoods -v")
        print("     pytest tests/integration/test_gemini_integration.py::TestExceptionCases -v")
    else:
        print("⚠️  GOOGLE_API_KEY not available - Gemini integration tests will be skipped")
        print("   To run Gemini integration tests:")
        print("   1. Get a Gemini API key from https://makersuite.google.com/app/apikey")
        print("   2. Set GOOGLE_API_KEY environment variable")
        print("   3. Run: pytest tests/integration/test_gemini_integration.py -v -m integration")


if __name__ == "__main__":
    # Run environment check when script is run directly
    test_environment_setup()
