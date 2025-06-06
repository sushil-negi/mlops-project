#!/bin/bash

# Quick Test Script for Demo LLM
# Tests the deployed model with various scenarios

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

# Configuration
MODEL_URL=${MODEL_URL:-"http://localhost:8080"}
NAMESPACE=${NAMESPACE:-"mlops-platform"}
SERVICE_NAME=${SERVICE_NAME:-"demo-llm-staging"}

print_test() {
    echo -e "${BLUE}[TEST]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[PASS]${NC} $1"
}

print_error() {
    echo -e "${RED}[FAIL]${NC} $1"
}

# Function to setup port forwarding
setup_port_forward() {
    print_test "Setting up port forwarding..."
    
    # Check if service exists
    if ! kubectl get service $SERVICE_NAME -n $NAMESPACE &>/dev/null; then
        print_error "Service $SERVICE_NAME not found in namespace $NAMESPACE"
        echo "Available services:"
        kubectl get services -n $NAMESPACE
        exit 1
    fi
    
    # Start port forwarding in background
    kubectl port-forward -n $NAMESPACE svc/$SERVICE_NAME 8080:8000 &
    PORT_FORWARD_PID=$!
    
    # Wait for port forward to be ready
    sleep 3
    
    # Test if port is accessible
    if ! curl -s http://localhost:8080/health > /dev/null; then
        print_error "Could not connect to service via port forwarding"
        kill $PORT_FORWARD_PID 2>/dev/null || true
        exit 1
    fi
    
    MODEL_URL="http://localhost:8080"
    print_success "Port forwarding setup complete"
}

# Function to test health endpoint
test_health() {
    print_test "Testing health endpoint..."
    
    RESPONSE=$(curl -s $MODEL_URL/health)
    STATUS=$(echo $RESPONSE | jq -r '.status' 2>/dev/null || echo "error")
    
    if [ "$STATUS" = "healthy" ]; then
        print_success "Health check passed"
        echo "  Model loaded: $(echo $RESPONSE | jq -r '.model_loaded')"
    else
        print_error "Health check failed: $RESPONSE"
        return 1
    fi
}

# Function to test model info
test_model_info() {
    print_test "Testing model info endpoint..."
    
    RESPONSE=$(curl -s $MODEL_URL/model/info)
    MODEL_NAME=$(echo $RESPONSE | jq -r '.model_name' 2>/dev/null || echo "error")
    
    if [ "$MODEL_NAME" != "error" ] && [ "$MODEL_NAME" != "null" ]; then
        print_success "Model info retrieved"
        echo "  Model: $MODEL_NAME"
        echo "  Parameters: $(echo $RESPONSE | jq -r '.parameters' 2>/dev/null || echo 'unknown')"
    else
        print_error "Model info test failed: $RESPONSE"
        return 1
    fi
}

# Function to test text generation
test_generation() {
    local input_text="$1"
    local max_length="${2:-100}"
    
    print_test "Testing generation: '$input_text'"
    
    REQUEST_DATA=$(jq -n \
        --arg text "$input_text" \
        --argjson max_length $max_length \
        '{text: $text, max_length: $max_length, temperature: 0.7}')
    
    RESPONSE=$(curl -s -X POST "$MODEL_URL/generate" \
        -H "Content-Type: application/json" \
        -d "$REQUEST_DATA")
    
    GENERATED_TEXT=$(echo $RESPONSE | jq -r '.generated_text[0]' 2>/dev/null)
    
    if [ "$GENERATED_TEXT" != "null" ] && [ "$GENERATED_TEXT" != "error" ] && [ -n "$GENERATED_TEXT" ]; then
        print_success "Generation test passed"
        echo "  Input: $input_text"
        echo "  Output: ${GENERATED_TEXT:0:100}..."
        echo "  Generation time: $(echo $RESPONSE | jq -r '.generation_time' 2>/dev/null || echo 'unknown')s"
    else
        print_error "Generation test failed: $RESPONSE"
        return 1
    fi
}

