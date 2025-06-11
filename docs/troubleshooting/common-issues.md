# Troubleshooting Guide

This guide helps resolve common issues with the Healthcare AI MLOps Platform across development, deployment, and production environments.

## Table of Contents

1. [Quick Diagnostics](#quick-diagnostics)
2. [Service Issues](#service-issues)
3. [MLOps Pipeline Issues](#mlops-pipeline-issues)
4. [Performance Issues](#performance-issues)
5. [Data and Model Issues](#data-and-model-issues)
6. [Infrastructure Issues](#infrastructure-issues)
7. [Security and Compliance Issues](#security-and-compliance-issues)

## Quick Diagnostics

### Health Check Commands

```bash
# Check all services
docker compose ps

# Check service health endpoints
curl http://localhost:8080/health    # Healthcare AI
curl http://localhost:5001/health    # MLflow
curl http://localhost:9000/minio/health/live    # MinIO

# Check service logs
docker logs healthcare-ai
docker logs mlflow
docker logs postgres
```

### System Status Dashboard

```bash
# Check resource usage
docker stats

# Check disk space
df -h

# Check memory usage
free -h

# Check network connectivity
netstat -tulpn | grep -E "(8080|5001|9000)"
```

## Service Issues

### Healthcare AI Service Won't Start

#### Symptoms
- Service fails to start
- Health check returns 500 error
- Container exits immediately

#### Common Causes and Solutions

**1. Model File Missing**
```bash
# Check if model file exists
ls -la models/healthcare-ai/models/

# Rebuild model if missing
python scripts/train_healthcare_model.py

# Copy model to container
docker cp models/healthcare_model.joblib healthcare-ai:/app/models/
```

**2. Port Conflicts**
```bash
# Check what's using port 8080
sudo lsof -i :8080

# Kill conflicting process
sudo kill -9 <PID>

# Or use alternative port
export HEALTHCARE_SERVICE_PORT=8888
docker compose up -d healthcare-ai
```

**3. Memory Issues**
```bash
# Check container memory limits
docker inspect healthcare-ai | grep -i memory

# Increase memory limits in docker-compose.yml
services:
  healthcare-ai:
    deploy:
      resources:
        limits:
          memory: 4G
```

### MLflow Service Issues

#### MLflow Won't Connect to Database

**Symptoms**
- MLflow UI shows database connection errors
- Model registration fails
- Artifact uploads fail

**Solutions**
```bash
# Check PostgreSQL is running
docker logs postgres

# Verify database configuration
docker exec postgres psql -U mlflow -d mlflow -c "\dt"

# Reset MLflow database
docker compose down
docker volume rm mlops_postgres_data
docker compose up -d
```

#### MLflow Artifact Upload Failures

**Symptoms**
- "Access Denied" errors when logging artifacts
- S3 connection timeouts
- Bucket not found errors

**Solutions**
```bash
# Run MinIO permissions fix
./scripts/fix-minio-permissions.sh

# Manual bucket creation
docker exec minio mc mb minio-local/mlflow-artifacts
docker exec minio mc anonymous set download minio-local/mlflow-artifacts

# Check S3 configuration
python scripts/debug-s3-config.py
```

### Database Connection Issues

#### PostgreSQL Connection Failures

**Symptoms**
- Connection refused errors
- Authentication failures
- Database not found errors

**Solutions**
```bash
# Check PostgreSQL status
docker exec postgres pg_isready

# Reset PostgreSQL
docker compose stop postgres
docker volume rm mlops_postgres_data
docker compose up -d postgres

# Check connection from another container
docker exec healthcare-ai pg_isready -h postgres -U mlflow
```

## MLOps Pipeline Issues

### CI Pipeline Failures

#### Data Quality Validation Fails

**Symptoms**
- CI pipeline fails with data quality errors
- Duplicate detection issues
- Format validation failures

**Solutions**
```bash
# Run data quality checks locally
python scripts/data_quality_checks.py

# Fix duplicate data
python scripts/remove_duplicates.py data/training_data.json

# Validate data format
python -c "import json; json.load(open('data/training_data.json'))"
```

#### Code Formatting Issues

**Symptoms**
- CI fails with import sorting errors
- Black formatting failures
- Linting errors

**Solutions**
```bash
# Fix import sorting
python -m isort . --profile black

# Fix code formatting
python -m black .

# Run linting
python -m flake8 models/ scripts/
```

### ML Pipeline Failures

#### Model Training Failures

**Symptoms**
- Training script crashes
- Low accuracy errors
- Memory out of bounds

**Solutions**
```bash
# Check training data quality
python tests/unit/test_training_data.py

# Train with verbose logging
python scripts/train_healthcare_model.py --verbose

# Reduce dataset size for testing
python scripts/create_test_data.py --size 1000
```

#### Model Validation Failures

**Symptoms**
- Accuracy below threshold
- Crisis detection validation fails
- Category coverage incomplete

**Solutions**
```bash
# Run model validation locally
python tests/healthcare_model_validation.py

# Check crisis detection specifically
python tests/crisis_detection_validation.py

# Retrain with more data
python scripts/train_with_expanded_data.py
```

### Security Pipeline Issues

#### Dependency Vulnerability Warnings

**Symptoms**
- Security pipeline reports vulnerabilities
- Outdated package warnings
- License compliance issues

**Solutions**
```bash
# Update dependencies
pip-audit --fix

# Check for security issues
bandit -r models/ scripts/

# Update requirements
pip-review --auto
```

## Performance Issues

### Slow Response Times

#### Healthcare AI Response Delays

**Symptoms**
- Response times > 1 second
- Timeout errors
- Poor user experience

**Diagnostics**
```bash
# Measure response time
time curl -X POST http://localhost:8080/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "test query"}'

# Check resource usage
docker stats healthcare-ai

# Monitor logs for performance issues
docker logs healthcare-ai --follow
```

**Solutions**
```bash
# Enable response caching
export ENABLE_RESPONSE_CACHE=true
docker compose restart healthcare-ai

# Increase worker threads
export HEALTHCARE_WORKERS=4
docker compose restart healthcare-ai

# Optimize model loading
python scripts/optimize_model_loading.py
```

### High Memory Usage

#### Memory Leaks

**Symptoms**
- Continuously increasing memory usage
- Out of memory errors
- Container restarts

**Solutions**
```bash
# Monitor memory usage over time
while true; do docker stats --no-stream; sleep 10; done

# Restart services to clear memory
docker compose restart healthcare-ai

# Implement memory limits
# Add to docker-compose.yml:
deploy:
  resources:
    limits:
      memory: 2G
```

### Database Performance Issues

#### Slow Query Performance

**Symptoms**
- MLflow UI loads slowly
- Database connection timeouts
- Query execution delays

**Solutions**
```bash
# Check database performance
docker exec postgres psql -U mlflow -d mlflow -c "
SELECT query, calls, total_time, mean_time 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;"

# Rebuild database indexes
docker exec postgres psql -U mlflow -d mlflow -c "REINDEX DATABASE mlflow;"

# Optimize PostgreSQL configuration
# Add to docker-compose.yml postgres environment:
- POSTGRES_SHARED_BUFFERS=256MB
- POSTGRES_EFFECTIVE_CACHE_SIZE=1GB
```

## Data and Model Issues

### Model Accuracy Degradation

#### Symptoms
- Accuracy drops below threshold
- Increased misclassification
- Poor response quality

**Diagnostics**
```bash
# Check current model performance
python tests/healthcare_model_validation.py

# Compare with previous model versions
python scripts/compare_model_versions.py

# Analyze prediction patterns
python scripts/analyze_prediction_accuracy.py
```

**Solutions**
```bash
# Retrain with recent data
python scripts/retrain_with_recent_data.py

# Update training data
python scripts/expand_training_dataset.py

# Rollback to previous model version
python scripts/rollback_model.py --version previous
```

### Data Quality Issues

#### Training Data Problems

**Symptoms**
- Inconsistent response quality
- Model bias in predictions
- Category imbalance

**Solutions**
```bash
# Analyze data distribution
python scripts/analyze_data_distribution.py

# Balance category representation
python scripts/balance_training_data.py

# Validate data quality
python scripts/comprehensive_data_validation.py
```

### Model Registry Issues

#### Model Registration Failures

**Symptoms**
- Models not appearing in MLflow UI
- Registration API errors
- Metadata missing

**Solutions**
```bash
# Check MLflow connectivity
python -c "import mlflow; print(mlflow.get_tracking_uri())"

# Register model manually
python scripts/manual_model_registration.py

# Clear and rebuild registry
python scripts/rebuild_model_registry.py
```

## Infrastructure Issues

### Docker Issues

#### Container Won't Start

**Symptoms**
- Container exits immediately
- "Container name already in use" errors
- Image build failures

**Solutions**
```bash
# Clean up containers
docker compose down
docker container prune -f

# Rebuild images
docker compose build --no-cache

# Check Docker resources
docker system df
docker system prune -f
```

#### Volume Mount Issues

**Symptoms**
- File not found errors
- Permission denied errors
- Data not persisting

**Solutions**
```bash
# Check volume mounts
docker volume ls
docker volume inspect mlops_postgres_data

# Fix permissions
sudo chown -R $USER:$USER ./data
chmod -R 755 ./data

# Recreate volumes
docker compose down -v
docker compose up -d
```

### Kubernetes Issues

#### Pod Failures

**Symptoms**
- Pods in CrashLoopBackOff state
- ImagePullBackOff errors
- Resource quota exceeded

**Solutions**
```bash
# Check pod status
kubectl get pods -n mlops-production

# Check pod logs
kubectl logs -f healthcare-ai-deployment-xxx -n mlops-production

# Describe pod for events
kubectl describe pod healthcare-ai-deployment-xxx -n mlops-production

# Check resource usage
kubectl top pods -n mlops-production
```

#### Service Discovery Issues

**Symptoms**
- Services can't communicate
- DNS resolution failures
- Network timeouts

**Solutions**
```bash
# Test service connectivity
kubectl exec -it healthcare-ai-deployment-xxx -- nslookup postgres

# Check service endpoints
kubectl get endpoints -n mlops-production

# Verify network policies
kubectl get networkpolicies -n mlops-production
```

## Security and Compliance Issues

### HIPAA Compliance Issues

#### Audit Trail Problems

**Symptoms**
- Missing audit logs
- Incomplete access logging
- Compliance validation failures

**Solutions**
```bash
# Check audit logging
grep "audit" /var/log/healthcare-ai/*.log

# Validate compliance configuration
python scripts/validate_hipaa_compliance.py

# Enable comprehensive logging
export LOG_LEVEL=INFO
export AUDIT_LOGGING=true
docker compose restart
```

### Security Scanning Issues

#### Vulnerability Alerts

**Symptoms**
- Security pipeline reports critical vulnerabilities
- Outdated dependencies
- Exposed sensitive information

**Solutions**
```bash
# Run comprehensive security scan
python scripts/run_security_checks.py

# Update vulnerable dependencies
pip-audit --fix

# Scan for exposed secrets
git-secrets --scan-history

# Update base images
docker pull python:3.11-slim
docker compose build --no-cache
```

## Getting Additional Help

### Log Collection

For support requests, collect relevant logs:

```bash
# Collect all service logs
mkdir troubleshooting-logs
docker logs healthcare-ai > troubleshooting-logs/healthcare-ai.log
docker logs mlflow > troubleshooting-logs/mlflow.log
docker logs postgres > troubleshooting-logs/postgres.log

# Collect system information
docker compose ps > troubleshooting-logs/services.log
docker stats --no-stream > troubleshooting-logs/stats.log
```

### Support Channels

1. **GitHub Issues** - Create detailed issue with logs and steps to reproduce
2. **Documentation** - Check relevant documentation sections
3. **Community Forums** - Ask questions in project discussions
4. **Emergency Support** - For production issues, contact on-call team

### Emergency Procedures

For critical production issues:

```bash
# Emergency restart
docker compose restart

# Emergency rollback
git checkout HEAD~1
docker compose up -d

# Emergency scale down
kubectl scale deployment healthcare-ai --replicas=0 -n mlops-production

# Emergency maintenance mode
kubectl apply -f k8s/maintenance-mode.yaml
```

For healthcare emergencies or crisis situations, always direct users to:
- **Call 911** for medical emergencies
- **Call 988** for mental health crises
- This platform provides guidance only, not emergency services