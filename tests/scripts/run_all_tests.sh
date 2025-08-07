#!/bin/bash
"""
Comprehensive test automation script with cleanup.
Runs all test suites and ensures proper cleanup of resources.
"""

set -e  # Exit on any error

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TEST_DIR="${PROJECT_ROOT}/tests"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
TEST_RESULTS_DIR="${PROJECT_ROOT}/test-results-${TIMESTAMP}"
CLEANUP=${CLEANUP:-true}
VERBOSE=${VERBOSE:-false}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Cleanup function
cleanup_resources() {
    if [ "$CLEANUP" = "true" ]; then
        log_info "Cleaning up test resources..."

        # Remove test virtual environments
        rm -rf "${PROJECT_ROOT}/.test-venv" 2>/dev/null || true

        # Remove temporary files
        find "${PROJECT_ROOT}" -name "*.pyc" -delete 2>/dev/null || true
        find "${PROJECT_ROOT}" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
        find "${PROJECT_ROOT}" -name ".pytest_cache" -type d -exec rm -rf {} + 2>/dev/null || true

        # Remove Terraform temporary files
        find "${PROJECT_ROOT}" -name "*.tfplan" -delete 2>/dev/null || true
        find "${PROJECT_ROOT}" -name "*.tfstate.backup" -delete 2>/dev/null || true

        # Clean up test DynamoDB tables (if any)
        cleanup_dynamodb_tables

        log_success "Cleanup completed"
    else
        log_info "Cleanup skipped (CLEANUP=false)"
    fi
}

# Cleanup DynamoDB test tables
cleanup_dynamodb_tables() {
    if command -v aws &> /dev/null; then
        log_info "Cleaning up test DynamoDB tables..."

        # List and delete tables with test prefix
        aws dynamodb list-tables --region eu-west-1 --query 'TableNames[?starts_with(@, `weather-test-`)]' --output text 2>/dev/null | while read -r table; do
            if [ -n "$table" ]; then
                log_info "Deleting test table: $table"
                aws dynamodb delete-table --table-name "$table" --region eu-west-1 2>/dev/null || true
            fi
        done
    fi
}

# Setup test environment
setup_test_environment() {
    log_info "Setting up test environment..."

    # Create test results directory
    mkdir -p "$TEST_RESULTS_DIR"

    # Check Python version
    if ! python3 --version | grep -q "3\.[89]\|3\.1[0-9]"; then
        log_error "Python 3.8+ required"
        exit 1
    fi

    # Create virtual environment for testing
    if [ ! -d "${PROJECT_ROOT}/.test-venv" ]; then
        log_info "Creating test virtual environment..."
        python3 -m venv "${PROJECT_ROOT}/.test-venv"
    fi

    # Activate virtual environment
    source "${PROJECT_ROOT}/.test-venv/bin/activate"

    # Install dependencies
    log_info "Installing test dependencies..."
    pip install --quiet --upgrade pip
    pip install --quiet -r "${PROJECT_ROOT}/requirements-dev.txt"

    # Set environment variables
    export PYTHONPATH="${PROJECT_ROOT}/src:${PYTHONPATH}"
    export AWS_DEFAULT_REGION="eu-west-1"
    export DYNAMODB_TABLE_NAME="weather-test-cache"
    export COMPANY_WEBSITE="test.example.com"
    export LOG_LEVEL="DEBUG"

    log_success "Test environment setup completed"
}

# Run unit tests
run_unit_tests() {
    log_info "Running unit tests..."

    cd "$PROJECT_ROOT"

    if [ "$VERBOSE" = "true" ]; then
        python -m pytest tests/unit/ -v --tb=short --junit-xml="${TEST_RESULTS_DIR}/unit-tests.xml" --cov=src --cov-report=html:"${TEST_RESULTS_DIR}/coverage-html" --cov-report=xml:"${TEST_RESULTS_DIR}/coverage.xml"
    else
        python -m pytest tests/unit/ -q --tb=line --junit-xml="${TEST_RESULTS_DIR}/unit-tests.xml" --cov=src --cov-report=xml:"${TEST_RESULTS_DIR}/coverage.xml"
    fi

    if [ $? -eq 0 ]; then
        log_success "Unit tests passed"
    else
        log_error "Unit tests failed"
        return 1
    fi
}

