#!/bin/bash

# Healthcare AI MLOps Platform Deployment Script
# Supports Docker Compose and Kubernetes deployments for dev, staging, and production

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
ENVIRONMENT="dev"
PLATFORM="docker"
ACTION="deploy"

print_usage() {
    echo "Healthcare AI MLOps Platform Deployment Script"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -e, --environment   Environment to deploy (dev|staging|production) [default: dev]"
    echo "  -p, --platform      Platform to deploy on (docker|kubernetes) [default: docker]"
    echo "  -a, --action        Action to perform (deploy|destroy|status|logs) [default: deploy]"
    echo "  -h, --help          Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 -e dev -p docker                    # Deploy dev environment with Docker"
    echo "  $0 -e staging -p kubernetes           # Deploy staging environment with Kubernetes"
    echo "  $0 -e production -p kubernetes        # Deploy production environment with Kubernetes"
    echo "  $0 -a destroy -e dev                  # Destroy dev environment"
    echo "  $0 -a status -e staging               # Check staging environment status"
    echo ""
}

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -p|--platform)
            PLATFORM="$2"
            shift 2
            ;;
        -a|--action)
            ACTION="$2"
            shift 2
            ;;
        -h|--help)
            print_usage
            exit 0
            ;;
        *)
            error "Unknown option: $1. Use -h for help."
            ;;
    esac
done

# Validate inputs
if [[ ! "$ENVIRONMENT" =~ ^(dev|staging|production)$ ]]; then
    error "Invalid environment: $ENVIRONMENT. Must be dev, staging, or production."
fi

if [[ ! "$PLATFORM" =~ ^(docker|kubernetes)$ ]]; then
    error "Invalid platform: $PLATFORM. Must be docker or kubernetes."
fi

if [[ ! "$ACTION" =~ ^(deploy|destroy|status|logs)$ ]]; then
    error "Invalid action: $ACTION. Must be deploy, destroy, status, or logs."
fi

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites for $PLATFORM deployment..."
    
    if [[ "$PLATFORM" == "docker" ]]; then
        if ! command -v docker &> /dev/null; then
            error "Docker is not installed or not in PATH"
        fi
        
        if ! command -v docker-compose &> /dev/null; then
            error "Docker Compose is not installed or not in PATH"
        fi
        
        if ! docker info &> /dev/null; then
            error "Docker daemon is not running"
        fi
        
    elif [[ "$PLATFORM" == "kubernetes" ]]; then
        if ! command -v kubectl &> /dev/null; then
            error "kubectl is not installed or not in PATH"
        fi
        
        if ! kubectl cluster-info &> /dev/null; then
            error "Cannot connect to Kubernetes cluster"
        fi
        
        # Check if Kind is being used
        if kubectl config current-context | grep -q "kind"; then
            if ! command -v kind &> /dev/null; then
                error "Kind is not installed or not in PATH"
            fi
        fi
    fi
    
    log "Prerequisites check passed ✓"
}

# Docker deployment functions
deploy_docker() {
    local env=$1
    
    log "Deploying $env environment using Docker Compose..."
    
    case $env in
        "dev")
            docker-compose -f docker-compose.multi-env.yml --profile dev up -d
            ;;
        "staging")
            docker-compose -f docker-compose.multi-env.yml --profile staging up -d
            ;;
        "production")
            error "Production deployment should use Kubernetes for better reliability and scaling"
            ;;
    esac
    
    log "Waiting for services to be ready..."
    sleep 10
    
    # Check service health
    check_docker_health $env
}

destroy_docker() {
    local env=$1
    
    log "Destroying $env environment..."
    
    case $env in
        "dev")
            docker-compose -f docker-compose.multi-env.yml --profile dev down -v
            ;;
        "staging")
            docker-compose -f docker-compose.multi-env.yml --profile staging down -v
            ;;
    esac
    
    log "Environment destroyed successfully"
}

check_docker_health() {
    local env=$1
    
    info "Checking service health for $env environment..."
    
    # Define service URLs based on environment
    case $env in
        "dev")
            URLS=(
                "http://localhost:5050"     # MLflow
                "http://localhost:8080"     # Healthcare AI
                "http://localhost:8090"     # A/B Testing
                "http://localhost:9090"     # Prometheus
                "http://localhost:3001"     # Grafana
            )
            ;;
        "staging")
            URLS=(
                "http://localhost:6050"     # MLflow
                "http://localhost:9080"     # Healthcare AI
                "http://localhost:9090"     # A/B Testing
                "http://localhost:10090"    # Prometheus
                "http://localhost:4001"     # Grafana
            )
            ;;
    esac
    
    for url in "${URLS[@]}"; do
        if curl -f -s "$url/health" > /dev/null || curl -f -s "$url" > /dev/null; then
            log "✓ Service at $url is healthy"
        else
            warn "✗ Service at $url is not responding"
        fi
    done
}

