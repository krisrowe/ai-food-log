"""
AI Food Logger Package
"""

from .core import FoodLoggerCore, FoodData, NutritionCalculation, ConsumptionEntry
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
