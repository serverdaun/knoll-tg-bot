#!/bin/bash

# Test runner script for Knoll Bot
# Usage: ./scripts/run_tests.sh [options]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
COVERAGE=false
VERBOSE=false
MARKERS=""
EXTRA_ARGS=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --coverage)
            COVERAGE=true
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --unit)
            MARKERS="unit"
            shift
            ;;
        --integration)
            MARKERS="integration"
            shift
            ;;
        --fast)
            MARKERS="not slow"
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --coverage     Run tests with coverage reporting"
            echo "  --verbose, -v  Run tests in verbose mode"
            echo "  --unit         Run only unit tests"
            echo "  --integration  Run only integration tests"
            echo "  --fast         Run tests excluding slow ones"
            echo "  --help, -h     Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                    # Run all tests"
            echo "  $0 --coverage         # Run tests with coverage"
            echo "  $0 --unit --verbose   # Run unit tests in verbose mode"
            echo "  $0 --fast             # Run fast tests only"
            exit 0
            ;;
        *)
            EXTRA_ARGS="$EXTRA_ARGS $1"
            shift
            ;;
    esac
done

echo -e "${BLUE}🧪 Running Knoll Bot Tests${NC}"
echo ""

# Check if we're in the right directory
if [[ ! -f "pyproject.toml" ]]; then
    echo -e "${RED}❌ Error: pyproject.toml not found. Please run this script from the project root.${NC}"
    exit 1
fi

# Install dependencies if needed
echo -e "${YELLOW}📦 Installing dependencies...${NC}"
uv sync --extra test

# Build pytest command
PYTEST_CMD="uv run pytest"

if [[ "$VERBOSE" == true ]]; then
    PYTEST_CMD="$PYTEST_CMD -v"
fi

if [[ "$COVERAGE" == true ]]; then
    PYTEST_CMD="$PYTEST_CMD --cov=src --cov-report=term-missing --cov-report=html"
fi

if [[ -n "$MARKERS" ]]; then
    PYTEST_CMD="$PYTEST_CMD -m \"$MARKERS\""
fi

if [[ -n "$EXTRA_ARGS" ]]; then
    PYTEST_CMD="$PYTEST_CMD $EXTRA_ARGS"
fi

# Run tests
echo -e "${YELLOW}🚀 Running tests...${NC}"
echo "Command: $PYTEST_CMD"
echo ""

eval $PYTEST_CMD

# Check exit status
if [[ $? -eq 0 ]]; then
    echo ""
    echo -e "${GREEN}✅ All tests passed!${NC}"
    
    if [[ "$COVERAGE" == true ]]; then
        echo ""
        echo -e "${BLUE}📊 Coverage report generated in htmlcov/index.html${NC}"
    fi
else
    echo ""
    echo -e "${RED}❌ Some tests failed!${NC}"
    exit 1
fi 