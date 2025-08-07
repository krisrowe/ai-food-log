"""
Unit test for the FoodLoggerService's pure calculation logic.
"""
import os
import json
import pytest
from jsonschema import validate, ValidationError
from food_logger.food_logger_service import FoodLoggerService
from food_logger.models import MealAnalysis

def get_input_files_with_ids():
    """
    Generates tuples of (file_path, test_id) for each input file.
    The test_id is the base name of the file, which is more readable in test output.
    """
    input_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'unit', 'inputs')
    for f in os.listdir(input_dir):
        if f.endswith('.json'):
            file_path = os.path.join(input_dir, f)
            test_id = os.path.basename(f)
            yield pytest.param(file_path, id=test_id)

@pytest.fixture(scope='module')
def response_schema():
    """Loads the master food analysis response schema once per test module run."""
    schema_path = os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'food_logger', 'schemas', 'food_analysis_response.json')
    with open(schema_path, 'r') as f:
        return json.load(f)

@pytest.mark.parametrize("input_file", get_input_files_with_ids())
def test_input_data_conforms_to_schema(input_file, response_schema):
    """
    Validates that the 'expected_api_response' in each test data file
    conforms to the official response schema.

    WHY THIS TEST EXISTS:
    This test acts as a critical guardrail to prevent a class of bugs where the
    application code works with unit tests but fails in integration tests with the Gemini API.
    It ensures that our mock test data never diverges from the real-world data structure
    defined by our schema. If this test fails, it means a test data file has
    either a missing required field or an extra, unexpected field. This prevents
    "passing" unit tests that rely on incorrectly shaped mock data, which was
    the root cause of the 'description' key error.
    """
    with open(input_file, 'r') as f:
        test_data = json.load(f)

    assert 'expected_api_response' in test_data, f"Test data file {input_file} is missing 'expected_api_response' key."
    
    api_response_data = test_data['expected_api_response']
    
    try:
        validate(instance=api_response_data, schema=response_schema)
    except ValidationError as e:
        pytest.fail(
            f"Schema validation failed for {os.path.basename(input_file)}.\n"
            f"Error: {e.message}\n"
            f"Path: {list(e.path)}\n"
            f"Validator: {e.validator} = {e.validator_value}"
        )

@pytest.mark.parametrize("input_file", get_input_files_with_ids())
def test_calculation_logic(input_file):
    """
    Tests the deterministic calculation logic against a "golden file".
    """
    # Derive paths
    base_name = os.path.basename(input_file)
    expected_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'unit', 'expected_outputs', base_name.replace('.json', '.expected.json'))
    
    # Load data
    with open(input_file, 'r') as f:
        input_data = json.load(f)
    raw_api_response = input_data["expected_api_response"]
    
    with open(expected_file, 'r') as f:
        expected_output = json.load(f)
        
    # --- Execution ---
    service = FoodLoggerService()
    actual_analysis = service.analyze_meal_from_data(raw_api_response)
    
    assert actual_analysis is not None, "The analysis function returned None."
    actual_output = actual_analysis.to_dict()
    
    # --- Verification ---
    assert actual_output == expected_output
