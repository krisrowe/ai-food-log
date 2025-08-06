# 🍎 AI Food Logger

An intelligent food logging system that uses natural language processing and Google's Gemini AI to extract detailed nutrition information from simple food descriptions.

## ✨ Features

- **Natural Language Input**: "I ate 150g of grilled chicken breast" → Structured nutrition data
- **AI-Powered Analysis**: Uses Google's Gemini API with Google Search grounding for accurate nutrition
- **Smart Food Database**: Automatically builds a reusable database of foods in Google Sheets
- **Unit Conversion**: Handles grams, ounces, cups, and other common units
- **Serving Size Calculations**: Automatically scales nutrition based on actual consumption
- **Confidence Scoring**: Indicates reliability of nutrition estimates
- **Comprehensive Testing**: Unit and integration tests for reliability

## 🚀 Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd ai-food-log

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure API Keys

```bash
# Copy the example config
cp config.ini.example config.ini

# Edit config.ini with your API keys
# Get Gemini API key from: https://makersuite.google.com/app/apikey
```

### 3. Start Logging Food!

```bash
# Log your food with natural language
python -m food_logger "160g grilled chicken breast"
python -m food_logger "26g Core Power Vanilla protein shake"
python -m food_logger "1 cup of cooked quinoa"

# Or use the Makefile
make log FOOD="160g grilled chicken breast"
make export  # Export to CSV
```

## 📖 Usage Examples

### Single Food Analysis

```bash
# Using Python module
python -m food_logger "160g grilled chicken breast"

# Using Makefile (recommended)
make log FOOD="160g grilled chicken breast"

# Output:
# ✅ Successfully analyzed 1 food(s):
# ================================================================================
# 
# 1. Grilled Chicken Breast
#    User consumed: 160.0 g
#    Standard serving: 100.0 g
#    Scaling factor: 1.60x
#    Calories: 264.0
#    Protein: 49.6g | Carbs: 0.0g | Fat: 4.8g
#    Confidence: 9.0/10
#    Notes: Nutrition information based on average values for grilled chicken breast...
# 
# 📊 Meal analysis exported to meal_analysis.csv
```

### Multi-Food Analysis (Multiple foods in one command)

```bash
make log FOOD="2 bananas and 1 apple"
# Or:
python -m food_logger "4 scoops protein powder, 2 bananas"

# Output:
# ✅ Successfully analyzed 2 food(s):
# ================================================================================
# 
# 1. Six Star Protein Powder (Chocolate)
#    User consumed: 188.0 g
#    Standard serving: 30.0 g
#    Scaling factor: 6.27x
#    Calories: 752.0
#    Protein: 150.4g | Carbs: 18.8g | Fat: 9.4g
#    Confidence: 8.0/10
# 
# 2. Banana
#    User consumed: 2.0 medium
#    Standard serving: 1.0 medium
#    Scaling factor: 2.00x
#    Calories: 210.0
#    Protein: 2.0g | Carbs: 54.0g | Fat: 0.8g
#    Confidence: 9.0/10
# 
# ================================================================================
# TOTALS: 962 cal | 152.4g protein | 72.8g carbs | 10.2g fat
# Average confidence: 8.5/10
```

### CSV Export

```bash
# Export analysis to CSV (happens automatically)
make export

# View the CSV file
cat meal_analysis.csv
```

## ⚙️ Configuration

### config.ini (Sensitive - Not in Git)

```ini
[gemini]
# Get your API key from: https://makersuite.google.com/app/apikey
api_key = your_gemini_api_key_here

[google_sheets]
# Google Sheets ID from the URL: https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit
sheet_id = your_google_sheets_id_here

# Path to your Google service account JSON key file
# Download from: https://console.cloud.google.com/iam-admin/serviceaccounts
service_account_key = path/to/your/service-account-key.json
```

### config.yaml (Non-sensitive - In Git)

```yaml
# Logging Configuration
logging:
  # Enable detailed tracing of AI API requests and responses
  # Traces are written to ai_api_trace.log (excluded from git)
  enable_ai_api_trace: true
  log_level: "INFO"
  max_trace_files: 7

# Food Analysis Settings
food_analysis:
  default_serving_unit: "grams"
  confidence_threshold: "medium"
  max_retries: 3

# CLI Settings
cli:
  show_detailed_output: true
  output_format: "table"  # "table", "json", "simple"
```

### AI API Tracing

Enable detailed API tracing for debugging:

```yaml
# In config.yaml
logging:
  enable_ai_api_trace: true
```

Traces are written to `ai_api_trace.log` in human-readable format:

```
=== AI API CALL ===
Timestamp: 2025-01-06 01:15:30
Input: "160g grilled chicken breast"

Request:
{
  "contents": [{
    "parts": [{
      "text": "Analyze the following food description and return an array..."
    }]
  }]
}

Response:
================================================================================
[
  {
    "food_name": "Grilled Chicken Breast",
    "standard_serving": {
      "amount": 100.0,
      "unit": "g",
      "calories": 165.0,
      "protein_g": 31.0,
      "carbs_g": 0.0,
      "fat_g": 3.0
    },
    "user_consumed": {
      "amount": 160.0,
      "unit": "g",
      "description": "160g grilled chicken breast"
    },
    "confidence_score": 9.0,
    "source_notes": "Nutrition information based on average values..."
  }
]
================================================================================

Duration: 2.3s
========================
```

