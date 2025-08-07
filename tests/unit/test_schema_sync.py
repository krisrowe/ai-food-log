"""
Tests for the food analysis response schema, including mocked client validation.
"""
import os
import json
import copy
import pytest
from unittest.mock import MagicMock, patch
from jsonschema import validate, ValidationError
from food_logger.gemini_client import GeminiClient, SchemaValidationError

@pytest.fixture(scope="module")
def schema():
    """Load the main response schema."""
    schema_path = os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'food_logger', 'schemas', 'food_analysis_response.json')
    with open(schema_path, 'r') as f:
        return json.load(f)

@pytest.fixture
def valid_instance():
    """Loads the known-good response from the golden file."""
    golden_file_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'golden_files', 'valid_response.json')
    with open(golden_file_path, 'r') as f:
        return json.load(f)

def test_positive(schema, valid_instance):
    """Tests that the golden file successfully validates against the schema."""
    validate(instance=valid_instance, schema=schema)

def test_negative_missing_property(schema, valid_instance):
    """Tests that validation fails if a required field ('food_name') is missing."""
    invalid_instance = copy.deepcopy(valid_instance)
    del invalid_instance[0]['food_name']
    with pytest.raises(ValidationError, match="'food_name' is a required property"):
        validate(instance=invalid_instance, schema=schema)

def test_negative_type_mismatch(schema, valid_instance):
    """Tests that validation fails if a field has the wrong data type."""
    invalid_instance = copy.deepcopy(valid_instance)
    invalid_instance[0]['confidence_score'] = "should be a number"
    with pytest.raises(ValidationError, match="'should be a number' is not of type 'number'"):
        validate(instance=invalid_instance, schema=schema)

def test_negative_unknown_property(schema, valid_instance):
    """Tests that validation fails if an unexpected property is added."""
    invalid_instance = copy.deepcopy(valid_instance)
    invalid_instance[0]['unexpected_property'] = "should not be here"
    with pytest.raises(ValidationError, match="Additional properties are not allowed"):
        validate(instance=invalid_instance, schema=schema)

@patch('food_logger.gemini_client.genai.GenerativeModel')
def test_gemini_client_validates_schema(mock_generative_model, valid_instance):
    """
    Tests that the GeminiClient raises a SchemaValidationError when the API 
    returns a malformed response.
    """
    # Create a malformed response (missing required 'nutrition' field)
    malformed_response = copy.deepcopy(valid_instance)
    del malformed_response[0]['standard_serving']['nutrition']

    # Mock the entire API response chain
    mock_response = MagicMock()
    mock_function_call = MagicMock()
    mock_function_call.name = "log_food_data"
    mock_function_call.args = {'items': malformed_response}
    mock_response.candidates[0].content.parts = [MagicMock(function_call=mock_function_call)]
    mock_generative_model.return_value.generate_content.return_value = mock_response

    client = GeminiClient()
    
    # Assert that our custom exception is raised
    with pytest.raises(SchemaValidationError):
        client.analyze_food("any prompt")