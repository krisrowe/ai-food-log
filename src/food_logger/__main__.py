#!/usr/bin/env python3
"""
Main entry point for food_logger module
Allows running: python -m src.food_logger "food description"
"""

import sys
import yaml
from .food_logger_service import FoodLoggerService

def format_console_output(result: FinalResult) -> str:
    """Format analysis results for console display"""
    analysis = result.analysis
    output = []
    output.append(f"\n✅ Successfully analyzed {len(analysis.processed_foods)} food(s):")
    output.append("=" * 80)
    
    for i, food in enumerate(analysis.processed_foods, 1):
        output.append(f"\n{i}. {food.food_name}")
        output.append(f"   Input: \"{food.user_description}\"")
        # Note: Accessing nested dictionary-like structures from the model
        output.append(f"   User consumed: {food.consumed.size.amount} {food.consumed.size.unit}")
        output.append(f"   Standard serving: {food.standard_serving.size.amount} {food.standard_serving.size.unit}")
        output.append(f"   Number of servings: {food.consumed.standard_servings:.2f}")
        
        nutrition = food.consumed.nutrition
        output.append(f"   Calories: {nutrition.calories:.1f}")
        output.append(f"   Protein: {nutrition.protein:.1f}g | Carbs: {nutrition.carbs:.1f}g | Fat: {nutrition.fat:.1f}g")
        output.append(f"   Confidence: {food.confidence_score}/10")
        if food.source_notes:
            output.append(f"   Notes: {food.source_notes}")
    
    if len(analysis.processed_foods) > 1:
        totals = analysis.totals
        output.append("\n" + "=" * 80)
        output.append(f"TOTALS: {totals.calories:.0f} cal | {totals.protein:.1f}g protein | {totals.carbs:.1f}g carbs | {totals.fat:.1f}g fat")
        output.append(f"Average confidence: {result.avg_confidence:.1f}/10")
    
    return "\n".join(output)

def main():
    """Thin CLI interface - delegates all business logic to FoodLoggerService"""
    # Load configuration
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    output_method = config.get('output_method', 'csv')

    # Parse command line arguments
    if len(sys.argv) < 2:
        print("Usage: python -m src.food_logger 'food description'")
        print("Example: python -m src.food_logger '160g grilled chicken breast'")
        return 1
    
    food_description = sys.argv[1]
    
    # Delegate to core service
    try:
        service = FoodLoggerService()
        result = service.process_meal(food_description, output_method=output_method)
        
        if result:
            # Display results (formatting handled by CLI)
            print(format_console_output(result))
            print(f"\n✅ Successfully wrote output via {output_method} writer.")
            return 0
        else:
            print("❌ Failed to analyze meal")
            return 1
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