## 🧪 Testing

### All Tests

```bash
# Run all tests using Makefile
make test

# Or run directly with pytest
python -m pytest tests/ -v
```

### Integration Tests (Requires Gemini API key)

```bash
# Run integration tests (requires GOOGLE_API_KEY)
make test-integration

# Or run directly
python -m pytest tests/integration/ -v
```

### Test Results

```bash
# Example successful test output:
============= test session starts =============
tests/integration/test_simple_integration.py::TestSimpleIntegration::test_single_food_analysis PASSED [ 25%]
tests/integration/test_simple_integration.py::TestSimpleIntegration::test_multi_food_analysis PASSED [ 50%]
tests/integration/test_simple_integration.py::TestSimpleIntegration::test_food_service_integration PASSED [ 75%]
tests/integration/test_simple_integration.py::TestSimpleIntegration::test_csv_export_integration PASSED [100%]
============= 4 passed in 10.74s ==============
```

## 🏗️ Architecture

### Core Components

```
src/food_logger/
├── __init__.py              # Package initialization
├── __main__.py              # CLI entry point (python -m food_logger)
├── food_logger_service.py   # Core business logic and meal processing
├── gemini_client.py         # Gemini API integration with tracing
└── sheets_client.py         # Google Sheets integration (placeholder)

tests/
├── __init__.py              # Package initialization
├── unit/                    # Unit tests (placeholder)
└── integration/             # Integration tests with real API
    ├── __init__.py
    └── test_simple_integration.py  # Working integration tests

config.ini.example           # Configuration template
config.yaml                  # Non-sensitive settings
Makefile                     # Build and test automation
requirements.txt             # Python dependencies
```

### Data Flow

1. **Input**: Natural language food description
2. **Analysis**: Gemini API extracts nutrition with Google Search grounding
3. **Processing**: FoodLoggerService calculates scaling factors and nutrition
4. **Output**: Display nutrition breakdown with confidence scores
5. **Export**: Automatically export analysis to CSV file
6. **Logging**: Optional Google Sheets integration (planned feature)

### Current Output Structure

**CSV Export** (`meal_analysis.csv`):
| Food Name | User Consumed | Standard Serving | Scaling Factor | Calories | Protein (g) | Carbs (g) | Fat (g) | Fiber (g) | Sugar (g) | Sodium (mg) | Potassium (mg) | Vitamin C (mg) | Calcium (mg) | Iron (mg) | Confidence | Source Notes |
|-----------|---------------|------------------|----------------|----------|-------------|----------|---------|----------|-----------|-------------|----------------|----------------|--------------|-----------|------------|---------------|
| Grilled Chicken Breast | 160.0 g | 100.0 g | 1.60x | 264.0 | 49.6 | 0.0 | 4.8 | 0.0 | 0.0 | 112.0 | 480.0 | 0.0 | 16.0 | 1.6 | 9.0/10 | Nutrition information based on... |
| TOTALS | | | | 264.0 | 49.6 | 0.0 | 4.8 | 0.0 | 0.0 | 112.0 | 480.0 | 0.0 | 16.0 | 1.6 | 9.0/10 | Analysis completed at 2025-01-06 03:23:50 |

**Google Sheets Integration** (Planned Feature):
- Master foods database with reusable nutrition data
- Daily consumption logging with foreign keys
- Automatic deduplication and food matching

## 🔧 Development

### Adding New Food Analyzers

```python
from food_logger.food_logger_service import FoodLoggerService
from food_logger.gemini_client import GeminiClient

class MyFoodLoggerService(FoodLoggerService):
    def process_meal(self, food_description: str, **kwargs):
        # Your custom processing logic here
        return super().process_meal(food_description, **kwargs)
```

### Adding New AI Clients

```python
from food_logger.gemini_client import GeminiClient

class MyAIClient(GeminiClient):
    def analyze_food(self, description: str) -> Optional[list]:
        # Your implementation here (must return array of foods)
        return [
            {
                'food_name': 'Your Food',
                'standard_serving': {...},
                'user_consumed': {...},
                'confidence_score': 8.0,
                'source_notes': 'Your source'
            }
        ]
```

### Debug Mode

```yaml
# In config.yaml
development:
  debug_mode: true
  use_mock_clients: true  # Use mocks instead of real APIs
```

## 📋 Requirements

- Python 3.7+
- Google Gemini API key
- Google Sheets (optional, for data storage)
- Google Cloud Service Account (for Sheets access)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass: `python run.py test`
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

## 🆘 Troubleshooting

### Common Issues

**"GOOGLE_API_KEY not available"**
- Ensure `config.ini` exists with valid Gemini API key
- Get key from: https://makersuite.google.com/app/apikey

**"404 models/gemini-pro is not found"**
- Update to use `gemini-1.5-flash` model (already fixed in current version)

**"No module named 'pytest'"**
- Run `python run.py setup` to install dependencies

**Google Sheets access issues**
- Ensure service account has edit access to your Google Sheet
- Check that `service_account_key` path in config.ini is correct

### Getting Help

- Check the test outputs for examples of expected behavior
- Enable Gemini tracing to debug API interactions
- Run unit tests to verify core functionality
- Check configuration files for missing or incorrect values
