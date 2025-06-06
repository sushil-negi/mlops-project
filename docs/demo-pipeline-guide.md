# Demo LLM Pipeline Guide

This guide walks you through using the complete MLOps pipeline to train, deploy, and monitor the demo LLM model.

## Prerequisites

Before starting, ensure you have:
- Kubernetes cluster running
- MLOps platform deployed
- Argo Workflows installed
- kubectl configured

## Step 1: Environment Setup

### 1.1 Deploy MLOps Platform

```bash
# Navigate to project directory
cd mlops-project

# Deploy infrastructure
make deploy-infrastructure

# Deploy services
make deploy-services

# Verify deployment
kubectl get pods -n mlops-platform
```

### 1.2 Install Argo Workflows

```bash
# Install Argo Workflows
kubectl create namespace argo
kubectl apply -n argo -f https://github.com/argoproj/argo-workflows/releases/download/v3.4.4/install.yaml

# Install Argo CLI
curl -sLO https://github.com/argoproj/argo-workflows/releases/download/v3.4.4/argo-linux-amd64.gz
gunzip argo-linux-amd64.gz
chmod +x argo-linux-amd64
sudo mv argo-linux-amd64 /usr/local/bin/argo

# Verify installation
argo version
```

### 1.3 Build Demo LLM Image

```bash
# Build Docker image
cd models/demo-llm
docker build -t demo-llm:latest .

# Tag for registry (adjust registry URL as needed)
docker tag demo-llm:latest localhost:5000/demo-llm:latest

# Push to registry
docker push localhost:5000/demo-llm:latest
```

## Step 2: Training Pipeline Execution

### 2.1 Submit Training Pipeline

```bash
# Submit the training pipeline
argo submit models/demo-llm/pipelines/training_pipeline.yaml \
    --parameter model-name=demo-llm \
    --parameter model-version=1.0.0 \
    --parameter experiment-name=demo-llm-experiment-1 \
    --parameter max-epochs=3 \
    --parameter batch-size=4 \
    --parameter learning-rate=5e-5

# Check pipeline status
argo list

# Watch pipeline execution
argo watch <workflow-name>

# Get detailed logs
argo logs <workflow-name>
```

### 2.2 Monitor Training Progress

```bash
# View pipeline in Argo UI (if available)
kubectl port-forward -n argo svc/argo-server 2746:2746
# Open browser to http://localhost:2746

# Check MLflow for experiment tracking
kubectl port-forward -n mlops-platform svc/mlflow 5000:5000
# Open browser to http://localhost:5000
```

### 2.3 Pipeline Steps Explained

The pipeline executes these steps automatically:

1. **Data Preparation**: Creates demo training data
2. **Data Validation**: Validates data format and quality
3. **Model Training**: Trains the LLM with specified parameters
4. **Model Evaluation**: Evaluates model performance
5. **Quality Gates**: Validates model meets criteria
6. **Model Registration**: Registers model in registry
7. **Staging Deployment**: Deploys to staging environment

## Step 3: Manual Training (Alternative)

If you prefer manual training outside the pipeline:

### 3.1 Local Training

```bash
# Create output directory
mkdir -p models/trained/demo-llm-v1.0.0

# Run training
cd models/demo-llm
python scripts/train.py \
    --config config/training_config.yaml \
    --output-dir ../../trained/demo-llm-v1.0.0 \
    --data-config config/data_config.yaml
```

### 3.2 Containerized Training

```bash
# Run training in container
docker run -v $(pwd)/models/trained:/workspace/models \
    -v $(pwd)/models/demo-llm:/app \
    -w /app \
    demo-llm:latest \
    python scripts/train.py \
    --config config/training_config.yaml \
    --output-dir /workspace/models/demo-llm-v1.0.0
```

## Step 4: Model Registration

### 4.1 Register Trained Model

