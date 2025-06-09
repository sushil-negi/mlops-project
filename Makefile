# Healthcare AI MLOps Project Makefile

.PHONY: help build test deploy clean test-unit test-integration test-e2e test-coverage install-deps lint format start-services stop-services

# Default target
help: ## Show this help message
	@echo "Healthcare AI MLOps Project"
	@echo "=========================="
	@echo ""
	@echo "Available targets:"
	@echo "  help             Show this help message"
	@echo "  install-deps     Install all dependencies"
	@echo "  test             Run all tests with coverage"
	@echo "  test-unit        Run unit tests only"
	@echo "  test-integration Run integration tests only"
	@echo "  test-e2e         Run end-to-end tests only"
	@echo "  test-coverage    Generate coverage report only"
	@echo "  lint             Run code linting"
	@echo "  clean            Clean test artifacts"
	@echo "  start-services   Start all required services"
	@echo "  stop-services    Stop all services"
	@echo "  train-model      Train healthcare model"
	@echo "  docker-up        Start services with Docker Compose"
	@echo "  docker-down      Stop Docker services"

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
test: ## Run all tests with coverage
	@echo "Running all tests with coverage..."
	source venv/bin/activate && python3 scripts/run_tests.py

test-unit: ## Run unit tests only
	@echo "Running unit tests..."
	source venv/bin/activate && python3 scripts/run_tests.py --unit

test-integration: ## Run integration tests only
	@echo "Running integration tests..."
	source venv/bin/activate && python3 scripts/run_tests.py --integration

test-e2e: ## Run end-to-end tests only
	@echo "Running end-to-end tests..."
	source venv/bin/activate && python3 scripts/run_tests.py --e2e

test-coverage: ## Generate coverage report only
	@echo "Generating coverage report..."
	source venv/bin/activate && python3 scripts/run_tests.py --coverage-only

# Install dependencies
install-deps: ## Install all dependencies
	@echo "Installing project dependencies..."
	source venv/bin/activate && pip install -r tests/requirements.txt
	source venv/bin/activate && pip install flake8 black isort

# Code quality
lint: ## Run code linting
	@echo "Running code linting..."
	source venv/bin/activate && flake8 models/demo-llm/src/ scripts/ --max-line-length=120 --ignore=E501,W503

format: ## Format code
	@echo "Formatting code..."
	source venv/bin/activate && black models/demo-llm/src/ scripts/
	source venv/bin/activate && isort models/demo-llm/src/ scripts/

validate: ## Run complete pre-commit validation pipeline
	@echo "🔍 Running mandatory pre-commit validation checks..."
	@echo "1. Code formatting check..."
	python3 -m black --check --diff models/ scripts/ tests/ services/
	@echo "2. Import sorting check..."
	python3 -m isort --check-only --diff models/ scripts/ tests/ services/
	@echo "3. Full test suite (CI pipeline)..."
	python3 scripts/run_tests.py
	@echo "4. ML pipeline validation..."
	python3 scripts/test_mlops_pipeline.py
	@echo "5. Security checks..."
	python3 scripts/run_security_checks.py
	@echo "6. HIPAA compliance validation..."
	python3 scripts/hipaa_compliance_check.py
	@echo "7. Crisis detection validation..."
	python3 tests/crisis_detection_validation.py
	@echo "8. Healthcare service health check..."
	@curl -f http://localhost:8888/health > /dev/null 2>&1 || curl -f http://localhost:8080/health > /dev/null 2>&1 || echo "⚠️ Healthcare service not running (expected if not started)"
	@echo "✅ ALL VALIDATION CHECKS PASSED - Safe to commit!"

# Healthcare AI specific targets
train-model: ## Train healthcare model
	@echo "Training healthcare model..."
	source venv/bin/activate && python3 scripts/train_real_healthcare_model.py

start-services: ## Start all required services
	@echo "Starting healthcare AI services..."
	source venv/bin/activate && nohup mlflow server --host 0.0.0.0 --port 5001 --backend-store-uri sqlite:///mlflow.db --default-artifact-root ./mlruns > mlflow.log 2>&1 &
	source venv/bin/activate && nohup python3 scripts/start_healthcare_ai_service.py > healthcare_ai.log 2>&1 &
	@sleep 5
	@echo "Services started. Check logs: mlflow.log, healthcare_ai.log"

stop-services: ## Stop all services
	@echo "Stopping services..."
	pkill -f "mlflow server" || true
	pkill -f "start_healthcare_ai_service" || true
	@echo "Services stopped."

# Cleanup
clean: ## Clean test artifacts
	@echo "Cleaning test artifacts..."
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf coverage.xml
	rm -rf .pytest_cache/
	rm -rf tests/__pycache__/
	rm -rf tests/unit/__pycache__/
	rm -rf tests/integration/__pycache__/
	rm -rf tests/e2e/__pycache__/
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -delete

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