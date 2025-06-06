#!/bin/bash

# Cirruslabs MLOps Demo Pipeline Runner
# Automated script to run the complete demo LLM pipeline

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
MODEL_NAME=${MODEL_NAME:-"demo-llm"}
MODEL_VERSION=${MODEL_VERSION:-"1.0.0"}
EXPERIMENT_NAME=${EXPERIMENT_NAME:-"demo-llm-experiment-$(date +%Y%m%d-%H%M%S)"}
NAMESPACE=${NAMESPACE:-"mlops-platform"}
REGISTRY_URL=${REGISTRY_URL:-"http://model-registry:8000"}

# Function to print colored output
print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
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

# Function to check prerequisites
check_prerequisites() {
    print_step "Checking prerequisites..."
    
    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        print_error "kubectl is not installed"
        exit 1
    fi
    
    # Check argo
    if ! command -v argo &> /dev/null; then
        print_error "argo CLI is not installed"
        exit 1
    fi
    
    # Check docker
    if ! command -v docker &> /dev/null; then
        print_error "docker is not installed"
        exit 1
    fi
    
    # Check namespace exists
    if ! kubectl get namespace $NAMESPACE &> /dev/null; then
        print_error "Namespace $NAMESPACE does not exist"
        exit 1
    fi
    
    print_success "Prerequisites check passed"
}

# Function to build and push model image
build_model_image() {
    print_step "Building demo LLM Docker image..."
    
    cd models/demo-llm
    
    # Build image
    docker build -t demo-llm:latest .
    docker tag demo-llm:latest demo-llm:${MODEL_VERSION}
    
    # If using local registry, push there
    if [[ "${REGISTRY_URL}" == *"localhost"* ]] || [[ "${REGISTRY_URL}" == *"127.0.0.1"* ]]; then
        docker tag demo-llm:latest localhost:5000/demo-llm:latest
        docker tag demo-llm:latest localhost:5000/demo-llm:${MODEL_VERSION}
        docker push localhost:5000/demo-llm:latest
        docker push localhost:5000/demo-llm:${MODEL_VERSION}
    fi
    
    cd - > /dev/null
    print_success "Model image built and pushed"
}

# Function to submit training pipeline
submit_training_pipeline() {
    print_step "Submitting training pipeline..."
    
    # Submit pipeline with parameters
    WORKFLOW_NAME=$(argo submit models/demo-llm/pipelines/training_pipeline.yaml \
        --parameter model-name=${MODEL_NAME} \
        --parameter model-version=${MODEL_VERSION} \
        --parameter experiment-name=${EXPERIMENT_NAME} \
        --parameter registry-url=${REGISTRY_URL} \
        --parameter max-epochs=3 \
        --parameter batch-size=4 \
        --parameter learning-rate=5e-5 \
        -o name)
    
    echo "Pipeline submitted: $WORKFLOW_NAME"
    echo "Experiment: $EXPERIMENT_NAME"
    
    # Wait for pipeline to complete
    print_step "Waiting for pipeline to complete..."
    argo wait $WORKFLOW_NAME
    
    # Check if pipeline succeeded
    STATUS=$(argo get $WORKFLOW_NAME -o json | jq -r '.status.phase')
    
    if [ "$STATUS" = "Succeeded" ]; then
        print_success "Training pipeline completed successfully"
        
        # Get model ID from pipeline output
        MODEL_ID=$(argo get $WORKFLOW_NAME -o json | jq -r '.status.nodes[] | select(.displayName=="register-model") | .outputs.parameters[] | select(.name=="model-id") | .value' 2>/dev/null || echo "")
        
        if [ -n "$MODEL_ID" ]; then
            echo "Model ID: $MODEL_ID"
            echo $MODEL_ID > .model_id
        fi
        
    else
        print_error "Training pipeline failed with status: $STATUS"
        argo logs $WORKFLOW_NAME
        exit 1
    fi
}

# Function to deploy model to staging
deploy_to_staging() {
    print_step "Deploying model to staging environment..."
    
    # Create staging deployment manifest
    cat > staging-deployment.yaml << EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ${MODEL_NAME}-staging
  namespace: ${NAMESPACE}
  labels:
    app: ${MODEL_NAME}
    environment: staging
    version: "${MODEL_VERSION}"
spec:
  replicas: 2
  selector:
    matchLabels:
      app: ${MODEL_NAME}
      environment: staging
  template:
    metadata:
      labels:
        app: ${MODEL_NAME}
        environment: staging
        version: "${MODEL_VERSION}"
    spec:
      containers:
      - name: ${MODEL_NAME}
        image: demo-llm:${MODEL_VERSION}
        ports:
        - containerPort: 8000
        env:
        - name: ENVIRONMENT
          value: "staging"
        - name: MODEL_NAME
          value: "${MODEL_NAME}"
        - name: MODEL_VERSION
          value: "${MODEL_VERSION}"
        resources:
          requests:
            cpu: 500m
            memory: 1Gi
          limits:
            cpu: 1000m
            memory: 2Gi
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: ${MODEL_NAME}-staging
  namespace: ${NAMESPACE}
  labels:
    app: ${MODEL_NAME}
    environment: staging
spec:
  selector:
    app: ${MODEL_NAME}
    environment: staging
  ports:
  - port: 8000
    targetPort: 8000
    protocol: TCP
  type: ClusterIP
EOF

    # Apply deployment
    kubectl apply -f staging-deployment.yaml
    
    # Wait for deployment to be ready
    kubectl rollout status deployment/${MODEL_NAME}-staging -n ${NAMESPACE} --timeout=300s
    
    print_success "Model deployed to staging"
    
    # Clean up temporary file
    rm -f staging-deployment.yaml
}

