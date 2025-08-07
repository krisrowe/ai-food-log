"""
Unit tests for the CsvOutputWriter class, focusing on the simplified food log.
"""
import os
import csv
import json
import pytest
import tempfile
from datetime import datetime
from food_logger.output_writer import CsvOutputWriter
from food_logger.models import MealAnalysis, FinalResult

def get_expected_output_files_with_ids():
    """
    Generates tuples of (file_path, test_id) for each expected output file.
    The test_id is the base name of the file, which is more readable in test output.
    """
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'unit', 'expected_outputs')
    for f in os.listdir(data_dir):
        if f.endswith('.json'):
            file_path = os.path.join(data_dir, f)
            test_id = os.path.basename(f)
            yield pytest.param(file_path, id=test_id)

@pytest.mark.parametrize("expected_output_file", get_expected_output_files_with_ids())
def test_csv_writer(expected_output_file):
    """
    Tests the simplified food_log.csv writing functionality with robust setup and teardown.
    """
    with open(expected_output_file, 'r') as f:
        expected_data = json.load(f)
    
    analysis = MealAnalysis.from_dict(expected_data)
    timestamp = datetime.now()
    result = FinalResult(analysis=analysis, avg_confidence=0.9, timestamp=timestamp)
    
    # Use a temporary directory provided by pytest for clean test runs
    with tempfile.TemporaryDirectory() as tmpdir:
        test_csv_path = os.path.join(tmpdir, "food_log.csv")
        writer = CsvOutputWriter(output_dir=tmpdir)
        
        # Ensure file does not exist before test
        if os.path.exists(test_csv_path):
            os.remove(test_csv_path)

        # --- Execute ---
        writer.write_log(result)
        
        # --- Validate ---
        assert os.path.exists(test_csv_path), "CSV file was not created."
        
        with open(test_csv_path, 'r') as f:
            reader = csv.reader(f)
            rows = list(reader)
            
        assert len(rows) == len(analysis.processed_foods) + 1 # foods + header
        
        expected_header = ['Date', 'Food Name', 'Unit', 'Count', 'Calories', 'Protein', 'Carbs', 'Fat']
        assert rows[0] == expected_header
        
        first_food = analysis.processed_foods[0]
        first_row = rows[1]
        
        assert first_row[0] == timestamp.strftime('%Y-%m-%d')
        assert first_row[1] == first_food.food_name
        assert first_row[2] == first_food.consumed.size.unit
        assert float(first_row[3]) == pytest.approx(first_food.consumed.standard_servings, 0.01)
        assert float(first_row[4]) == pytest.approx(first_food.consumed.nutrition.calories, 0.1)
        assert float(first_row[5]) == pytest.approx(first_food.consumed.nutrition.protein, 0.1)

        # Teardown is handled automatically by TemporaryDirectory context manager