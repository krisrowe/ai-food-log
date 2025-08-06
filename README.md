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

# Simple setup - handles virtual environment automatically
python run.py setup
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
python run.py log "I ate 150g grilled chicken breast"
python run.py log "26g Core Power Vanilla protein shake"
python run.py log "1 cup of cooked quinoa"
```

## 📖 Usage Examples

### Whole Foods (Natural ingredients)

```bash
python run.py log "160g grilled chicken breast"
# Output:
# ✅ Whole food consistency - Chicken breast:
#    Name: Grilled Chicken Breast
#    Nutrition per 100g: 165.0 cal, 31.0g protein, 0.0g carbs, 3.0g fat
#    Confidence: medium

python run.py log "100g raw salmon fillet"
python run.py log "1 large egg"
python run.py log "1 medium banana"
```

### Packaged Products (Branded items)

```bash
python run.py log "26g Core Power Vanilla protein shake"
# Output:
# ✅ Packaged product - Core Power Vanilla:
#    Name: Core Power Vanilla Protein Shake
#    Nutrition per 1 bottle (26g): 110.0 cal, 20.0g protein, 7.0g carbs, 2.5g fat
#    Confidence: medium

python run.py log "1 Clif Bar Chocolate Chip"
python run.py log "1 cup Chobani Greek Yogurt Plain"
```

### Ambiguous Foods (May need clarification)

```bash
python run.py log "1 cup of milk"
# Output:
# ✅ Ambiguous milk (needs fat % clarification):
#    Name: Milk, cow's milk
#    Confidence: high
#    Notes: Data compiled from USDA FoodData Central and average values for whole milk.
#           Values may vary slightly depending on the type of milk (e.g., skim, 2%, whole) and brand.

python run.py log "2 slices of bread"
python run.py log "1 scoop protein powder"
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
  # Enable detailed tracing of Gemini API requests and responses
  enable_gemini_trace: false
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

### Gemini API Tracing

Enable detailed API tracing for debugging:

```yaml
# In config.yaml
logging:
  enable_gemini_trace: true
```

Traces are written to `gemini_trace.log` in human-readable format:

```
=== GEMINI API CALL ===
Timestamp: 2025-01-06 01:15:30
Input: "160g grilled chicken breast"

Request:
{
  "contents": [{
    "parts": [{
      "text": "Analyze the following food description..."
    }]
  }]
}

Response:
{
  "food_name": "Grilled Chicken Breast",
  "serving_size": "100g",
  "calories_per_serving": 165.0,
  "protein_g": 31.0,
  "confidence": "medium"
}

Duration: 2.3s
========================
```

## 🧪 Testing

### Run All Tests

```bash
python run.py test
```

### Unit Tests (Fast, No API calls)

```bash
python run.py test-unit
```

### Integration Tests (Requires Gemini API key)

```bash
python run.py test-integration
```

### Test Categories

- **Whole Foods**: Natural ingredients with stable nutrition (chicken, salmon, eggs)
- **Packaged Products**: Branded items with fixed nutrition labels (Core Power, Clif Bars)
- **Ambiguous Foods**: Items needing clarification ("milk" without fat %, "bread" without type)
- **Exception Cases**: Invalid inputs, non-food items, edge cases

## 🏗️ Architecture

### Core Components

```
src/food_logger/
├── core.py              # Core business logic and data models
├── gemini_client.py     # Gemini API integration
└── sheets_client.py     # Google Sheets integration

tests/
├── unit/                # Fast unit tests with mocks
└── integration/         # Real API integration tests

food_logger.py           # CLI interface
run.py                   # Simple runner (handles venv, config)
```

### Data Flow

1. **Input**: Natural language food description
2. **Analysis**: Gemini API extracts nutrition with Google Search grounding
3. **Database Check**: Look for existing food in Google Sheets
4. **Food Entry**: Create new food entry if needed
5. **Consumption Log**: Record consumption with foreign key to food
6. **Output**: Display nutrition breakdown and confidence

### Google Sheets Structure

**Foods Tab** (Master database):
| ID | Food Name | Serving Size | Calories | Protein | Carbs | Fat | Fiber | Sugar | Confidence | Source |
|----|-----------|--------------|----------|---------|-------|-----|-------|-------|------------|--------|
| 1  | Grilled Chicken Breast | 100g | 165 | 31.0 | 0.0 | 3.0 | 0.0 | 0.0 | medium | Gemini |

**Food Log Tab** (Daily consumption):
| Date | Time | Food ID | Food Name | Amount | Calories | Protein | Carbs | Fat |
|------|------|---------|-----------|--------|----------|---------|-------|-----|
| 2025-01-06 | 12:30 | 1 | Grilled Chicken Breast | 160g | 264 | 49.6 | 0.0 | 4.8 |

## 🔧 Development

### Adding New Food Analyzers

```python
from food_logger.core import FoodAnalyzer, FoodData

class MyFoodAnalyzer(FoodAnalyzer):
    def analyze_food(self, description: str) -> Optional[FoodData]:
        # Your implementation here
        return FoodData(...)
```

### Adding New Database Backends

```python
from food_logger.core import FoodDatabase

class MyFoodDatabase(FoodDatabase):
    def find_food(self, food_name: str) -> Optional[FoodData]:
        # Your implementation here
        pass
    
    def save_food(self, food_data: FoodData) -> str:
        # Your implementation here
        pass
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