# Function to test staging deployment
test_staging_deployment() {
    print_step "Testing staging deployment..."
    
    # Port forward in background
    kubectl port-forward -n ${NAMESPACE} svc/${MODEL_NAME}-staging 8080:8000 &
    PORT_FORWARD_PID=$!
    
    # Wait for port forward to be ready
    sleep 5
    
    # Test health endpoint
    if curl -f http://localhost:8080/health > /dev/null 2>&1; then
        print_success "Health check passed"
    else
        print_error "Health check failed"
        kill $PORT_FORWARD_PID 2>/dev/null || true
        exit 1
    fi
    
    # Test inference endpoint
    INFERENCE_RESULT=$(curl -s -X POST "http://localhost:8080/generate" \
         -H "Content-Type: application/json" \
         -d '{
           "text": "The future of machine learning is",
           "max_length": 50,
           "temperature": 0.7
         }')
    
    if echo "$INFERENCE_RESULT" | jq -e '.generated_text' > /dev/null 2>&1; then
        print_success "Inference test passed"
        echo "Sample output: $(echo "$INFERENCE_RESULT" | jq -r '.generated_text[0]' | head -c 100)..."
    else
        print_error "Inference test failed"
        echo "Response: $INFERENCE_RESULT"
        kill $PORT_FORWARD_PID 2>/dev/null || true
        exit 1
    fi
    
    # Stop port forward
    kill $PORT_FORWARD_PID 2>/dev/null || true
    
    print_success "Staging deployment tests passed"
}

# Function to setup monitoring
setup_monitoring() {
    print_step "Setting up monitoring..."
    
    # Create ServiceMonitor for Prometheus scraping
    cat > model-monitoring.yaml << EOF
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: ${MODEL_NAME}-monitor
  namespace: ${NAMESPACE}
  labels:
    app: ${MODEL_NAME}
spec:
  selector:
    matchLabels:
      app: ${MODEL_NAME}
  endpoints:
  - port: http
    path: /metrics
    interval: 30s
---
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: ${MODEL_NAME}-alerts
  namespace: ${NAMESPACE}
spec:
  groups:
  - name: ${MODEL_NAME}
    rules:
    - alert: ModelHighErrorRate
      expr: rate(demo_llm_errors_total[5m]) > 0.1
      for: 2m
      labels:
        severity: warning
        model: ${MODEL_NAME}
      annotations:
        summary: "High error rate detected in ${MODEL_NAME}"
        description: "Error rate is {{ \$value }} errors per second"
    
    - alert: ModelHighLatency
      expr: histogram_quantile(0.95, rate(demo_llm_duration_seconds_bucket[5m])) > 2
      for: 5m
      labels:
        severity: warning
        model: ${MODEL_NAME}
      annotations:
        summary: "High latency detected in ${MODEL_NAME}"
        description: "95th percentile latency is {{ \$value }} seconds"
EOF

    kubectl apply -f model-monitoring.yaml 2>/dev/null || print_warning "Could not set up monitoring (ServiceMonitor/PrometheusRule may not be available)"
    
    # Clean up
    rm -f model-monitoring.yaml
    
    print_success "Monitoring setup completed"
}

# Function to show dashboard URLs
show_dashboard_urls() {
    print_step "Setting up dashboard access..."
    
    echo ""
    echo "==============================================="
    echo "🎉 Demo Pipeline Completed Successfully!"
    echo "==============================================="
    echo ""
    echo "Model Information:"
    echo "  Name: $MODEL_NAME"
    echo "  Version: $MODEL_VERSION"
    echo "  Experiment: $EXPERIMENT_NAME"
    echo ""
    echo "Access your model and monitoring dashboards:"
    echo ""
    echo "1. Model API (staging):"
    echo "   kubectl port-forward -n $NAMESPACE svc/$MODEL_NAME-staging 8080:8000"
    echo "   Then visit: http://localhost:8080/docs"
    echo ""
    echo "2. Model Registry:"
    echo "   kubectl port-forward -n $NAMESPACE svc/model-registry 8081:8000"
    echo "   Then visit: http://localhost:8081/docs"
    echo ""
    echo "3. MLflow (experiment tracking):"
    echo "   kubectl port-forward -n $NAMESPACE svc/mlflow 5000:5000"
    echo "   Then visit: http://localhost:5000"
    echo ""
    echo "4. Grafana (monitoring):"
    echo "   kubectl port-forward -n $NAMESPACE svc/grafana 3000:3000"
    echo "   Then visit: http://localhost:3000 (admin/admin123)"
    echo ""
    echo "5. Argo Workflows:"
    echo "   kubectl port-forward -n argo svc/argo-server 2746:2746"
    echo "   Then visit: http://localhost:2746"
    echo ""
    echo "Test your model:"
    echo "  curl -X POST 'http://localhost:8080/generate' \\"
    echo "       -H 'Content-Type: application/json' \\"
    echo "       -d '{\"text\": \"The future of AI is\", \"max_length\": 100}'"
    echo ""
    echo "==============================================="
}

