#!/bin/bash
set -e

echo "🧪 Running Family Emotions Light Test Suite"
echo "==========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default test type
TEST_TYPE=${1:-all}
COVERAGE_THRESHOLD=${2:-80}

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if dependencies are available
check_dependencies() {
    print_status "Checking dependencies..."
    
    if ! command -v poetry &> /dev/null; then
        print_error "Poetry is not installed. Please install Poetry first."
        exit 1
    fi
    
    if ! poetry show pytest &> /dev/null; then
        print_error "pytest is not installed. Run 'poetry install' first."
        exit 1
    fi
    
    print_success "Dependencies check passed"
}

# Function to check services
check_services() {
    print_status "Checking required services..."
    
    # Check PostgreSQL (optional for integration tests)
    if nc -z localhost 5432 2>/dev/null; then
        print_success "PostgreSQL is running"
    else
        print_warning "PostgreSQL is not running - integration tests may fail"
    fi
    
    # Check Redis (optional for cache tests)
    if nc -z localhost 6379 2>/dev/null; then
        print_success "Redis is running"
    else
        print_warning "Redis is not running - cache tests may fail"
    fi
}

# Function to run linting
run_linting() {
    print_status "Running code linting..."
    
    echo "📋 Running Black..."
    poetry run black --check . || {
        print_error "Black formatting check failed"
        echo "Run 'poetry run black .' to fix formatting issues"
        return 1
    }
    
    echo "📋 Running Ruff..."
    poetry run ruff check . || {
        print_error "Ruff linting failed"
        return 1
    }
    
    echo "📋 Running MyPy..."
    poetry run mypy src tests || {
        print_warning "MyPy type checking found issues"
        # Don't fail on mypy issues, just warn
    }
    
    print_success "Linting completed"
}

# Function to run unit tests
run_unit_tests() {
    print_status "Running unit tests..."
    
    poetry run pytest tests/unit -v \
        --cov=src \
        --cov-report=term-missing \
        --cov-report=html \
        --cov-report=xml \
        --cov-fail-under=${COVERAGE_THRESHOLD} \
        --junit-xml=test-results-unit.xml \
        || return 1
    
    print_success "Unit tests passed"
}

# Function to run integration tests
run_integration_tests() {
    print_status "Running integration tests..."
    
    poetry run pytest tests/integration -v \
        --cov=src \
        --cov-append \
        --cov-report=html \
        --cov-report=xml \
        --junit-xml=test-results-integration.xml \
        || return 1
    
    print_success "Integration tests passed"
}

# Function to run E2E tests
run_e2e_tests() {
    print_status "Running E2E tests..."
    
    poetry run pytest tests/e2e -v \
        --cov=src \
        --cov-append \
        --cov-report=html \
        --cov-report=xml \
        --junit-xml=test-results-e2e.xml \
        || return 1
    
    print_success "E2E tests passed"
}

# Function to run security scan
run_security_scan() {
    print_status "Running security scan..."
    
    echo "🔒 Running Bandit security scan..."
    poetry run bandit -r src/ -f txt || {
        print_warning "Bandit found security issues"
        # Don't fail on bandit issues, just warn
    }
    
    echo "🔒 Running Safety check..."
    poetry run safety check || {
        print_warning "Safety found vulnerable dependencies"
        # Don't fail on safety issues, just warn
    }
    
    print_success "Security scan completed"
}

# Function to generate coverage report
generate_coverage_report() {
    print_status "Generating coverage report..."
    
    echo "📊 Coverage Summary:"
    poetry run coverage report --show-missing
    
    echo ""
    echo "📊 HTML Coverage report generated: htmlcov/index.html"
    
    # Check if coverage meets threshold
    COVERAGE_PERCENT=$(poetry run coverage report --format=total)
    if (( $(echo "$COVERAGE_PERCENT >= $COVERAGE_THRESHOLD" | bc -l) )); then
        print_success "Coverage threshold met: ${COVERAGE_PERCENT}% >= ${COVERAGE_THRESHOLD}%"
    else
        print_error "Coverage threshold not met: ${COVERAGE_PERCENT}% < ${COVERAGE_THRESHOLD}%"
        return 1
    fi
}

