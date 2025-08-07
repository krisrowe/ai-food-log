# 🍎 AI Food Logger

An intelligent food logging system that uses natural language processing and Google's Gemini AI to extract detailed nutrition information from simple food descriptions.

## ✨ Features

- **Natural Language Input**: "I ate 150g of grilled chicken breast" → Structured nutrition data
- **AI-Powered Analysis**: Uses Google's Gemini API with Google Search grounding for accurate nutrition
- **Multiple Output Formats**: Supports CSV and Google Sheets.
- **Unit Conversion**: Handles grams, ounces, cups, and other common units
- **Serving Size Calculations**: Automatically scales nutrition based on actual consumption
- **Confidence Scoring**: Indicates reliability of nutrition estimates
- **Comprehensive Testing**: Unit and integration tests for reliability

## 🚀 Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd ai-food-log

# Set up virtual environment and install dependencies
make setup
```

### 2. Configure API Keys

```bash
# Copy the example config
cp config.ini.example config.ini
cp config.yaml.example config.yaml

# Edit config.ini with your API keys
# Get Gemini API key from: https://makersuite.google.com/app/apikey
```

### 3. Start Logging Food!

```bash
# Log your food with natural language
make log FOOD="160g grilled chicken breast"
make log FOOD="26g Core Power Vanilla protein shake"
make log FOOD="1 cup of cooked quinoa"
```

## 📖 Usage

This project uses a `Makefile` for common development tasks.

| Command | Description |
|---|---|
| `make setup` | Creates a Python virtual environment and installs all required dependencies. |
| `make log FOOD="..."` | Analyzes the food description provided in the `FOOD` variable and saves the output. |
| `make log-sheets FOOD="..."` | Analyzes the food and saves the output to Google Sheets. |
| `make test` | Runs the complete test suite (unit and integration tests). |
| `make test-unit` | Runs only the unit tests. |
| `make test-integration` | Runs only the integration tests (requires a configured API key). |
| `make clean` | Removes all generated files, such as virtual environments and cache files. |
| `make help` | Displays a list of all available commands. |

### ⚠️ Known Limitations

- **Multi-Product Prompts**: The system currently struggles with prompts containing multiple, comma-separated food items. This is a known issue and is being actively worked on. While you can try it, it may not produce the expected results.
  - **Example of an experimental multi-product prompt:**
    ```bash
    make log FOOD="121g turkey breast, 1 great value fiber brownie, 2 bananas"
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
# The output method to use. Can be 'csv' or 'sheets'.
output_method: 'csv'

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
```

## 🧪 Testing

### All Tests

```bash
# Run all tests using Makefile
make test
```

### Unit & Integration Tests

```bash
# Run unit tests
make test-unit

# Run integration tests (requires a configured Gemini API key)
make test-integration
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass: `make test`
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details
