"""
AI Food Logger Package
"""

# Legacy imports removed - using new food_logger_service architecture
from .gemini_client import GeminiClient
from .sheets_client import SheetsClient

__version__ = "0.1.0"
__all__ = [
    "FoodLoggerCore",
    "FoodData", 
    "NutritionCalculation",
    "ConsumptionEntry",
    "GeminiClient",
    "SheetsClient"
]