```bash
# Get model registry URL
kubectl get svc -n mlops-platform model-registry

# Register model
cd models/demo-llm
python scripts/register_model.py \
    --model-dir ../../trained/demo-llm-v1.0.0/best_model \
    --registry-url http://<model-registry-ip>:8000 \
    --model-name demo-llm \
    --version 1.0.0 \
    --stage Development \
    --output registration_result.json

# View registration result
cat registration_result.json
```

### 4.2 Verify Registration

```bash
# Check model in registry
curl -X GET "http://<model-registry-ip>:8000/api/v1/models" | jq

# Get specific model info
curl -X GET "http://<model-registry-ip>:8000/api/v1/models/<model-id>" | jq
```

## Step 5: Model Deployment

### 5.1 Deploy to Staging

Create deployment manifest:

```yaml
# models/demo-llm/k8s/staging-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: demo-llm-staging
  namespace: mlops-platform
  labels:
    app: demo-llm
    environment: staging
    version: "1.0.0"
spec:
  replicas: 2
  selector:
    matchLabels:
      app: demo-llm
      environment: staging
  template:
    metadata:
      labels:
        app: demo-llm
        environment: staging
        version: "1.0.0"
    spec:
      containers:
      - name: demo-llm
        image: demo-llm:latest
        ports:
        - containerPort: 8000
        env:
        - name: MODEL_PATH
          value: "/models/demo-llm-v1.0.0"
        - name: ENVIRONMENT
          value: "staging"
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
  name: demo-llm-staging
  namespace: mlops-platform
  labels:
    app: demo-llm
    environment: staging
spec:
  selector:
    app: demo-llm
    environment: staging
  ports:
  - port: 8000
    targetPort: 8000
    protocol: TCP
  type: ClusterIP
```

Deploy to staging:

```bash
# Apply deployment
kubectl apply -f models/demo-llm/k8s/staging-deployment.yaml

# Check deployment status
kubectl get pods -n mlops-platform -l app=demo-llm,environment=staging

# Check service
kubectl get svc -n mlops-platform demo-llm-staging
```

### 5.2 Test Staging Deployment

```bash
# Port forward to test
kubectl port-forward -n mlops-platform svc/demo-llm-staging 8000:8000

# Test health endpoint
curl http://localhost:8000/health

# Test model inference
curl -X POST "http://localhost:8000/generate" \
     -H "Content-Type: application/json" \
     -d '{
       "text": "The future of machine learning is",
       "max_length": 100,
       "temperature": 0.7
     }' | jq
```

### 5.3 Deploy to Production

Once staging tests pass, promote to production:

```bash
# Update model stage in registry
curl -X PUT "http://<model-registry-ip>:8000/api/v1/models/<model-id>/stage" \
     -H "Content-Type: application/json" \
     -d '{"stage": "Production"}'

# Deploy to production (similar to staging but with production config)
sed 's/staging/production/g' models/demo-llm/k8s/staging-deployment.yaml > production-deployment.yaml
kubectl apply -f production-deployment.yaml
```

## Step 6: Monitoring and Observability

### 6.1 Set Up Monitoring

```bash
# Access Grafana dashboard
kubectl port-forward -n mlops-platform svc/grafana 3000:3000
# Login: admin/admin123
# Open browser to http://localhost:3000

# Access Prometheus
kubectl port-forward -n mlops-platform svc/prometheus 9090:9090
# Open browser to http://localhost:9090
```

### 6.2 Monitor Model Performance

```bash
# Check model metrics
curl http://localhost:8000/metrics

# View request logs
kubectl logs -n mlops-platform -l app=demo-llm --tail=100

# Monitor resource usage
kubectl top pods -n mlops-platform -l app=demo-llm
```

### 6.3 Set Up Alerts

Create alerting rules for model monitoring:

```yaml
# monitoring/model-alerts.yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: demo-llm-alerts
  namespace: mlops-platform
spec:
  groups:
  - name: demo-llm
    rules:
    - alert: HighErrorRate
      expr: rate(demo_llm_errors_total[5m]) > 0.1
      for: 2m
      labels:
        severity: warning
      annotations:
        summary: "High error rate detected in demo LLM"
        description: "Error rate is {{ $value }} errors per second"
    
    - alert: HighLatency
      expr: histogram_quantile(0.95, rate(demo_llm_duration_seconds_bucket[5m])) > 2
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: "High latency detected in demo LLM"
        description: "95th percentile latency is {{ $value }} seconds"
    
    - alert: ModelDown
      expr: up{job="demo-llm"} == 0
      for: 1m
      labels:
        severity: critical
      annotations:
        summary: "Demo LLM model is down"
        description: "Demo LLM service is not responding"
```

Apply monitoring rules:

```bash
kubectl apply -f monitoring/model-alerts.yaml
```

## Step 7: Continuous Integration

### 7.1 Set Up Automated Pipeline

Create a trigger for automatic retraining:

```bash
# Create a CronWorkflow for periodic retraining
argo cron create - <<EOF
apiVersion: argoproj.io/v1alpha1
kind: CronWorkflow
metadata:
  name: demo-llm-retrain
  namespace: mlops-platform
spec:
  schedule: "0 2 * * 0"  # Weekly on Sunday at 2 AM
  workflowSpec:
    entrypoint: training-pipeline
    templates:
    - name: training-pipeline
      dag:
        tasks:
        - name: retrain
          templateRef:
            name: demo-llm-training-pipeline
            template: training-pipeline
          arguments:
            parameters:
            - name: model-version
              value: "{{workflow.creationTimestamp}}"
EOF
```

### 7.2 Model Validation Pipeline

```bash
# Submit validation pipeline after deployment
argo submit - <<EOF
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  generateName: demo-llm-validation-
  namespace: mlops-platform
spec:
  entrypoint: validate-deployment
  templates:
  - name: validate-deployment
    script:
      image: curlimages/curl
      command: [sh]
      source: |
        # Test health endpoint
        curl -f http://demo-llm-staging:8000/health
        
        # Test inference endpoint
        curl -f -X POST "http://demo-llm-staging:8000/generate" \
             -H "Content-Type: application/json" \
             -d '{"text": "Test input", "max_length": 50}'
        
        echo "Validation completed successfully"
EOF
```

## Step 8: Troubleshooting

### 8.1 Common Issues

**Pipeline Fails at Training Step:**
```bash
# Check logs
argo logs <workflow-name> -c train-model

# Check resource usage
kubectl describe pod <training-pod> -n mlops-platform
```

**Model Registration Fails:**
```bash
# Check model registry service
kubectl get pods -n mlops-platform -l app=model-registry
kubectl logs -n mlops-platform -l app=model-registry

# Test registry connectivity
kubectl exec -it <any-pod> -n mlops-platform -- curl http://model-registry:8000/health
```

**Deployment Issues:**
```bash
# Check deployment status
kubectl describe deployment demo-llm-staging -n mlops-platform

# Check pod logs
kubectl logs -n mlops-platform -l app=demo-llm,environment=staging
```

### 8.2 Performance Optimization

**Increase Training Speed:**
```yaml
# In training_config.yaml
batch_size: 8  # Increase if you have more memory
max_epochs: 2  # Reduce for faster demo
learning_rate: 1e-4  # Slightly higher for faster convergence
```

**Scale Inference Service:**
```bash
# Scale up replicas
kubectl scale deployment demo-llm-staging --replicas=5 -n mlops-platform

# Set up horizontal pod autoscaler
kubectl autoscale deployment demo-llm-staging \
    --cpu-percent=70 \
    --min=2 \
    --max=10 \
    -n mlops-platform
```

## Complete Workflow Summary

1. **Setup**: Deploy MLOps platform and build model image
2. **Train**: Submit training pipeline or run manual training
3. **Register**: Register trained model in model registry
4. **Deploy**: Deploy to staging, test, then promote to production
5. **Monitor**: Set up monitoring, alerts, and observability
6. **Iterate**: Set up automated retraining and validation

This complete workflow demonstrates the full MLOps lifecycle using the demo LLM model through the Cirruslabs MLOps platform.