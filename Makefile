.PHONY: help install test test-coverage lint format clean docker-build docker-run

# Default target
help:
	@echo "Available commands:"
	@echo "  install        Install dependencies"
	@echo "  test           Run all tests"
	@echo "  test-coverage  Run tests with coverage"
	@echo "  test-unit      Run unit tests only"
	@echo "  test-integration Run integration tests only"
	@echo "  lint           Run linting checks"
	@echo "  format         Format code with black and isort"
	@echo "  clean          Clean up generated files"
	@echo "  docker-build   Build Docker image"
	@echo "  docker-run     Run Docker container"
	@echo "  ci-local       Run all CI checks locally"

# Install dependencies
install:
	uv sync --extra test,lint,security

# Run all tests
test:
	uv run pytest tests/ -v

# Run tests with coverage
test-coverage:
	uv run pytest tests/ -v --cov=src --cov-report=term-missing --cov-report=html

# Run unit tests only
test-unit:
	uv run pytest tests/ -v -m unit

# Run integration tests only
test-integration:
	uv run pytest tests/ -v -m integration

# Run linting checks
lint:
	uv run black --check --diff src/ tests/
	uv run isort --check-only --diff src/ tests/

# Format code
format:
	uv run black src/ tests/
	uv run isort src/ tests/

# Clean up generated files
clean:
	rm -rf __pycache__/
	rm -rf src/__pycache__/
	rm -rf tests/__pycache__/
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf coverage.xml
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Build Docker image
docker-build:
	docker build -t knoll-bot .

# Run Docker container
docker-run:
	docker run --env-file .env knoll-bot

# Run the bot
run:
	uv run python src/main.py

# Run CI checks locally
act:
	act -W .github/workflows/ci.yml
