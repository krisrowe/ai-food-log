# AI Food Logger Makefile
.PHONY: setup test test-unit test-integration log clean help

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
	python3 -m venv venv
	@echo "📦 Installing dependencies..."
	./venv/bin/pip install -r requirements.txt
	@echo "✅ Setup complete!"
	@echo ""
	@echo "Next steps:"
	@echo "1. Copy config.ini.example to config.ini"
	@echo "2. Add your Gemini API key to config.ini"
	@echo "3. Run: make log FOOD=\"your food description\""

# Log food consumption (requires FOOD parameter)
log:
	@if [ -z "$(FOOD)" ]; then \
		echo "❌ Error: FOOD parameter is required"; \
		echo "Usage: make log FOOD='160g grilled chicken breast'"; \
		echo "       make log FOOD='Turkey breast 121g, Core Power 26g Vanilla, 2 bananas'"; \
		exit 1; \
	fi
	@echo "🍽️  Analyzing food(s): $(FOOD)"
	@cd $(PROJECT_DIR) && PYTHONPATH=. python3 -m food_logger "$(FOOD)"

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
	@cd $(PROJECT_DIR) && PYTHONPATH=. python3 -c "from src.food_logger.gemini_client import main; import sys; sys.argv = ['', '$(FOOD)', '--sheets']; main()"

# Run all tests
test:
	@echo "🧪 Running all tests..."
	./venv/bin/pytest -v

# Run unit tests only
test-unit:
	@echo "🧪 Running unit tests..."
	./venv/bin/pytest tests/unit/ -v

# Run integration tests
test-integration:
	@echo "🧪 Running integration tests..."
	@if [ ! -f config.ini ]; then \
		echo "❌ config.ini required for integration tests"; \
		exit 1; \
	fi
	./venv/bin/pytest tests/integration/ -v -m integration

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
	rm -rf venv
	rm -rf __pycache__
	rm -rf .pytest_cache
	rm -rf src/**/__pycache__
	rm -rf tests/**/__pycache__
	rm -f ai_api_trace.log
	rm -f *.db
	@echo "✅ Cleanup complete!"

# Development helpers
dev-setup: setup
	@echo "🔧 Setting up development environment..."
	./venv/bin/pip install -e .
	@echo "✅ Development setup complete!"

# Check configuration
check-config:
	@echo "🔍 Checking configuration..."
	@if [ -f config.ini ]; then \
		echo "✅ config.ini exists"; \
		if grep -q "your_gemini_api_key_here" config.ini; then \
			echo "❌ Please set your Gemini API key in config.ini"; \
		else \
			echo "✅ Gemini API key configured"; \
		fi; \
	else \
		echo "❌ config.ini not found - copy from config.ini.example"; \
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
