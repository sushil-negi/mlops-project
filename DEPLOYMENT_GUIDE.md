# Healthcare AI MLOps Platform - Deployment Guide

Complete deployment guide for Healthcare AI MLOps platform supporting dev, staging, and production environments on both Docker and Kubernetes.

## 🚀 Quick Start

```bash
# Deploy development environment with Docker
./deploy.sh -e dev -p docker

# Deploy staging environment with Kubernetes
./deploy.sh -e staging -p kubernetes

# Deploy production environment with Kubernetes  
./deploy.sh -e production -p kubernetes
```

## 📋 Prerequisites

### For Docker Deployments
- Docker Engine 20.10+
- Docker Compose 2.0+
- At least 8GB RAM available
- 20GB disk space

### For Kubernetes Deployments
- kubectl configured and connected to cluster
- Kubernetes 1.21+
- For local development: Kind or minikube
- At least 16GB RAM for staging/production
- 50GB+ disk space for production

## 🏗️ Architecture Overview

### Environments

| Environment | Purpose | Resources | High Availability |
|-------------|---------|-----------|------------------|
| **Development** | Local development and testing | Minimal | Single replicas |
| **Staging** | Pre-production testing | Medium | 2-3 replicas |
| **Production** | Live system | High | 3-5 replicas |

### Port Allocation

| Service | Dev | Staging | Production | Kubernetes |
|---------|-----|---------|------------|------------|
| Healthcare AI | 8080 | 9080 | - | 31000 |
| MLflow | 5050 | 6050 | - | 30700 |
| A/B Testing | 8090 | 9090 | - | 31008 |
| Prometheus | 9090 | 10090 | - | 31109 |
| Grafana | 3001 | 4001 | - | 30500 |
| MinIO API | 9000 | 10000 | - | 31100 |
| MinIO Console | 9001 | 10001 | - | 31101 |

## 🐳 Docker Deployment

### Development Environment

```bash
# Start development environment
./deploy.sh -e dev -p docker

# Check service health
./deploy.sh -a status -e dev -p docker

# View logs
./deploy.sh -a logs -e dev -p docker

# Stop environment
./deploy.sh -a destroy -e dev -p docker
```

**Access URLs (Development):**
- Healthcare AI: http://localhost:8080
- MLflow: http://localhost:5050
- A/B Testing: http://localhost:8090
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3001 (admin/admin123)
- MinIO Console: http://localhost:9001 (minioadmin/minioadmin123)

### Staging Environment

```bash
# Start staging environment
./deploy.sh -e staging -p docker

# Both environments can run simultaneously
./deploy.sh -e dev -p docker
./deploy.sh -e staging -p docker
```

**Access URLs (Staging):**
- Healthcare AI: http://localhost:9080
- MLflow: http://localhost:6050
- A/B Testing: http://localhost:9090
- Prometheus: http://localhost:10090
- Grafana: http://localhost:4001 (admin/admin123)
- MinIO Console: http://localhost:10001 (minioadmin/minioadmin123)

## ☸️ Kubernetes Deployment

### Local Development (Kind)

```bash
# Create Kind cluster
kind create cluster --config infrastructure/kubernetes/kind-cluster-config.yaml

# Deploy development environment
./deploy.sh -e dev -p kubernetes

# Check status
./deploy.sh -a status -e dev -p kubernetes

# Access services (NodePort)
kubectl get services -n healthcare-ai-dev
```

### Staging Environment

```bash
# Deploy staging environment
./deploy.sh -e staging -p kubernetes

# Check all environments
kubectl get namespaces | grep healthcare-ai
```

### Production Environment

```bash
# ⚠️ IMPORTANT: Update production secrets first!
# Edit k8s/environments/production/namespace.yaml
# Replace placeholder passwords with secure values

# Deploy production environment
./deploy.sh -e production -p kubernetes

# Verify high availability setup
kubectl get pods -n healthcare-ai-production -o wide
```

## 🔧 Configuration

### Environment Variables

| Variable | Development | Staging | Production |
|----------|------------|---------|------------|
| `LOG_LEVEL` | DEBUG | INFO | WARNING |
| `ENVIRONMENT` | development | staging | production |
| `MODEL_VERSION` | latest | release-candidate | stable |
| `REPLICAS` | 1-2 | 2-3 | 3-5 |

### Resource Allocation

#### Development
- **CPU**: 250m-500m per service
- **Memory**: 256Mi-1Gi per service
- **Storage**: 5-20Gi per service

#### Staging
- **CPU**: 500m-1000m per service
- **Memory**: 512Mi-2Gi per service
- **Storage**: 10-50Gi per service

#### Production
- **CPU**: 1-4 cores per service
- **Memory**: 2-8Gi per service
- **Storage**: 50-500Gi per service

## 🔒 Security

### Development
- Default passwords (insecure)
- No network policies
- Basic security contexts

### Staging
- Strong passwords required
- Network isolation
- Security contexts enabled

### Production
- **CRITICAL**: Update all secrets before deployment
- Pod security standards enforced
- Network policies active
- Anti-affinity rules for HA
- Node affinity for dedicated nodes

### Security Checklist for Production

- [ ] Update all passwords in `k8s/environments/production/namespace.yaml`
- [ ] Configure TLS certificates
- [ ] Set up RBAC policies
- [ ] Enable Pod Security Policies
- [ ] Configure network policies
- [ ] Set up monitoring alerts
- [ ] Enable audit logging

## 📊 Monitoring & Observability