# Function to test batch generation
test_batch_generation() {
    print_test "Testing batch generation..."
    
    REQUEST_DATA=$(jq -n \
        '{texts: ["The future of AI", "Machine learning will", "Technology enables"], max_length: 50}')
    
    RESPONSE=$(curl -s -X POST "$MODEL_URL/generate/batch" \
        -H "Content-Type: application/json" \
        -d "$REQUEST_DATA")
    
    RESULTS_COUNT=$(echo $RESPONSE | jq '.results | length' 2>/dev/null || echo 0)
    
    if [ "$RESULTS_COUNT" -eq 3 ]; then
        print_success "Batch generation test passed"
        echo "  Processed $RESULTS_COUNT texts"
        echo "  Total time: $(echo $RESPONSE | jq -r '.generation_time' 2>/dev/null || echo 'unknown')s"
    else
        print_error "Batch generation test failed: $RESPONSE"
        return 1
    fi
}

# Function to test metrics endpoint
test_metrics() {
    print_test "Testing metrics endpoint..."
    
    RESPONSE=$(curl -s $MODEL_URL/metrics)
    TOTAL_REQUESTS=$(echo $RESPONSE | jq -r '.total_requests' 2>/dev/null || echo "error")
    
    if [ "$TOTAL_REQUESTS" != "error" ] && [ "$TOTAL_REQUESTS" != "null" ]; then
        print_success "Metrics test passed"
        echo "  Total requests: $TOTAL_REQUESTS"
        echo "  Average response time: $(echo $RESPONSE | jq -r '.average_response_time' 2>/dev/null || echo 'unknown')s"
        echo "  Error rate: $(echo $RESPONSE | jq -r '.error_rate' 2>/dev/null || echo 'unknown')"
    else
        print_error "Metrics test failed: $RESPONSE"
        return 1
    fi
}

# Function to test error handling
test_error_handling() {
    print_test "Testing error handling..."
    
    # Test with invalid request
    RESPONSE=$(curl -s -X POST "$MODEL_URL/generate" \
        -H "Content-Type: application/json" \
        -d '{"invalid": "request"}')
    
    # Should return 422 for validation error
    if echo $RESPONSE | jq -e '.error' > /dev/null 2>&1; then
        print_success "Error handling test passed"
        echo "  Properly handles invalid requests"
    else
        print_error "Error handling test failed: $RESPONSE"
        return 1
    fi
}

# Function to run performance test
test_performance() {
    print_test "Running performance test (10 requests)..."
    
    local total_time=0
    local success_count=0
    local start_time=$(date +%s.%N)
    
    for i in {1..10}; do
        REQUEST_START=$(date +%s.%N)
        
        RESPONSE=$(curl -s -X POST "$MODEL_URL/generate" \
            -H "Content-Type: application/json" \
            -d '{"text": "Performance test", "max_length": 30}' 2>/dev/null)
        
        REQUEST_END=$(date +%s.%N)
        
        if echo $RESPONSE | jq -e '.generated_text' > /dev/null 2>&1; then
            success_count=$((success_count + 1))
        fi
        
        REQUEST_TIME=$(echo "$REQUEST_END - $REQUEST_START" | bc -l)
        total_time=$(echo "$total_time + $REQUEST_TIME" | bc -l)
        
        echo -n "."
    done
    echo ""
    
    local end_time=$(date +%s.%N)
    local total_elapsed=$(echo "$end_time - $start_time" | bc -l)
    local avg_time=$(echo "scale=3; $total_time / 10" | bc -l)
    local throughput=$(echo "scale=2; 10 / $total_elapsed" | bc -l)
    
    if [ $success_count -eq 10 ]; then
        print_success "Performance test passed"
        echo "  Success rate: 100% (10/10)"
        echo "  Average response time: ${avg_time}s"
        echo "  Throughput: ${throughput} req/s"
    else
        print_error "Performance test failed: $success_count/10 successful"
        return 1
    fi
}

# Function to cleanup
cleanup() {
    if [ -n "$PORT_FORWARD_PID" ]; then
        kill $PORT_FORWARD_PID 2>/dev/null || true
        print_test "Cleaned up port forwarding"
    fi
}