# Kubernetes deployment functions
deploy_kubernetes() {
    local env=$1
    
    log "Deploying $env environment on Kubernetes..."
    
    # Apply manifests in order
    kubectl apply -f "k8s/environments/$env/namespace.yaml"
    
    # Wait for namespace to be ready
    kubectl wait --for=condition=Ready namespace/healthcare-ai-$env --timeout=60s
    
    # Apply all other manifests
    for manifest in "k8s/environments/$env"/*.yaml; do
        if [[ "$(basename "$manifest")" != "namespace.yaml" ]]; then
            log "Applying $(basename "$manifest")..."
            kubectl apply -f "$manifest"
        fi
    done
    
    # Wait for deployments to be ready
    log "Waiting for deployments to be ready..."
    kubectl wait --for=condition=available --timeout=600s deployment --all -n healthcare-ai-$env
    
    log "Kubernetes deployment completed successfully"
    
    # Show access information
    show_kubernetes_access $env
}

destroy_kubernetes() {
    local env=$1
    
    log "Destroying $env environment from Kubernetes..."
    
    kubectl delete namespace healthcare-ai-$env --timeout=300s
    
    log "Kubernetes environment destroyed successfully"
}

show_kubernetes_access() {
    local env=$1
    
    info "Access URLs for $env environment:"
    
    # Get NodePort services
    kubectl get services -n healthcare-ai-$env -o wide | grep NodePort | while read line; do
        service_name=$(echo $line | awk '{print $1}')
        node_port=$(echo $line | awk '{print $5}' | cut -d: -f2 | cut -d/ -f1)
        
        case $service_name in
            "healthcare-ai-external")
                echo "  Healthcare AI: http://localhost:$node_port"
                ;;
            "mlflow-external")
                echo "  MLflow: http://localhost:$node_port"
                ;;
            "prometheus-external")
                echo "  Prometheus: http://localhost:$node_port"
                ;;
            "grafana-external")
                echo "  Grafana: http://localhost:$node_port (admin/admin123)"
                ;;
            "ab-testing-external")
                echo "  A/B Testing: http://localhost:$node_port"
                ;;
        esac
    done
}

check_kubernetes_status() {
    local env=$1
    
    info "Checking status of $env environment on Kubernetes..."
    
    # Check namespace
    if kubectl get namespace healthcare-ai-$env &> /dev/null; then
        log "✓ Namespace healthcare-ai-$env exists"
    else
        warn "✗ Namespace healthcare-ai-$env does not exist"
        return
    fi
    
    # Check pods
    echo ""
    info "Pod Status:"
    kubectl get pods -n healthcare-ai-$env
    
    # Check services
    echo ""
    info "Service Status:"
    kubectl get services -n healthcare-ai-$env
    
    # Check deployments
    echo ""
    info "Deployment Status:"
    kubectl get deployments -n healthcare-ai-$env
}

show_logs() {
    local env=$1
    
    if [[ "$PLATFORM" == "docker" ]]; then
        log "Showing logs for $env environment (Docker)..."
        
        case $env in
            "dev")
                docker-compose -f docker-compose.multi-env.yml --profile dev logs -f --tail=50
                ;;
            "staging")
                docker-compose -f docker-compose.multi-env.yml --profile staging logs -f --tail=50
                ;;
        esac
    else
        log "Showing logs for $env environment (Kubernetes)..."
        
        # Show logs for all pods
        kubectl logs -n healthcare-ai-$env --all-containers=true --tail=50 -l environment=$env
    fi
}

# Build Docker images if needed
build_images() {
    if [[ "$PLATFORM" == "docker" ]] || [[ "$PLATFORM" == "kubernetes" && "$(kubectl config current-context)" =~ kind ]]; then
        log "Building Docker images..."
        
        # Build MLflow image
        docker build -t mlflow-server:latest services/mlflow/
        
        # Build Healthcare AI image
        docker build -t healthcare-ai:latest models/healthcare-ai/
        
        # Build A/B Testing image
        docker build -t ab-testing:latest services/ab-testing/
        
        # For Kind, load images into cluster
        if [[ "$PLATFORM" == "kubernetes" && "$(kubectl config current-context)" =~ kind ]]; then
            log "Loading images into Kind cluster..."
            kind load docker-image mlflow-server:latest
            kind load docker-image healthcare-ai:latest
            kind load docker-image ab-testing:latest
        fi
        
        log "Docker images built successfully"
    fi
}

# Main execution
main() {
    log "Starting $ACTION for $ENVIRONMENT environment on $PLATFORM..."
    
    check_prerequisites
    
    case $ACTION in
        "deploy")
            build_images
            
            if [[ "$PLATFORM" == "docker" ]]; then
                deploy_docker $ENVIRONMENT
            else
                deploy_kubernetes $ENVIRONMENT
            fi
            ;;
        "destroy")
            if [[ "$PLATFORM" == "docker" ]]; then
                destroy_docker $ENVIRONMENT
            else
                destroy_kubernetes $ENVIRONMENT
            fi
            ;;
        "status")
            if [[ "$PLATFORM" == "docker" ]]; then
                check_docker_health $ENVIRONMENT
            else
                check_kubernetes_status $ENVIRONMENT
            fi
            ;;
        "logs")
            show_logs $ENVIRONMENT
            ;;
    esac
    
    log "$ACTION completed successfully!"
}

# Trap to handle interruption
trap 'error "Script interrupted"' INT TERM

# Run main function
main