### Metrics Collection
- **Prometheus**: Time-series metrics collection
- **Grafana**: Visualization and dashboards
- **Custom Metrics**: Healthcare-specific metrics

### A/B Testing Safety
- **Real-time monitoring**: Automatic safety threshold checks
- **Emergency stops**: Automatic experiment termination
- **Statistical analysis**: Confidence intervals and p-values
- **Safety thresholds**:
  - Crisis detection rate: ≥99%
  - Empathy score: ≥65%
  - Accuracy: ≥90%

### Logging
- **Structured logging**: JSON format with structured data
- **Log levels**: DEBUG (dev), INFO (staging), WARNING (prod)
- **Centralized**: All logs collected in monitoring stack

## 🧪 Testing Deployments

### Health Checks

```bash
# Test all services are responding
curl -f http://localhost:8080/health  # Healthcare AI
curl -f http://localhost:5050/        # MLflow  
curl -f http://localhost:8090/health  # A/B Testing
curl -f http://localhost:9090/-/healthy # Prometheus

# Test model prediction
curl -X POST http://localhost:8080/predict \
  -H "Content-Type: application/json" \
  -d '{"text": "I am feeling anxious about my health"}'

# Test A/B routing
curl http://localhost:8090/route/user123
```

### Load Testing

```bash
# Install hey for load testing
go install github.com/rakyll/hey@latest

# Test Healthcare AI service
hey -n 1000 -c 10 http://localhost:8080/health

# Test A/B routing
hey -n 1000 -c 10 http://localhost:8090/route/user123
```

## 🔄 Updating Deployments

### Rolling Updates (Kubernetes)

```bash
# Update Healthcare AI model
kubectl set image deployment/healthcare-ai \
  healthcare-ai=healthcare-ai:v2.0.0 \
  -n healthcare-ai-staging

# Check rollout status
kubectl rollout status deployment/healthcare-ai -n healthcare-ai-staging

# Rollback if needed
kubectl rollout undo deployment/healthcare-ai -n healthcare-ai-staging
```

### Blue-Green Deployment

```bash
# Deploy new version alongside current
kubectl apply -f deployment/blue_green_deployment.yaml

# Switch traffic after validation
kubectl patch service healthcare-ai -p '{"spec":{"selector":{"version":"green"}}}'
```

## 🚨 Troubleshooting

### Common Issues

#### Docker: Port Already in Use
```bash
# Check what's using the port
lsof -i :8080

# Kill process if needed
kill -9 $(lsof -t -i:8080)
```

#### Kubernetes: Pods Not Starting
```bash
# Check pod status
kubectl describe pod <pod-name> -n healthcare-ai-dev

# Check logs
kubectl logs <pod-name> -n healthcare-ai-dev -c <container-name>

# Check events
kubectl get events -n healthcare-ai-dev --sort-by='.lastTimestamp'
```

#### Database Connection Issues
```bash
# Test PostgreSQL connectivity
kubectl exec -it postgres-xxx -n healthcare-ai-dev -- psql -U mlflow -d mlflow_dev

# Check Redis connectivity  
kubectl exec -it redis-xxx -n healthcare-ai-dev -- redis-cli ping
```

### Service Dependencies

```
Healthcare AI ← MLflow ← PostgreSQL
Healthcare AI ← Redis
A/B Testing ← Redis  
A/B Testing ← Prometheus
Prometheus ← All Services
Grafana ← Prometheus
```

## 📈 Scaling

### Horizontal Scaling

```bash
# Scale Healthcare AI service
kubectl scale deployment healthcare-ai --replicas=10 -n healthcare-ai-production

# Auto-scaling (HPA)
kubectl autoscale deployment healthcare-ai \
  --cpu-percent=70 \
  --min=3 \
  --max=20 \
  -n healthcare-ai-production
```

### Vertical Scaling

```bash
# Update resource limits
kubectl patch deployment healthcare-ai -p '
{
  "spec": {
    "template": {
      "spec": {
        "containers": [{
          "name": "healthcare-ai",
          "resources": {
            "limits": {"memory": "8Gi", "cpu": "4000m"},
            "requests": {"memory": "4Gi", "cpu": "2000m"}
          }
        }]
      }
    }
  }
}' -n healthcare-ai-production
```

## 🏃‍♂️ Quick Commands Reference

```bash
# Deployment
./deploy.sh -e dev -p docker        # Deploy dev with Docker
./deploy.sh -e staging -p kubernetes # Deploy staging with K8s
./deploy.sh -e production -p kubernetes # Deploy production with K8s

# Management
./deploy.sh -a status -e dev        # Check status
./deploy.sh -a logs -e staging      # View logs
./deploy.sh -a destroy -e dev       # Destroy environment

# Kubernetes specific
kubectl get all -n healthcare-ai-dev          # Check all resources
kubectl logs -f deployment/healthcare-ai -n healthcare-ai-dev # Follow logs
kubectl port-forward svc/grafana 3000:3000 -n healthcare-ai-dev # Port forward

# Health checks
curl -f http://localhost:8080/health           # Healthcare AI
curl -f http://localhost:5050/                # MLflow
curl -f http://localhost:8090/health          # A/B Testing
```

## 📚 Additional Resources

- [Healthcare AI Model Documentation](models/healthcare-ai/README.md)
- [A/B Testing Service Documentation](services/ab-testing/README.md)
- [Monitoring Setup Guide](docs/monitoring-setup.md)
- [Production Security Checklist](docs/production-security.md)
- [Troubleshooting Guide](docs/troubleshooting.md)