# Function to run all tests
run_all_tests() {
    echo "🧪 Demo LLM Model Test Suite"
    echo "============================="
    echo "Target: $MODEL_URL"
    echo "Service: $SERVICE_NAME"
    echo "Namespace: $NAMESPACE"
    echo ""
    
    local failed_tests=0
    
    # Basic functionality tests
    test_health || failed_tests=$((failed_tests + 1))
    test_model_info || failed_tests=$((failed_tests + 1))
    
    # Generation tests
    test_generation "The future of machine learning is" 100 || failed_tests=$((failed_tests + 1))
    test_generation "Artificial intelligence will" 50 || failed_tests=$((failed_tests + 1))
    test_generation "Deep learning models can" 75 || failed_tests=$((failed_tests + 1))
    
    # Advanced tests
    test_batch_generation || failed_tests=$((failed_tests + 1))
    test_metrics || failed_tests=$((failed_tests + 1))
    test_error_handling || failed_tests=$((failed_tests + 1))
    
    # Performance test
    test_performance || failed_tests=$((failed_tests + 1))
    
    echo ""
    echo "============================="
    if [ $failed_tests -eq 0 ]; then
        print_success "All tests passed! 🎉"
        echo "The demo LLM model is working correctly."
    else
        print_error "$failed_tests test(s) failed ❌"
        echo "Please check the logs and fix any issues."
        return 1
    fi
    echo "============================="
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS] [TEST]"
    echo ""
    echo "Tests:"
    echo "  all                 Run all tests (default)"
    echo "  health              Test health endpoint"
    echo "  info                Test model info endpoint"
    echo "  generate            Test text generation"
    echo "  batch               Test batch generation"
    echo "  metrics             Test metrics endpoint"
    echo "  performance         Run performance test"
    echo ""
    echo "Options:"
    echo "  --url URL                   Model URL (default: auto port-forward)"
    echo "  --service NAME              Service name (default: demo-llm-staging)"
    echo "  --namespace NAMESPACE       Namespace (default: mlops-platform)"
    echo "  --no-port-forward          Don't setup port forwarding"
    echo "  --help                      Show this help"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Run all tests with auto port-forward"
    echo "  $0 --url http://localhost:8080       # Test specific URL"
    echo "  $0 generate                          # Test only generation"
    echo "  $0 --service demo-llm-production all # Test production service"
}

# Parse arguments
TEST_TYPE="all"
SETUP_PORT_FORWARD=true

while [[ $# -gt 0 ]]; do
    case $1 in
        --url)
            MODEL_URL="$2"
            SETUP_PORT_FORWARD=false
            shift 2
            ;;
        --service)
            SERVICE_NAME="$2"
            shift 2
            ;;
        --namespace)
            NAMESPACE="$2"
            shift 2
            ;;
        --no-port-forward)
            SETUP_PORT_FORWARD=false
            shift
            ;;
        --help)
            show_usage
            exit 0
            ;;
        all|health|info|generate|batch|metrics|performance)
            TEST_TYPE="$1"
            shift
            ;;
        *)
            echo "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Check prerequisites
if ! command -v curl &> /dev/null; then
    print_error "curl is required but not installed"
    exit 1
fi

if ! command -v jq &> /dev/null; then
    print_error "jq is required but not installed"
    exit 1
fi

if ! command -v bc &> /dev/null; then
    print_error "bc is required but not installed"
    exit 1
fi

# Setup cleanup on exit
trap cleanup EXIT

# Setup port forwarding if needed
if [ "$SETUP_PORT_FORWARD" = true ]; then
    setup_port_forward
fi

# Run tests
case $TEST_TYPE in
    all)
        run_all_tests
        ;;
    health)
        test_health
        ;;
    info)
        test_model_info
        ;;
    generate)
        test_generation "The future of AI is" 100
        ;;
    batch)
        test_batch_generation
        ;;
    metrics)
        test_metrics
        ;;
    performance)
        test_performance
        ;;
    *)
        echo "Unknown test type: $TEST_TYPE"
        show_usage
        exit 1
        ;;
esac