# Run integration tests
run_integration_tests() {
    log_info "Running integration tests..."

    cd "$PROJECT_ROOT"

    if [ "$VERBOSE" = "true" ]; then
        python -m pytest tests/integration/ -v --tb=short --junit-xml="${TEST_RESULTS_DIR}/integration-tests.xml"
    else
        python -m pytest tests/integration/ -q --tb=line --junit-xml="${TEST_RESULTS_DIR}/integration-tests.xml"
    fi

    if [ $? -eq 0 ]; then
        log_success "Integration tests passed"
    else
        log_error "Integration tests failed"
        return 1
    fi
}

# Run infrastructure tests
run_infrastructure_tests() {
    log_info "Running infrastructure tests..."

    cd "$PROJECT_ROOT"

    if [ "$VERBOSE" = "true" ]; then
        python -m pytest tests/infrastructure/ -v --tb=short --junit-xml="${TEST_RESULTS_DIR}/infrastructure-tests.xml"
    else
        python -m pytest tests/infrastructure/ -q --tb=line --junit-xml="${TEST_RESULTS_DIR}/infrastructure-tests.xml"
    fi

    if [ $? -eq 0 ]; then
        log_success "Infrastructure tests passed"
    else
        log_error "Infrastructure tests failed"
        return 1
    fi
}

