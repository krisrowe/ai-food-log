#!/usr/bin/env python3
"""
Simple integration tests for the new array API response format
"""

import os
import sys
import pytest

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from food_logger.gemini_client import GeminiClient
from food_logger.food_logger_service import FoodLoggerService


class TestSimpleIntegration:
    """Simple integration tests that work with the new architecture"""
    
    @pytest.fixture
    def gemini_client(self):
        """Create GeminiClient for testing"""
        if not os.getenv('GOOGLE_API_KEY'):
            pytest.skip("GOOGLE_API_KEY not available - skipping Gemini integration tests")
        return GeminiClient()
    
    @pytest.fixture 
    def food_service(self):
        """Create FoodLoggerService for testing"""
        if not os.getenv('GOOGLE_API_KEY'):
            pytest.skip("GOOGLE_API_KEY not available - skipping integration tests")
        return FoodLoggerService()
    
    def test_single_food_analysis(self, gemini_client):
        """Test analyzing a single food item"""
        result = gemini_client.analyze_food("100g grilled chicken breast")
        
        # Should return array of foods
        assert result is not None, "Should return result"
        assert isinstance(result, list), "Should return array"
        assert len(result) == 1, "Should return one food"
        
        food = result[0]
        assert 'food_name' in food, "Should have food_name"
        assert 'standard_serving' in food, "Should have standard_serving"
        assert 'user_consumed' in food, "Should have user_consumed"
        assert 'confidence_score' in food, "Should have confidence_score"
        
        # Check food identification
        assert 'chicken' in food['food_name'].lower(), f"Should identify chicken: {food['food_name']}"
        
        # Check confidence
        assert food['confidence_score'] >= 5, f"Should have reasonable confidence: {food['confidence_score']}"
    
    def test_multi_food_analysis(self, gemini_client):
        """Test analyzing multiple foods"""
        result = gemini_client.analyze_food("1 banana and 1 apple")
        
        # Should return array of foods
        assert result is not None, "Should return result"
        assert isinstance(result, list), "Should return array"
        assert len(result) == 2, "Should return two foods"
        
        food_names = [food['food_name'].lower() for food in result]
        assert any('banana' in name for name in food_names), "Should identify banana"
        assert any('apple' in name for name in food_names), "Should identify apple"
    
    def test_food_service_integration(self, food_service):
        """Test the complete food service workflow"""
        result = food_service.analyze_meal("160g grilled salmon")
        
        assert result is not None, "Should return analysis"
        assert len(result.processed_foods) == 1, "Should process one food"
        
        food = result.processed_foods[0]
        assert 'salmon' in food.food_name.lower(), f"Should identify salmon: {food.food_name}"
        assert food.scaling_factor > 0, "Should have positive scaling factor"
        assert result.total_calories > 0, "Should have positive calories"
        assert result.total_protein > 0, "Should have positive protein"
    
    def test_csv_export_integration(self, food_service):
        """Test CSV export functionality"""
        result = food_service.process_meal("100g chicken breast", export_csv=True)
        
        assert result is not None, "Should return result"
        assert os.path.exists('meal_analysis.csv'), "Should create CSV file"
        
        # Check CSV content
        with open('meal_analysis.csv', 'r') as f:
            content = f.read()
            assert 'chicken' in content.lower(), "CSV should contain chicken"
            assert 'TOTALS' in content, "CSV should have totals row"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
