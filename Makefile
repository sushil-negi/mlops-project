# Cirruslabs MLOps Platform Makefile

.PHONY: help build test deploy clean

# Default target
help: ## Show this help message
	@echo "Cirruslabs MLOps Platform"
	@echo "Available targets:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Variables
DOCKER_REGISTRY ?= localhost:5000
VERSION ?= $(shell git rev-parse --short HEAD)
NAMESPACE ?= mlops-platform
SERVICES = model-registry pipeline-orchestrator monitoring-engine security-compliance data-pipeline model-serving

# Development targets
dev-setup: ## Set up development environment
	@echo "Setting up development environment..."
	./scripts/setup-dev.sh
	kubectl create namespace $(NAMESPACE) --dry-run=client -o yaml | kubectl apply -f -

dev-deploy: build deploy-infrastructure deploy-services ## Deploy to development environment
	@echo "Development deployment complete"

# Build targets
build: $(addprefix build-,$(SERVICES)) ## Build all services

build-%: ## Build specific service
	@echo "Building service: $*"
	cd services/$* && docker build -t $(DOCKER_REGISTRY)/mlops-$*:$(VERSION) .
	docker push $(DOCKER_REGISTRY)/mlops-$*:$(VERSION)

# Test targets
test: test-unit test-integration ## Run all tests

test-unit: ## Run unit tests
	@echo "Running unit tests..."
	cd tests/unit && python -m pytest -v

test-integration: ## Run integration tests
	@echo "Running integration tests..."
	cd tests/integration && python -m pytest -v

test-e2e: ## Run end-to-end tests
	@echo "Running E2E tests..."
	cd tests/e2e && python -m pytest -v

# Deployment targets
deploy-infrastructure: ## Deploy infrastructure components
	@echo "Deploying infrastructure..."
	kubectl apply -f infrastructure/kubernetes/namespace.yaml
	kubectl apply -f infrastructure/kubernetes/storage/
	kubectl apply -f infrastructure/kubernetes/databases/
	kubectl apply -f infrastructure/kubernetes/monitoring/

deploy-services: $(addprefix deploy-,$(SERVICES)) ## Deploy all services

deploy-%: ## Deploy specific service
	@echo "Deploying service: $*"
	envsubst < infrastructure/kubernetes/services/$*/deployment.yaml | kubectl apply -f -
	kubectl apply -f infrastructure/kubernetes/services/$*/service.yaml

# Environment-specific deployments
staging-deploy: ## Deploy to staging environment
	@$(MAKE) NAMESPACE=mlops-staging DOCKER_REGISTRY=staging-registry deploy-infrastructure deploy-services

prod-deploy: ## Deploy to production environment
	@$(MAKE) NAMESPACE=mlops-production DOCKER_REGISTRY=prod-registry deploy-infrastructure deploy-services

# Utility targets
clean: ## Clean up resources
	@echo "Cleaning up..."
	kubectl delete namespace $(NAMESPACE) --ignore-not-found
	docker system prune -f

logs: ## Show logs for all services
	kubectl logs -l app.kubernetes.io/part-of=mlops-platform -n $(NAMESPACE) --tail=100

status: ## Show status of all services
	kubectl get pods,services,ingress -n $(NAMESPACE)

# Database operations
db-migrate: ## Run database migrations
	kubectl exec -it deployment/model-registry -n $(NAMESPACE) -- python manage.py migrate

db-seed: ## Seed database with sample data
	kubectl exec -it deployment/model-registry -n $(NAMESPACE) -- python manage.py seed

# Monitoring
monitoring-setup: ## Set up monitoring stack
	helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
	helm install prometheus prometheus-community/kube-prometheus-stack -n $(NAMESPACE)

# Security
security-scan: ## Run security scans
	@echo "Running security scans..."
	./scripts/security-scan.sh

# Documentation
docs: ## Generate documentation
	@echo "Generating documentation..."
	cd docs && mkdocs build

docs-serve: ## Serve documentation locally
	cd docs && mkdocs serve

# Development utilities
port-forward: ## Set up port forwarding for local development
	kubectl port-forward svc/api-gateway 8080:80 -n $(NAMESPACE) &
	kubectl port-forward svc/model-registry 8081:8000 -n $(NAMESPACE) &
	kubectl port-forward svc/monitoring-dashboard 3000:3000 -n $(NAMESPACE) &

install-tools: ## Install required development tools
	./scripts/install-tools.sh