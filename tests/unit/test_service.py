"""
Unit tests for the FoodLoggerService.
"""
import pytest
from unittest.mock import patch, MagicMock

from food_logger.food_logger_service import FoodLoggerService
from food_logger.models import FinalResult
from food_logger.output_writer import OutputWriter

# A sample raw food response that gemini_client.analyze_food would return
SAMPLE_RAW_FOODS = [
    {
        "food_name": "Turkey breast",
        "standard_serving": {
            "size": {"amount": 100, "unit": "g"},
            "nutrition": {"calories": 110, "protein": 25, "carbs": 0, "fat": 1},
            "alt_size": None
        },
        "consumed": {
            "size": {"amount": 121, "unit": "g"}
        },
        "servings": {"calculable": True},
        "user_description": "Turkey breast 121g",
        "confidence_score": 9,
        "source_notes": "USDA database"
    }
]

@pytest.fixture
def mock_gemini_client():
    """Fixture to mock the GeminiClient and its analyze_food method."""
    with patch('food_logger.food_logger_service.GeminiClient') as mock_client_class:
        mock_client_instance = mock_client_class.return_value
        mock_client_instance.analyze_food.return_value = SAMPLE_RAW_FOODS
        yield mock_client_instance

@pytest.fixture
def mock_csv_writer():
    """Fixture to mock the CsvOutputWriter."""
    with patch('food_logger.food_logger_service.CsvOutputWriter') as mock_writer_class:
        mock_writer_instance = MagicMock(spec=OutputWriter)
        mock_writer_class.return_value = mock_writer_instance
        yield mock_writer_class

@pytest.fixture
def mock_sheets_writer():
    """Fixture to mock the SheetsOutputWriter."""
    with patch('food_logger.food_logger_service.SheetsOutputWriter') as mock_writer_class:
        mock_writer_instance = MagicMock(spec=OutputWriter)
        mock_writer_class.return_value = mock_writer_instance
        yield mock_writer_class

@pytest.fixture
def mock_sheets_client():
    """Fixture to mock the SheetsClient."""
    with patch('food_logger.food_logger_service.SheetsClient') as mock_s_client:
        yield mock_s_client

def test_process_meal_invokes_gemini_client(mock_gemini_client):
    """
    Tests that process_meal correctly calls the Gemini client's analyze_food method.
    """
    # Arrange
    service = FoodLoggerService()
    food_description = "A specific food description"
    
    # Act
    service.process_meal(food_description, output_method='csv')
    
    # Assert
    mock_gemini_client.analyze_food.assert_called_once_with(food_description)

def test_process_meal_uses_csv_writer(mock_gemini_client, mock_csv_writer, mock_sheets_writer):
    """
    Tests that process_meal calls the CsvOutputWriter when output_method is 'csv'.
    """
    # Arrange
    service = FoodLoggerService()
    food_description = "Turkey breast 121g"
    
    # Act
    result = service.process_meal(food_description, output_method='csv')

    # Assert
    assert result is not None
    assert isinstance(result, FinalResult)
    
    # Check that the correct writer was instantiated and used
    mock_csv_writer.assert_called_once()
    mock_csv_writer.return_value.process.assert_called_once_with(result)
    
    # Check that the other writer was NOT used
    mock_sheets_writer.assert_not_called()

def test_process_meal_uses_sheets_writer(mock_gemini_client, mock_sheets_writer, mock_csv_writer, mock_sheets_client):
    """
    Tests that process_meal calls the SheetsOutputWriter when output_method is 'sheets'.
    """
    # Arrange
    service = FoodLoggerService()
    food_description = "Turkey breast 121g"

    # Act
    result = service.process_meal(food_description, output_method='sheets')

    # Assert
    assert result is not None
    assert isinstance(result, FinalResult)

    # Check that the correct writer was instantiated and used
    mock_sheets_client.assert_called_once()
    mock_sheets_writer.assert_called_once_with(sheets_client=mock_sheets_client.return_value)
    mock_sheets_writer.return_value.process.assert_called_once_with(result)

    # Check that the other writer was NOT used
    mock_csv_writer.assert_not_called()
