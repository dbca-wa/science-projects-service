#!/bin/bash
# Test runner with optimized output and parallel execution
# Usage: ./run_tests.sh [app_name] [options]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default settings
APP=""
VERBOSE=false
COVERAGE=true
PARALLEL=true
WORKERS="auto"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        --no-coverage)
            COVERAGE=false
            shift
            ;;
        --no-parallel)
            PARALLEL=false
            shift
            ;;
        -n|--workers)
            WORKERS="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: ./run_tests.sh [app_name] [options]"
            echo ""
            echo "Options:"
            echo "  -v, --verbose       Show verbose output"
            echo "  --no-coverage       Skip coverage reporting"
            echo "  --no-parallel       Run tests sequentially"
            echo "  -n, --workers N     Number of parallel workers (default: auto)"
            echo "  -h, --help          Show this help message"
            echo ""
            echo "Examples:"
            echo "  ./run_tests.sh                    # Run all tests"
            echo "  ./run_tests.sh documents          # Run documents app tests"
            echo "  ./run_tests.sh documents -v       # Run with verbose output"
            echo "  ./run_tests.sh --no-parallel      # Run sequentially"
            exit 0
            ;;
        *)
            APP="$1"
            shift
            ;;
    esac
done

# Build pytest command
CMD="poetry run pytest"

# Add app path if specified
if [ -n "$APP" ]; then
    CMD="$CMD $APP/tests"
fi

# Add parallel execution
if [ "$PARALLEL" = true ]; then
    CMD="$CMD -n $WORKERS"
fi

# Add coverage options
if [ "$COVERAGE" = true ]; then
    if [ -n "$APP" ]; then
        CMD="$CMD --cov=$APP --cov-report=term-missing:skip-covered --cov-report=html"
    else
        CMD="$CMD --cov=. --cov-report=term-missing:skip-covered --cov-report=html"
    fi
fi

# Add verbosity
if [ "$VERBOSE" = true ]; then
    CMD="$CMD -v"
else
    CMD="$CMD -q"
fi

# Add output options
CMD="$CMD --tb=short --no-header --disable-warnings"

# Create test results directory
mkdir -p test_results

# Run tests and capture output
echo -e "${YELLOW}Running tests...${NC}"
echo "Command: $CMD"
echo ""

# Run tests and save detailed output to file
if $CMD 2>&1 | tee test_results/last_run.log; then
    echo ""
    echo -e "${GREEN}✓ All tests passed!${NC}"
    
    # Extract and show summary
    if [ "$COVERAGE" = true ]; then
        echo ""
        echo -e "${YELLOW}Coverage Summary:${NC}"
        tail -20 test_results/last_run.log | grep -A 20 "TOTAL" || true
    fi
    
    # Show skipped tests if any
    if grep -q "SKIPPED\|skipped" test_results/last_run.log; then
        echo ""
        echo -e "${YELLOW}Skipped Tests:${NC}"
        grep -E "SKIPPED|skipped" test_results/last_run.log | grep -v "files skipped" || true
    fi
    
    exit 0
else
    EXIT_CODE=$?
    echo ""
    echo -e "${RED}✗ Tests failed!${NC}"
    echo ""
    echo -e "${YELLOW}Failed tests saved to: test_results/last_run.log${NC}"
    echo ""
    
    # Extract and show failures
    echo -e "${RED}Failures:${NC}"
    grep -A 10 "FAILED\|ERROR" test_results/last_run.log | head -50 || true
    
    # Extract and show skipped tests
    if grep -q "SKIPPED" test_results/last_run.log; then
        echo ""
        echo -e "${YELLOW}Skipped Tests:${NC}"
        grep "SKIPPED" test_results/last_run.log | head -20 || true
    fi
    
    # Save failures to separate file
    grep -A 10 "FAILED\|ERROR" test_results/last_run.log > test_results/failures.log 2>/dev/null || true
    
    # Save skipped to separate file
    grep "SKIPPED" test_results/last_run.log > test_results/skipped.log 2>/dev/null || true
    
    exit $EXIT_CODE
fi
