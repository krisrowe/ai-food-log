# AI Food Logger Makefile
.PHONY: setup test test-unit test-integration log clean help

# Project directory (current directory)
PROJECT_DIR := $(shell pwd)

# Default target
help:
	@echo "🍎 AI Food Logger"
	@echo ""
	@echo "Available commands:"
	@echo "  make setup              Setup virtual environment and install dependencies"
	@echo "  make log FOOD=\"...\"      Log food consumption"
	@echo "  make test               Run all tests"
	@echo "  make test-unit          Run unit tests only"
	@echo "  make test-integration   Run integration tests (requires API key)"
	@echo "  make clean              Clean up generated files"
	@echo ""
	@echo "Examples:"
	@echo "  make log FOOD=\"160g grilled chicken breast\""
	@echo "  make log FOOD=\"26g Core Power Vanilla protein shake\""
	@echo "  make log FOOD=\"1 cup of milk\""

# Setup virtual environment and install dependencies
setup:
	@echo "🔧 Setting up virtual environment..."
	@python3 -m venv venv
	@echo "📦 Installing dependencies..."
	@./venv/bin/pip install -r requirements.txt
	@echo "✅ Setup complete!"
	@echo ""
	@echo "Next steps:"
	@echo "1. Copy .env.example to .env and add your API keys."
	@echo "2. Run: make log FOOD=\"your food description\""

# Log food consumption (requires FOOD parameter)
log:
	@if [ -z "$(FOOD)" ]; then \
		echo "❌ Error: FOOD parameter is required"; \
		echo "Usage: make log FOOD='160g grilled chicken breast'"; \
		echo "       make log FOOD='Turkey breast 121g, Core Power 26g Vanilla, 2 bananas'"; \
		exit 1; \
	fi
	@echo "🍽️  Analyzing food(s): $(FOOD)"
	@echo "Working directory: $$(pwd)"
	@echo "Python path: $(PROJECT_DIR)"
	@cd $(PROJECT_DIR) && PYTHONPATH=. ./venv/bin/python3 -m src.food_logger "$(FOOD)"

# Note: CSV export is now built into the main log command
# No separate export step needed - meal_analysis.csv is created automatically

# Clean up any stray CSV files (keeps only meal_analysis.csv)
clean-csv:
	@echo "🧹 Cleaning up stray CSV files..."
	@cd $(PROJECT_DIR) && find . -name "*.csv" ! -name "meal_analysis.csv" -type f -delete 2>/dev/null || true
	@echo "✅ Cleaned up. Only meal_analysis.csv will remain."

# Log with Google Sheets integration
log-sheets:
	@if [ -z "$(FOOD)" ]; then \
		echo "❌ Error: FOOD parameter is required"; \
		echo "Usage: make log-sheets FOOD='Turkey breast 121g, Core Power 26g'"; \
		exit 1; \
	fi
	@echo "🍽️  Analyzing and logging to Google Sheets: $(FOOD)"
	@cd $(PROJECT_DIR) && PYTHONPATH=. ./venv/bin/python3 -m src.food_logger "$(FOOD)" --sheets

# Run all tests
test: test-unit test-integration

# Run unit tests
test-unit:
	@echo "🧪 Running unit tests..."
	@PYTHONPATH=src ./venv/bin/pytest tests/unit/ -v

# Run integration tests
test-integration:
	@echo "🧪 Running integration tests..."
	@PYTHONPATH=src ./venv/bin/pytest tests/integration/ -v

# Enable AI API tracing
trace-on:
	@echo "🔍 Enabling AI API tracing..."
	@sed -i 's/enable_ai_api_trace: false/enable_ai_api_trace: true/' config.yaml
	@echo "✅ Tracing enabled - logs will be written to ai_api_trace.log"

# Disable AI API tracing
trace-off:
	@echo "🔍 Disabling AI API tracing..."
	@sed -i 's/enable_ai_api_trace: true/enable_ai_api_trace: false/' config.yaml
	@echo "✅ Tracing disabled"

# Clean up generated files
clean:
	@echo "🧹 Cleaning up..."
	@rm -rf venv
	@rm -rf __pycache__
	@rm -rf .pytest_cache
	@rm -rf src/**/__pycache__
	@rm -rf tests/**/__pycache__
	@rm -f ai_api_trace.log
	@rm -f *.db
	@find . -name "*.csv" -type f -delete
	@echo "✅ Cleanup complete!"

# Check configuration
check-config:
	@echo "🔍 Checking configuration..."
	@if [ -f .env ]; then \
		echo "✅ .env file exists"; \
		if grep -q "GOOGLE_API_KEY=your_google_api_key_here" .env; then \
			echo "❌ Please set your GOOGLE_API_KEY in .env"; \
		elif ! grep -q "GOOGLE_API_KEY" .env; then \
			echo "❌ GOOGLE_API_KEY is not set in .env"; \
		else \
			echo "✅ GOOGLE_API_KEY is configured"; \
		fi; \
	else \
		echo "❌ .env file not found - copy from .env.example"; \
	fi
	@if [ -f config.yaml ]; then \
		echo "✅ config.yaml exists"; \
		if grep -q "enable_ai_api_trace: true" config.yaml; then \
			echo "🔍 AI API tracing is ENABLED"; \
		else \
			echo "🔍 AI API tracing is disabled"; \
		fi; \
	else \
		echo "❌ config.yaml not found"; \
	fi