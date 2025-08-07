#!/usr/bin/env python3
"""
Core Food Logger Service
"""

from datetime import datetime
from typing import List, Dict, Any, Optional

from .gemini_client import GeminiClient
from .sheets_client import SheetsClient
from .models import (
    ProcessedFood, MealAnalysis, NutritionalInfo, FinalResult, 
    Consumed, StandardServing, ServingSize
)
from .output_writer import OutputWriter, CsvOutputWriter, SheetsOutputWriter

class FoodLoggerService:
    """Core service for food logging operations with proper unit conversions"""
    
    def __init__(self, gemini_client: Optional[GeminiClient] = None):
        self.gemini_client = gemini_client or GeminiClient()
    
    def _calculate_servings(self, std_serv: Dict[str, Any], user_serv: Dict[str, Any], servings_info: Dict[str, Any]) -> float:
        """Calculate the number of standard servings consumed."""
        if not servings_info.get('calculable', False):
            return servings_info.get('guess', 1.0)

        user_size = user_serv['size']
        std_size = std_serv['size']
        alt_size = std_serv.get('alt_size')

        # Prioritize matching the user's unit
        if user_size['unit'] == std_size['unit'] and std_size['amount'] > 0:
            return user_size['amount'] / std_size['amount']
        if alt_size and user_size['unit'] == alt_size['unit'] and alt_size['amount'] > 0:
            return user_size['amount'] / alt_size['amount']
        
        return 1.0 # Fallback

    def _scale_nutrition(self, std_nutr: Dict[str, Any], ratio: float) -> NutritionalInfo:
        """Scale nutrition values based on the serving ratio."""
        return NutritionalInfo(
            calories=std_nutr.get('calories', 0) * ratio,
            protein=std_nutr.get('protein', 0) * ratio,
            carbs=std_nutr.get('carbs', 0) * ratio,
            fat=std_nutr.get('fat', 0) * ratio,
            fiber=std_nutr.get('fiber', 0) * ratio,
            sugar=std_nutr.get('sugar', 0) * ratio,
            sodium=std_nutr.get('sodium', 0) * ratio,
            potassium=std_nutr.get('potassium', 0) * ratio,
            vitamin_c=std_nutr.get('vitamin_c', 0) * ratio,
            calcium=std_nutr.get('calcium', 0) * ratio,
            iron=std_nutr.get('iron', 0) * ratio,
        )

    def analyze_meal_from_data(self, raw_foods: List[Dict[str, Any]]) -> Optional[MealAnalysis]:
        """Pure function to perform calculations on raw food data."""
        if not raw_foods: return None
            
        processed_foods = []
        for raw_food in raw_foods:
            try:
                std_serv_raw = raw_food['standard_serving']
                user_serv_raw = raw_food['consumed']
                std_nutr_raw = std_serv_raw['nutrition']
                servings_info = raw_food['servings']

                standard_servings = self._calculate_servings(std_serv_raw, user_serv_raw, servings_info)
                calculated_nutrition = self._scale_nutrition(std_nutr_raw, standard_servings)
                
                standard_nutrition = NutritionalInfo(**std_nutr_raw)

                standard_serving = StandardServing(
                    size=ServingSize(**std_serv_raw['size']),
                    alt_size=ServingSize(**std_serv_raw['alt_size']) if std_serv_raw.get('alt_size') else None,
                    nutrition=standard_nutrition
                )

                consumed = Consumed(
                    size=ServingSize(**user_serv_raw['size']),
                    standard_servings=standard_servings,
                    nutrition=calculated_nutrition
                )

                processed_foods.append(ProcessedFood(
                    food_name=raw_food['food_name'],
                    standard_serving=standard_serving,
                    consumed=consumed,
                    user_description=raw_food['user_description'],
                    confidence_score=raw_food['confidence_score'],
                    source_notes=raw_food['source_notes']
                ))
            except (KeyError, ValueError) as e:
                print(f"Warning: Error processing food {raw_food.get('food_name', 'unknown')}: {e}")
                continue
        
        if not processed_foods: return None

        totals = NutritionalInfo(calories=0, protein=0, carbs=0, fat=0, fiber=0, sugar=0, sodium=0, potassium=0, vitamin_c=0, calcium=0, iron=0)
        for food in processed_foods:
            nutr = food.consumed.nutrition
            for key in totals.__annotations__:
                setattr(totals, key, getattr(totals, key) + getattr(nutr, key))
            
        return MealAnalysis(processed_foods=processed_foods, totals=totals)

    def process_meal(self, food_description: str, output_method: str) -> Optional[FinalResult]:
        """
        Main entry point: gets data from API, processes it, selects the correct
        output writer, and persists the result.
        """
        try:
            raw_foods = self.gemini_client.analyze_food(food_description)
            if not raw_foods:
                return None
            
            analysis = self.analyze_meal_from_data(raw_foods)
            if not analysis:
                return None

            confidence_scores = [food.confidence_score for food in analysis.processed_foods]
            avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
            
            result = FinalResult(
                analysis=analysis,
                avg_confidence=avg_confidence,
                timestamp=datetime.now()
            )

            # Select and use the appropriate writer
            writer: OutputWriter
            if output_method == 'sheets':
                writer = SheetsOutputWriter(sheets_client=SheetsClient())
            else: # Default to csv
                writer = CsvOutputWriter()
            
            writer.process(result)
            
            return result

        except Exception as e:
            print(f"Error processing meal: {e}")
            return None