# Function to run performance tests
run_performance_tests() {
    print_status "Running performance tests..."
    
    poetry run pytest tests/e2e -v \
        -m "performance" \
        --benchmark-only \
        --benchmark-json=benchmark.json \
        || {
        print_warning "Performance tests failed or not found"
        return 0  # Don't fail the entire suite
    }
    
    print_success "Performance tests completed"
}

# Function to clean up test artifacts
cleanup() {
    print_status "Cleaning up test artifacts..."
    
    rm -rf .coverage .pytest_cache .mypy_cache
    rm -f test-results-*.xml coverage.xml benchmark.json
    rm -f bandit-report.json safety-report.json
    
    print_success "Cleanup completed"
}

# Main execution
main() {
    echo "Test type: $TEST_TYPE"
    echo "Coverage threshold: $COVERAGE_THRESHOLD%"
    echo ""
    
    # Check dependencies
    check_dependencies
    
    # Check services (non-failing)
    check_services
    
    case $TEST_TYPE in
        "lint")
            run_linting
            ;;
        "unit")
            run_linting
            run_unit_tests
            generate_coverage_report
            ;;
        "integration")
            run_integration_tests
            ;;
        "e2e")
            run_e2e_tests
            ;;
        "security")
            run_security_scan
            ;;
        "performance")
            run_performance_tests
            ;;
        "coverage")
            run_unit_tests
            run_integration_tests
            run_e2e_tests
            generate_coverage_report
            ;;
        "all")
            run_linting
            run_unit_tests
            run_integration_tests
            run_e2e_tests
            generate_coverage_report
            run_security_scan
            run_performance_tests
            ;;
        *)
            print_error "Unknown test type: $TEST_TYPE"
            echo "Available types: lint, unit, integration, e2e, security, performance, coverage, all"
            exit 1
            ;;
    esac
    
    print_success "Test suite completed successfully! 🎉"
    
    # Display summary
    echo ""
    echo "📈 Summary:"
    if [[ -f "htmlcov/index.html" ]]; then
        echo "   - Coverage Report: htmlcov/index.html"
    fi
    if [[ -f "benchmark.json" ]]; then
        echo "   - Performance Results: benchmark.json"
    fi
    echo "   - Test Results: test-results-*.xml"
}

# Help function
show_help() {
    echo "Usage: $0 [TEST_TYPE] [COVERAGE_THRESHOLD]"
    echo ""
    echo "TEST_TYPE options:"
    echo "  lint         - Run only linting (black, ruff, mypy)"
    echo "  unit         - Run unit tests with coverage"
    echo "  integration  - Run integration tests"
    echo "  e2e          - Run end-to-end tests"
    echo "  security     - Run security scans (bandit, safety)"
    echo "  performance  - Run performance tests"
    echo "  coverage     - Run all tests and generate coverage report"
    echo "  all          - Run complete test suite (default)"
    echo ""
    echo "COVERAGE_THRESHOLD:"
    echo "  Minimum coverage percentage required (default: 80)"
    echo ""
    echo "Examples:"
    echo "  $0                    # Run all tests with 80% coverage threshold"
    echo "  $0 unit               # Run only unit tests"
    echo "  $0 all 90             # Run all tests with 90% coverage threshold"
    echo "  $0 lint               # Run only linting"
    echo ""
    echo "Environment setup:"
    echo "  Make sure PostgreSQL and Redis are running for integration tests"
    echo "  Set required environment variables:"
    echo "    export DATABASE_URL=postgresql://user:pass@localhost:5432/testdb"
    echo "    export REDIS_URL=redis://localhost:6379"
    echo "    export ANTHROPIC_API_KEY=your-test-key"
}

# Handle help flag
if [[ "$1" == "--help" ]] || [[ "$1" == "-h" ]]; then
    show_help
    exit 0
fi

# Trap cleanup on exit
trap cleanup EXIT

# Run main function
main