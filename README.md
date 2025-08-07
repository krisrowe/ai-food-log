# 🍎 AI Food Logger

An intelligent food logging system that uses natural language processing and Google's Gemini AI to extract detailed nutrition information from simple food descriptions.

## ✨ Features

- **Natural Language Input**: "I ate 150g of grilled chicken breast" → Structured nutrition data
- **AI-Powered Analysis**: Uses Google's Gemini API with Google Search grounding for accurate nutrition
- **Multi-Food Analysis**: Log an entire meal in a single command (e.g., "2 eggs, 1 slice of toast, and a banana").
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
# Copy the environment file example
cp .env.example .env

# Edit .env and add your API keys and Google Sheet details
```

### 3. Start Logging Food!

```bash
# Log a single food item
make log FOOD="160g grilled chicken breast"

# Log an entire meal at once
make log FOOD="2 bananas, 1 great value fiber brownie, and 4 scoops of protein powder"
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

## ⚙️ Configuration

Configuration is managed through environment variables and the `config.yaml` file.

### Environment Variables

Create a `.env` file in the project root for your secret keys. You can copy the example file to get started:

```bash
cp .env.example .env
```

Then, edit your `.env` file:

```env
# .env

# Used by the Gemini API client library
GOOGLE_API_KEY="your_google_api_key_here"

# Optional: Used by the Gemini CLI if that's your IDE of choice.
# This may be the same as your GOOGLE_API_KEY.
GEMINI_API_KEY="your_gemini_api_key_here"

# Optional: For Google Sheets integration
# The ID of your Google Sheet, found in its URL
GOOGLE_SHEETS_ID="your_google_sheets_id_here"

# Optional: The path to your Google Cloud service account JSON key file for Sheets integration
GOOGLE_APPLICATION_CREDENTIALS="path/to/your/service-account-key.json"
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
