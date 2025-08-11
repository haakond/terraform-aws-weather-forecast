#!/bin/bash

# Comprehensive test runner script
# Runs all tests in non-interactive mode suitable for CI/CD

set -e

echo "🧪 Running comprehensive test suite..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    local status=$1
    local message=$2
    case $status in
        "success")
            echo -e "${GREEN}✅ $message${NC}"
            ;;
        "error")
            echo -e "${RED}❌ $message${NC}"
            ;;
        "warning")
            echo -e "${YELLOW}⚠️  $message${NC}"
            ;;
        "info")
            echo -e "ℹ️  $message"
            ;;
    esac
}

# Track test results
TESTS_PASSED=0
TESTS_FAILED=0

# Function to run a test and track results
run_test() {
    local test_name=$1
    local test_command=$2

    print_status "info" "Running $test_name..."

    if eval "$test_command"; then
        print_status "success" "$test_name passed"
        ((TESTS_PASSED++))
        return 0
    else
        print_status "error" "$test_name failed"
        ((TESTS_FAILED++))
        return 1
    fi
}

# 1. Frontend Unit Tests
print_status "info" "=== Frontend Unit Tests ==="
if [ -d "frontend" ]; then
    cd frontend

    # Install dependencies if needed
    if [ ! -d "node_modules" ]; then
        print_status "info" "Installing frontend dependencies..."
        npm ci --silent
    fi

    # Run tests in non-interactive mode
    run_test "Frontend Unit Tests" "npm run test:ci"

    cd ..
else
    print_status "warning" "Frontend directory not found, skipping frontend tests"
fi# 2. P
ython Unit Tests
print_status "info" "=== Python Unit Tests ==="
if [ -d "tests/unit" ]; then
    cd tests/unit

    # Set up Python virtual environment if needed
    if [ ! -d "venv" ]; then
        print_status "info" "Setting up Python virtual environment..."
        python3 -m venv venv
        source venv/bin/activate
        pip install -r ../../requirements.txt 2>/dev/null || pip install boto3 pytest
    else
        source venv/bin/activate
    fi

    # Run Python tests
    run_test "Python Unit Tests" "python -m pytest test_lambda_handler.py -v"

    deactivate
    cd ../..
else
    print_status "warning" "Python unit tests directory not found, skipping Python tests"
fi

# 3. Terraform Validation Tests
print_status "info" "=== Terraform Validation Tests ==="
if [ -d "tests/terraform" ]; then
    cd tests/terraform

    # Run Terraform validation scripts
    run_test "Frontend Module Validation" "./validate_frontend.sh"
    run_test "Lambda Module Validation" "./validate_lambda.sh"
    run_test "API Gateway Validation" "./validate_api_gateway.sh"
    run_test "Monitoring Validation" "./validate_monitoring.sh"
    run_test "CloudFront Configuration Validation" "./validate_cloudfront_config.sh"

    cd ../..
else
    print_status "warning" "Terraform tests directory not found, skipping Terraform validation"
fi

# 4. Cache Header Validation
print_status "info" "=== Cache Header Validation ==="
if [ -d "frontend" ] && [ -f "frontend/scripts/validate-cache-headers.js" ]; then
    cd frontend

    # Build the frontend first if build directory doesn't exist
    if [ ! -d "build" ]; then
        print_status "info" "Building frontend for cache validation..."
        npm run build:optimized
    fi

    # Validate cache headers
    run_test "Cache Header Validation" "npm run validate:cache"

    cd ..
else
    print_status "warning" "Frontend cache validation script not found, skipping cache validation"
fi

# Summary
print_status "info" "=== Test Summary ==="
echo "Tests passed: $TESTS_PASSED"
echo "Tests failed: $TESTS_FAILED"

if [ $TESTS_FAILED -eq 0 ]; then
    print_status "success" "All tests passed! 🎉"
    exit 0
else
    print_status "error" "Some tests failed. Please review the output above."
    exit 1
fi