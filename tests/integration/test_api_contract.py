"""
Integration test to validate the live API contract against our schema and data expectations.
"""
import os
import json
import re
import yaml
import pytest
from food_logger.gemini_client import GeminiClient

def load_test_config():
    """Load the test configuration file."""
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config.yaml')
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def assert_with_margin(actual, expected, tolerances, context):
    """Asserts that the actual value is within an acceptable margin of the expected value."""
    absolute_tolerance = tolerances['absolute']
    relative_tolerance = tolerances['relative']
    margin = max(absolute_tolerance, abs(expected) * relative_tolerance)
    assert actual == pytest.approx(expected, abs=margin), context

def _assert_product_name_is_valid(actual_name: str, expected_name: str, context: str):
    """
    Asserts that the actual product name contains all the words from the expected name,
    ignoring punctuation and case.
    """
    # Use regex to find all word characters, making the comparison robust
    expected_tokens = set(re.findall(r'\w+', expected_name.lower()))
    actual_tokens = set(re.findall(r'\w+', actual_name.lower()))

    assert expected_tokens.issubset(actual_tokens), \
        f"Expected product name tokens {expected_tokens} not found in actual name '{actual_name}' for {context}"

def assert_nutrition_facts(actual, expected, tolerances, context):
    """Compare the core nutrition facts of two food objects with a margin of error."""
    _assert_product_name_is_valid(
        actual_name=actual.get('food_name', ''),
        expected_name=expected.get('food_name', ''),
        context=context
    )
    
    # Compare standard serving details field by field
    actual_std = actual['standard_serving']
    expected_std = expected['standard_serving']
    for key in expected_std:
        if isinstance(expected_std[key], (int, float)):
            assert_with_margin(actual_std.get(key, 0), expected_std[key], tolerances, f"{key} mismatch in {context}")

    # Compare user consumed details
    actual_consumed_size = actual['consumed']['size']
    expected_consumed = expected['consumed']
    
    if 'size_options' in expected_consumed:
        # Check if the actual size is one of the valid options
        assert any(
            actual_consumed_size['amount'] == pytest.approx(opt['amount']) and actual_consumed_size['unit'] == opt['unit']
            for opt in expected_consumed['size_options']
        ), f"Consumed size {actual_consumed_size} not in expected options for {context}"
    else:
        # Fallback to single size comparison
        expected_size = expected_consumed['size']
        assert actual_consumed_size['amount'] == pytest.approx(expected_size['amount']), f"User consumed amount mismatch in {context}"
        assert actual_consumed_size['unit'] == expected_size['unit'], f"User consumed unit mismatch in {context}"

def _run_contract_test(data_file_name: str):
    """Helper function to run the core API contract test logic."""
    config = load_test_config()
    tolerances = config['tolerances']
    
    data_file_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'integration', 'inputs', data_file_name)
    with open(data_file_path, 'r') as f:
        test_data = json.load(f)
    
    prompt = test_data["prompt"]
    expected_response = test_data["expected_api_response"]
    
    client = GeminiClient()
    actual_response = client.analyze_food(prompt)
    
    assert actual_response is not None, f"API call returned None for {data_file_name}"
    assert len(actual_response) == len(expected_response), f"API returned {len(actual_response)} items, expected {len(expected_response)} for {data_file_name}"
    
    for i, actual_item in enumerate(actual_response):
        expected_item = expected_response[i]
        context = f"{data_file_name} (item {i})"
        assert_nutrition_facts(actual_item, expected_item, tolerances, context)

@pytest.mark.integration
def test_simple_product():
    """Tests the API contract for a simple product (Peter Pan Peanut Butter)."""
    _run_contract_test("peter_pan_pb.json")

@pytest.mark.integration
def test_long_name_product():
    """Tests the API contract for a product with a long name (Six Star Protein)."""
    _run_contract_test("six_star_protein.json")

@pytest.mark.integration
def test_multiple_products():
    """Tests the API contract for a prompt with multiple food items."""
    _run_contract_test("multiple_products.json")

# --- Unit tests for the assertion logic itself ---

def test_product_name_exact_match():
    """Tests that identical product names pass validation."""
    expected = "Peter Pan Peanut Butter"
    actual = "peter pan peanut butter"
    _assert_product_name_is_valid(actual, expected, "exact match context")

def test_product_name_superset_match():
    """Tests that a superset product name (with extra words/punctuation) passes."""
    expected = "Six Star Pro Nutrition 100% Whey Protein Plus"
    actual = "Six Star Pro Nutrition 100% Whey Protein Plus, Triple Chocolate"
    _assert_product_name_is_valid(actual, expected, "superset match context")

def test_product_name_mismatch():
    """Tests that a completely different product name fails validation."""
    expected = "Peter Pan Peanut Butter"
    actual = "Jif Creamy Peanut Butter"
    with pytest.raises(AssertionError):
        _assert_product_name_is_valid(actual, expected, "mismatch context")
