#!/usr/bin/env python3
"""
Core Food Logger Service

Handles all business logic for food analysis, calculations, logging, and output.
Can be used by CLI, web API, or any other interface.

New Architecture:
- Gemini returns standard serving info + user consumed amount separately
- Service performs unit conversions and scaling calculations
- All math done in-memory, no file-based intermediate storage
"""

import csv
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from .gemini_client import GeminiClient


@dataclass
class ProcessedFood:
    """A food item with calculated nutrition based on user's consumed amount"""
    food_name: str
    standard_serving: Dict[str, Any]  # Standard serving info from Gemini
    user_consumed: Dict[str, Any]     # What user actually ate
    calculated_nutrition: Dict[str, float]  # Scaled nutrition for user's amount
    scaling_factor: float             # How much user ate vs standard serving
    confidence_score: float
    source_notes: str


@dataclass
class MealAnalysis:
    """Results of a complete meal analysis with proper conversions"""
    processed_foods: List[ProcessedFood]
    total_calories: float
    total_protein: float
    total_carbs: float
    total_fat: float
    total_fiber: float
    total_sugar: float
    total_sodium: float
    total_potassium: float
    total_vitamin_c: float
    total_calcium: float
    total_iron: float
    avg_confidence: float
    timestamp: datetime


class FoodLoggerService:
    """Core service for food logging operations with proper unit conversions"""
    
    # Unit conversion factors to grams/ml
    UNIT_CONVERSIONS = {
        # Weight units to grams
        'g': 1.0,
        'kg': 1000.0,
        'oz': 28.35,
        'lb': 453.59,
        
        # Volume units to ml (approximate for common foods)
        'ml': 1.0,
        'l': 1000.0,
        'cup': 240.0,  # US cup
        'tbsp': 15.0,
        'tsp': 5.0,
        
        # Count units (no conversion, use as-is)
        'piece': 1.0,
        'slice': 1.0,
        'medium': 1.0,
        'large': 1.0,
        'small': 1.0,
        'scoop': 1.0
    }
    
    def __init__(self, gemini_client: Optional[GeminiClient] = None):
        """Initialize with optional Gemini client (for testing)"""
        self.gemini_client = gemini_client or GeminiClient()
    
    def calculate_scaling_factor(self, standard_serving: Dict[str, Any], user_consumed: Dict[str, Any]) -> float:
        """Calculate how much the user consumed relative to the standard serving"""
        try:
            standard_amount = standard_serving['amount']
            standard_unit = standard_serving['unit']
            user_amount = user_consumed['amount']
            user_unit = user_consumed['unit']
            
            # Convert both to common units if possible
            if standard_unit in self.UNIT_CONVERSIONS and user_unit in self.UNIT_CONVERSIONS:
                # Convert to base units (grams or ml)
                standard_base = standard_amount * self.UNIT_CONVERSIONS[standard_unit]
                user_base = user_amount * self.UNIT_CONVERSIONS[user_unit]
                
                if standard_base > 0:
                    return user_base / standard_base
                else:
                    return 1.0  # Fallback
            
            # For count-based units, direct comparison
            elif standard_unit == user_unit:
                if standard_amount > 0:
                    return user_amount / standard_amount
                else:
                    return 1.0  # Fallback
            
            # If units don't match and can't convert, assume 1:1
            else:
                print(f"Warning: Cannot convert {user_unit} to {standard_unit}, assuming 1:1 ratio")
                return user_amount / standard_amount if standard_amount > 0 else 1.0
                
        except (KeyError, ValueError, ZeroDivisionError) as e:
            print(f"Warning: Error calculating scaling factor: {e}")
            return 1.0  # Safe fallback
    
    def scale_nutrition(self, standard_serving: Dict[str, Any], scaling_factor: float) -> Dict[str, float]:
        """Scale nutrition values based on scaling factor"""
        nutrition_keys = ['calories', 'protein_g', 'carbs_g', 'fat_g', 'fiber_g', 'sugar_g', 
                         'sodium_mg', 'potassium_mg', 'vitamin_c_mg', 'calcium_mg', 'iron_mg']
        
        scaled_nutrition = {}
        for key in nutrition_keys:
            base_value = standard_serving.get(key, 0)
            scaled_nutrition[key] = base_value * scaling_factor
            
        return scaled_nutrition
    
    def process_raw_foods(self, raw_foods: List[Dict[str, Any]]) -> List[ProcessedFood]:
        """Process raw Gemini response into ProcessedFood objects with calculations"""
        processed_foods = []
        
        for raw_food in raw_foods:
            try:
                standard_serving = raw_food['standard_serving']
                user_consumed = raw_food['user_consumed']
                
                # Calculate scaling factor
                scaling_factor = self.calculate_scaling_factor(standard_serving, user_consumed)
                
                # Scale nutrition based on user's consumed amount
                calculated_nutrition = self.scale_nutrition(standard_serving, scaling_factor)
                
                # Create processed food object
                processed_food = ProcessedFood(
                    food_name=raw_food['food_name'],
                    standard_serving=standard_serving,
                    user_consumed=user_consumed,
                    calculated_nutrition=calculated_nutrition,
                    scaling_factor=scaling_factor,
                    confidence_score=raw_food['confidence_score'],
                    source_notes=raw_food['source_notes']
                )
                
                processed_foods.append(processed_food)
                
            except (KeyError, ValueError) as e:
                print(f"Warning: Error processing food {raw_food.get('food_name', 'unknown')}: {e}")
                continue
                
        return processed_foods
    
    def analyze_meal(self, food_description: str) -> Optional[MealAnalysis]:
        """Analyze a food description and return complete meal analysis with proper conversions"""
        try:
            # Get raw analysis from Gemini
            raw_foods = self.gemini_client.analyze_food(food_description)
            if not raw_foods:
                return None
            
            # Process raw foods into calculated nutrition
            processed_foods = self.process_raw_foods(raw_foods)
            if not processed_foods:
                return None
            
            # Calculate totals from processed foods
            totals = {
                'calories': 0, 'protein_g': 0, 'carbs_g': 0, 'fat_g': 0,
                'fiber_g': 0, 'sugar_g': 0, 'sodium_mg': 0, 'potassium_mg': 0,
                'vitamin_c_mg': 0, 'calcium_mg': 0, 'iron_mg': 0
            }
            
            confidence_scores = []
            
            for food in processed_foods:
                nutrition = food.calculated_nutrition
                for key in totals:
                    totals[key] += nutrition.get(key, 0)
                confidence_scores.append(food.confidence_score)
            
            avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
            
            return MealAnalysis(
                processed_foods=processed_foods,
                total_calories=totals['calories'],
                total_protein=totals['protein_g'],
                total_carbs=totals['carbs_g'],
                total_fat=totals['fat_g'],
                total_fiber=totals['fiber_g'],
                total_sugar=totals['sugar_g'],
                total_sodium=totals['sodium_mg'],
                total_potassium=totals['potassium_mg'],
                total_vitamin_c=totals['vitamin_c_mg'],
                total_calcium=totals['calcium_mg'],
                total_iron=totals['iron_mg'],
                avg_confidence=avg_confidence,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            print(f"Error analyzing meal: {e}")
            return None
    
    def process_meal(self, food_description: str, export_csv: bool = True, log_sheets: bool = False) -> Optional[MealAnalysis]:
        """Main entry point - analyze meal and handle all outputs"""
        analysis = self.analyze_meal(food_description)
        if not analysis:
            return None
        
        # Export to CSV if requested
        if export_csv:
            self.export_to_csv(analysis)
        
        # Log to Google Sheets if requested
        if log_sheets:
            self.log_to_sheets(analysis)
        
        return analysis
    
    def export_to_csv(self, analysis: MealAnalysis, filename: str = 'meal_analysis.csv') -> None:
        """Export meal analysis to CSV file"""
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write header
                writer.writerow([
                    'Food Name', 'User Consumed', 'Standard Serving', 'Scaling Factor',
                    'Calories', 'Protein (g)', 'Carbs (g)', 'Fat (g)', 'Fiber (g)', 'Sugar (g)',
                    'Sodium (mg)', 'Potassium (mg)', 'Vitamin C (mg)', 'Calcium (mg)', 'Iron (mg)',
                    'Confidence', 'Source Notes'
                ])
                
                # Write food data
                for food in analysis.processed_foods:
                    user_desc = f"{food.user_consumed['amount']} {food.user_consumed['unit']}"
                    standard_desc = f"{food.standard_serving['amount']} {food.standard_serving['unit']}"
                    
                    writer.writerow([
                        food.food_name,
                        user_desc,
                        standard_desc,
                        f"{food.scaling_factor:.2f}x",
                        f"{food.calculated_nutrition['calories']:.1f}",
                        f"{food.calculated_nutrition['protein_g']:.1f}",
                        f"{food.calculated_nutrition['carbs_g']:.1f}",
                        f"{food.calculated_nutrition['fat_g']:.1f}",
                        f"{food.calculated_nutrition['fiber_g']:.1f}",
                        f"{food.calculated_nutrition['sugar_g']:.1f}",
                        f"{food.calculated_nutrition['sodium_mg']:.1f}",
                        f"{food.calculated_nutrition['potassium_mg']:.1f}",
                        f"{food.calculated_nutrition['vitamin_c_mg']:.1f}",
                        f"{food.calculated_nutrition['calcium_mg']:.1f}",
                        f"{food.calculated_nutrition['iron_mg']:.1f}",
                        f"{food.confidence_score}/10",
                        food.source_notes
                    ])
                
                # Write totals row
                writer.writerow([
                    'TOTALS', '', '', '',
                    f"{analysis.total_calories:.1f}",
                    f"{analysis.total_protein:.1f}",
                    f"{analysis.total_carbs:.1f}",
                    f"{analysis.total_fat:.1f}",
                    f"{analysis.total_fiber:.1f}",
                    f"{analysis.total_sugar:.1f}",
                    f"{analysis.total_sodium:.1f}",
                    f"{analysis.total_potassium:.1f}",
                    f"{analysis.total_vitamin_c:.1f}",
                    f"{analysis.total_calcium:.1f}",
                    f"{analysis.total_iron:.1f}",
                    f"{analysis.avg_confidence:.1f}/10",
                    f"Analysis completed at {analysis.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
                ])
                
            print(f"📊 Exported meal analysis to {filename}")
            
        except Exception as e:
            print(f"Warning: Failed to export CSV: {e}")
    
    def log_to_sheets(self, analysis: MealAnalysis) -> None:
        """Log meal analysis to Google Sheets (placeholder)"""
        # TODO: Implement Google Sheets integration
        print("📝 Google Sheets logging not yet implemented")
    
    def format_console_output(self, analysis: MealAnalysis) -> str:
        """Format analysis results for console display"""
        output = []
        output.append(f"\n✅ Successfully analyzed {len(analysis.processed_foods)} food(s):")
        output.append("=" * 80)
        
        for i, food in enumerate(analysis.processed_foods, 1):
            output.append(f"\n{i}. {food.food_name}")
            output.append(f"   User consumed: {food.user_consumed['amount']} {food.user_consumed['unit']}")
            output.append(f"   Standard serving: {food.standard_serving['amount']} {food.standard_serving['unit']}")
            output.append(f"   Scaling factor: {food.scaling_factor:.2f}x")
            
            nutrition = food.calculated_nutrition
            output.append(f"   Calories: {nutrition['calories']:.1f}")
            output.append(f"   Protein: {nutrition['protein_g']:.1f}g | Carbs: {nutrition['carbs_g']:.1f}g | Fat: {nutrition['fat_g']:.1f}g")
            output.append(f"   Confidence: {food.confidence_score}/10")
            if food.source_notes:
                output.append(f"   Notes: {food.source_notes}")
        
        if len(analysis.processed_foods) > 1:
            output.append("\n" + "=" * 80)
            output.append(f"TOTALS: {analysis.total_calories:.0f} cal | {analysis.total_protein:.1f}g protein | {analysis.total_carbs:.1f}g carbs | {analysis.total_fat:.1f}g fat")
            output.append(f"Average confidence: {analysis.avg_confidence:.1f}/10")
        
        output.append("\n📊 Meal analysis exported to meal_analysis.csv")
        
        return "\n".join(output)
    
    def calculate_scaling_factor(self, standard_serving: Dict[str, Any], user_consumed: Dict[str, Any]) -> float:
        """Calculate how much the user consumed relative to the standard serving"""
        try:
            standard_amount = standard_serving['amount']
            standard_unit = standard_serving['unit']
            user_amount = user_consumed['amount']
            user_unit = user_consumed['unit']
            
            # Convert both to common units if possible
            if standard_unit in self.UNIT_CONVERSIONS and user_unit in self.UNIT_CONVERSIONS:
                # Convert to base units (grams or ml)
                standard_base = standard_amount * self.UNIT_CONVERSIONS[standard_unit]
                user_base = user_amount * self.UNIT_CONVERSIONS[user_unit]
                
                if standard_base > 0:
                    return user_base / standard_base
                else:
                    return 1.0  # Fallback
            
            # For count-based units, direct comparison
            elif standard_unit == user_unit:
                if standard_amount > 0:
                    return user_amount / standard_amount
                else:
                    return 1.0  # Fallback
            
            # If units don't match and can't convert, assume 1:1
            else:
                print(f"Warning: Cannot convert {user_unit} to {standard_unit}, assuming 1:1 ratio")
                return user_amount / standard_amount if standard_amount > 0 else 1.0
                
        except (KeyError, ValueError, ZeroDivisionError) as e:
            print(f"Warning: Error calculating scaling factor: {e}")
            return 1.0  # Safe fallback
    
    def scale_nutrition(self, standard_serving: Dict[str, Any], scaling_factor: float) -> Dict[str, float]:
        """Scale nutrition values based on scaling factor"""
        nutrition_keys = ['calories', 'protein_g', 'carbs_g', 'fat_g', 'fiber_g', 'sugar_g', 
                         'sodium_mg', 'potassium_mg', 'vitamin_c_mg', 'calcium_mg', 'iron_mg']
        
        scaled_nutrition = {}
        for key in nutrition_keys:
            base_value = standard_serving.get(key, 0)
            scaled_nutrition[key] = base_value * scaling_factor
            
        return scaled_nutrition
    
    def process_raw_foods(self, raw_foods: List[Dict[str, Any]]) -> List[ProcessedFood]:
        """Process raw Gemini response into ProcessedFood objects with calculations"""
        processed_foods = []
        
        for raw_food in raw_foods:
            try:
                standard_serving = raw_food['standard_serving']
                user_consumed = raw_food['user_consumed']
                
                # Calculate scaling factor
                scaling_factor = self.calculate_scaling_factor(standard_serving, user_consumed)
                
                # Scale nutrition based on user's consumed amount
                calculated_nutrition = self.scale_nutrition(standard_serving, scaling_factor)
                
                # Create processed food object
                processed_food = ProcessedFood(
                    food_name=raw_food['food_name'],
                    standard_serving=standard_serving,
                    user_consumed=user_consumed,
                    calculated_nutrition=calculated_nutrition,
                    scaling_factor=scaling_factor,
                    confidence_score=raw_food['confidence_score'],
                    source_notes=raw_food['source_notes']
                )
                
                processed_foods.append(processed_food)
                
            except (KeyError, ValueError) as e:
                print(f"Warning: Error processing food {raw_food.get('food_name', 'unknown')}: {e}")
                continue
                
        return processed_foods
    
    def analyze_meal(self, food_description: str) -> Optional[MealAnalysis]:
        """Analyze a food description and return complete meal analysis with proper conversions"""
        try:
            # Get raw analysis from Gemini
            raw_foods = self.gemini_client.analyze_food(food_description)
            if not raw_foods:
                return None
            
            # Process raw foods into calculated nutrition
            processed_foods = self.process_raw_foods(raw_foods)
            if not processed_foods:
                return None
            
            # Calculate totals from processed foods
            totals = {
                'calories': 0, 'protein_g': 0, 'carbs_g': 0, 'fat_g': 0,
                'fiber_g': 0, 'sugar_g': 0, 'sodium_mg': 0, 'potassium_mg': 0,
                'vitamin_c_mg': 0, 'calcium_mg': 0, 'iron_mg': 0
            }
            
            confidence_scores = []
            
            for food in processed_foods:
                nutrition = food.calculated_nutrition
                for key in totals:
                    totals[key] += nutrition.get(key, 0)
                confidence_scores.append(food.confidence_score)
            
            avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
            
            return MealAnalysis(
                processed_foods=processed_foods,
                total_calories=totals['calories'],
                total_protein=totals['protein_g'],
                total_carbs=totals['carbs_g'],
                total_fat=totals['fat_g'],
                total_fiber=totals['fiber_g'],
                total_sugar=totals['sugar_g'],
                total_sodium=totals['sodium_mg'],
                total_potassium=totals['potassium_mg'],
                total_vitamin_c=totals['vitamin_c_mg'],
                total_calcium=totals['calcium_mg'],
                total_iron=totals['iron_mg'],
                avg_confidence=avg_confidence,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            print(f"Error analyzing meal: {e}")
            return None