# Function to run complete pipeline
run_complete_pipeline() {
    echo "🚀 Starting Cirruslabs MLOps Demo Pipeline"
    echo "==========================================="
    echo "Model: $MODEL_NAME v$MODEL_VERSION"
    echo "Experiment: $EXPERIMENT_NAME"
    echo "Namespace: $NAMESPACE"
    echo ""
    
    check_prerequisites
    build_model_image
    submit_training_pipeline
    deploy_to_staging
    test_staging_deployment
    setup_monitoring
    show_dashboard_urls
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS] [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  run                 Run complete pipeline (default)"
    echo "  build               Build model image only"
    echo "  train               Submit training pipeline only"
    echo "  deploy              Deploy to staging only"
    echo "  test                Test staging deployment only"
    echo "  monitor             Setup monitoring only"
    echo "  status              Show pipeline status"
    echo "  cleanup             Clean up resources"
    echo ""
    echo "Options:"
    echo "  --model-name NAME           Model name (default: demo-llm)"
    echo "  --model-version VERSION     Model version (default: 1.0.0)"
    echo "  --namespace NAMESPACE       Kubernetes namespace (default: mlops-platform)"
    echo "  --registry-url URL          Model registry URL"
    echo "  --help                      Show this help"
    echo ""
    echo "Environment Variables:"
    echo "  MODEL_NAME, MODEL_VERSION, NAMESPACE, REGISTRY_URL"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Run complete pipeline"
    echo "  $0 --model-version 1.1.0 train       # Train new model version"
    echo "  $0 deploy                             # Deploy existing model"
}

# Function to show status
show_status() {
    print_step "Checking pipeline status..."
    
    echo ""
    echo "MLOps Platform Services:"
    kubectl get pods -n $NAMESPACE -l app.kubernetes.io/part-of=mlops-platform
    
    echo ""
    echo "Model Deployments:"
    kubectl get deployments -n $NAMESPACE -l app=$MODEL_NAME
    
    echo ""
    echo "Recent Workflows:"
    argo list | head -10
    
    if [ -f .model_id ]; then
        MODEL_ID=$(cat .model_id)
        echo ""
        echo "Latest Model ID: $MODEL_ID"
    fi
}

# Function to cleanup resources
cleanup_resources() {
    print_step "Cleaning up demo resources..."
    
    # Delete model deployments
    kubectl delete deployment -n $NAMESPACE -l app=$MODEL_NAME --ignore-not-found
    kubectl delete service -n $NAMESPACE -l app=$MODEL_NAME --ignore-not-found
    kubectl delete servicemonitor -n $NAMESPACE -l app=$MODEL_NAME --ignore-not-found 2>/dev/null || true
    kubectl delete prometheusrule -n $NAMESPACE -l app=$MODEL_NAME --ignore-not-found 2>/dev/null || true
    
    # Clean up local files
    rm -f .model_id staging-deployment.yaml model-monitoring.yaml
    
    print_success "Cleanup completed"
}

# Parse command line arguments
COMMAND="run"
while [[ $# -gt 0 ]]; do
    case $1 in
        --model-name)
            MODEL_NAME="$2"
            shift 2
            ;;
        --model-version)
            MODEL_VERSION="$2"
            shift 2
            ;;
        --namespace)
            NAMESPACE="$2"
            shift 2
            ;;
        --registry-url)
            REGISTRY_URL="$2"
            shift 2
            ;;
        --help)
            show_usage
            exit 0
            ;;
        run|build|train|deploy|test|monitor|status|cleanup)
            COMMAND="$1"
            shift
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Execute command
case $COMMAND in
    run)
        run_complete_pipeline
        ;;
    build)
        check_prerequisites
        build_model_image
        ;;
    train)
        check_prerequisites
        submit_training_pipeline
        ;;
    deploy)
        check_prerequisites
        deploy_to_staging
        ;;
    test)
        test_staging_deployment
        ;;
    monitor)
        setup_monitoring
        ;;
    status)
        show_status
        ;;
    cleanup)
        cleanup_resources
        ;;
    *)
        print_error "Unknown command: $COMMAND"
        show_usage
        exit 1
        ;;
esac