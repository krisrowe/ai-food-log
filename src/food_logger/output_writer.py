"""
Output writers for different formats (CSV, Google Sheets, etc.)
"""

import csv
import os
from abc import ABC, abstractmethod
from typing import List
from .models import FinalResult, MealAnalysis
from .sheets_client import SheetsClient

class OutputWriter(ABC):
    """Abstract base class for output writers."""

    @abstractmethod
    def write_foods(self, result: FinalResult):
        pass

    @abstractmethod
    def write_log(self, result: FinalResult):
        pass

    def process(self, result: FinalResult):
        self.write_foods(result)
        self.write_log(result)

class CsvOutputWriter(OutputWriter):
    """Writes meal analysis to CSV files."""

    def __init__(self, output_dir: str = 'output'):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.foods_file = os.path.join(self.output_dir, 'foods.csv')
        self.log_file = os.path.join(self.output_dir, 'food_log.csv')

    def write_foods(self, result: FinalResult):
        with open(self.foods_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if f.tell() == 0:
                writer.writerow(['food_id', 'food_name', 'serving_size', 'serving_unit', 'calories', 'protein_g', 'carbs_g', 'fat_g'])
            
            for food in result.analysis.processed_foods:
                food.food_id = food.food_id or f"F{hash(food.food_name)}" # Simple hash for ID
                s = food.standard_serving
                n = s.nutrition
                writer.writerow([
                    food.food_id,
                    food.food_name, s.size.amount, s.size.unit, n.calories, 
                    n.protein, n.carbs, n.fat
                ])

    def write_log(self, result: FinalResult):
        with open(self.log_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if f.tell() == 0:
                writer.writerow([
                    'Date', 'Food Name', 'Unit', 'Count', 'Calories', 
                    'Protein', 'Carbs', 'Fat'
                ])
            
            for food in result.analysis.processed_foods:
                c = food.consumed.nutrition
                writer.writerow([
                    result.timestamp.strftime('%Y-%m-%d'),
                    food.food_name,
                    food.consumed.size.unit,
                    f"{food.consumed.standard_servings:.2f}",
                    f"{c.calories:.1f}",
                    f"{c.protein:.1f}",
                    f"{c.carbs:.1f}",
                    f"{c.fat:.1f}"
                ])

class SheetsOutputWriter(OutputWriter):
    """Writes meal analysis to Google Sheets."""

    def __init__(self, sheets_client: SheetsClient):
        self.client = sheets_client

    def write_foods(self, result: FinalResult):
        food_rows = []
        for food in result.analysis.processed_foods:
            if not food.food_id:
                s = food.standard_serving
                n = s.nutrition
                food_rows.append([
                    food.food_name, s.size.amount, s.size.unit, n.calories, 
                    n.protein, n.carbs, n.fat
                ])
        if food_rows:
            self.client.add_foods(food_rows)

    def write_log(self, result: FinalResult):
        self.client.log_meal_analysis(result.analysis)
