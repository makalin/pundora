# Pundora - Dad Joke Generator Makefile

.PHONY: help install run test clean dev setup

# Default target
help:
	@echo "🎭 Pundora - Dad Joke Generator"
	@echo "================================"
	@echo ""
	@echo "Available commands:"
	@echo "  make install    - Install dependencies"
	@echo "  make setup      - Setup environment and install dependencies"
	@echo "  make run        - Run the web application"
	@echo "  make cli        - Run CLI example"
	@echo "  make test       - Run installation tests"
	@echo "  make dev        - Run in development mode with auto-reload"
	@echo "  make clean      - Clean up generated files"
	@echo "  make help       - Show this help message"

# Install dependencies
install:
	@echo "📦 Installing dependencies..."
	pip install -r requirements.txt

# Setup environment
setup: install
	@echo "⚙️ Setting up environment..."
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "✅ Created .env file from template"; \
		echo "⚠️  Please edit .env with your API keys"; \
	else \
		echo "✅ .env file already exists"; \
	fi

# Run the web application
run:
	@echo "🚀 Starting Pundora web application..."
	python main.py

# Run CLI example
cli:
	@echo "💻 Running CLI example..."
	python -m pundora.cli --joke --category puns --level medium

# Run tests
test:
	@echo "🧪 Running installation tests..."
	python test_installation.py

# Run in development mode
dev:
	@echo "🔧 Starting in development mode..."
	uvicorn pundora.api:app --reload --host 0.0.0.0 --port 8000

# Clean up
clean:
	@echo "🧹 Cleaning up..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type f -name "*.mp3" -delete
	find . -type f -name "*.wav" -delete
	@echo "✅ Cleanup complete"