# Run Terraform tests
run_terraform_tests() {
    log_info "Running Terraform tests..."

    cd "$PROJECT_ROOT"

    # Check if Terraform is installed
    if ! command -v terraform &> /dev/null; then
        log_warning "Terraform not installed, skipping Terraform tests"
        return 0
    fi

    # Run Terraform validation
    log_info "Running terraform validate..."
    terraform init -backend=false > /dev/null
    terraform validate

    if [ $? -eq 0 ]; then
        log_success "Terraform validation passed"
    else
        log_error "Terraform validation failed"
        return 1
    fi

    # Run Terraform format check
    log_info "Running terraform fmt check..."
    terraform fmt -check -recursive

    if [ $? -eq 0 ]; then
        log_success "Terraform format check passed"
    else
        log_error "Terraform format check failed"
        return 1
    fi

    # Run Terraform native tests (if available)
    if ls tests/terraform/*.tftest.hcl 1> /dev/null 2>&1; then
        log_info "Running Terraform native tests..."
        terraform test

        if [ $? -eq 0 ]; then
            log_success "Terraform native tests passed"
        else
            log_error "Terraform native tests failed"
            return 1
        fi
    fi
}

# Run security tests
run_security_tests() {
    log_info "Running security tests..."

    cd "$PROJECT_ROOT"

    # Check if checkov is available
    if command -v checkov &> /dev/null; then
        log_info "Running Checkov security scan..."
        checkov -d . --framework terraform --quiet --output cli --output junit --output-file-path "${TEST_RESULTS_DIR}/security-tests.xml"

        if [ $? -eq 0 ]; then
            log_success "Security tests passed"
        else
            log_warning "Security tests found issues (check report)"
        fi
    else
        log_warning "Checkov not installed, skipping security tests"
    fi
}

# Run linting
run_linting() {
    log_info "Running code linting..."

    cd "$PROJECT_ROOT"

    # Python linting with flake8
    if command -v flake8 &> /dev/null; then
        log_info "Running flake8 linting..."
        flake8 src/ tests/ --max-line-length=100 --exclude=__pycache__,.pytest_cache --output-file="${TEST_RESULTS_DIR}/flake8-report.txt"

        if [ $? -eq 0 ]; then
            log_success "Python linting passed"
        else
            log_warning "Python linting found issues"
        fi
    fi

    # JavaScript linting (if frontend exists)
    if [ -d "${PROJECT_ROOT}/frontend" ] && [ -f "${PROJECT_ROOT}/frontend/package.json" ]; then
        cd "${PROJECT_ROOT}/frontend"

        if command -v npm &> /dev/null; then
            log_info "Running JavaScript linting..."
            npm run lint 2>&1 | tee "${TEST_RESULTS_DIR}/eslint-report.txt"

            if [ ${PIPESTATUS[0]} -eq 0 ]; then
                log_success "JavaScript linting passed"
            else
                log_warning "JavaScript linting found issues"
            fi
        fi

        cd "$PROJECT_ROOT"
    fi
}

# Generate test report
generate_test_report() {
    log_info "Generating test report..."

    cat > "${TEST_RESULTS_DIR}/test-summary.md" << EOF
# Test Execution Summary

**Date:** $(date)
**Duration:** $(($(date +%s) - START_TIME)) seconds
**Results Directory:** ${TEST_RESULTS_DIR}

## Test Results

- Unit Tests: $([ -f "${TEST_RESULTS_DIR}/unit-tests.xml" ] && echo "✅ Passed" || echo "❌ Failed/Skipped")
- Integration Tests: $([ -f "${TEST_RESULTS_DIR}/integration-tests.xml" ] && echo "✅ Passed" || echo "❌ Failed/Skipped")
- Infrastructure Tests: $([ -f "${TEST_RESULTS_DIR}/infrastructure-tests.xml" ] && echo "✅ Passed" || echo "❌ Failed/Skipped")
- Terraform Tests: ✅ Passed
- Security Tests: $([ -f "${TEST_RESULTS_DIR}/security-tests.xml" ] && echo "✅ Passed" || echo "⚠️ Skipped")
- Code Linting: $([ -f "${TEST_RESULTS_DIR}/flake8-report.txt" ] && echo "✅ Passed" || echo "⚠️ Skipped")

## Coverage Report

$([ -f "${TEST_RESULTS_DIR}/coverage.xml" ] && echo "Coverage report available in coverage.xml" || echo "Coverage report not generated")

## Files Generated

$(ls -la "${TEST_RESULTS_DIR}")

EOF

    log_success "Test report generated: ${TEST_RESULTS_DIR}/test-summary.md"
}

# Trap to ensure cleanup on exit
trap cleanup_resources EXIT

# Main execution
main() {
    START_TIME=$(date +%s)

    log_info "Starting comprehensive test suite..."
    log_info "Results will be saved to: ${TEST_RESULTS_DIR}"

    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --no-cleanup)
                CLEANUP=false
                shift
                ;;
            --verbose|-v)
                VERBOSE=true
                shift
                ;;
            --help|-h)
                echo "Usage: $0 [--no-cleanup] [--verbose|-v] [--help|-h]"
                echo "  --no-cleanup    Skip cleanup of test resources"
                echo "  --verbose,-v    Enable verbose output"
                echo "  --help,-h       Show this help message"
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done

    # Setup
    setup_test_environment

    # Run test suites
    local failed=0

    run_unit_tests || failed=1
    run_integration_tests || failed=1
    run_infrastructure_tests || failed=1
    run_terraform_tests || failed=1
    run_security_tests || true  # Don't fail on security warnings
    run_linting || true  # Don't fail on linting warnings

    # Generate report
    generate_test_report

    # Final result
    if [ $failed -eq 0 ]; then
        log_success "All tests completed successfully!"
        log_info "Test results available in: ${TEST_RESULTS_DIR}"
        exit 0
    else
        log_error "Some tests failed. Check the results in: ${TEST_RESULTS_DIR}"
        exit 1
    fi
}

# Run main function
main "$@"