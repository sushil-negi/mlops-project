# Getting Started Guide

## Prerequisites

Before you begin, ensure you have the following installed:

- **Docker** (20.10+) and **Docker Compose** (2.0+)
- **Python** (3.9+) for local development
- **Git** for version control
- **curl** or **Postman** for API testing
- **Make** (optional, for convenience commands)

### System Requirements
- **RAM**: Minimum 8GB (16GB recommended)
- **Storage**: 10GB free space
- **OS**: Linux, macOS, or Windows with WSL2

## 🚀 Quick Start (5 minutes)

### 1. Clone the Repository
```bash
git clone https://github.com/sushil-negi/mlops-project.git
cd mlops-project
```

### 2. Start All Services
```bash
# Start the entire platform
docker compose up -d

# Wait for services to be healthy (about 2-3 minutes)
docker compose ps

# Check service health
curl http://localhost:8080/health
```

### 3. Test Healthcare AI
```bash
# Send a test query
curl -X POST http://localhost:8080/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "I need help with elderly care"}'

# Expected response:
{
  "response": "For elderly care support: 1) Consider in-home care services...",
  "category": "senior_care",
  "confidence": 0.92,
  "cached": false
}
```

### 4. Access Web Interfaces
- **Healthcare Chat UI**: http://localhost:8080
- **API Documentation**: http://localhost:8080/docs
- **MLflow UI**: http://localhost:5001
- **MinIO Console**: http://localhost:9001 (minioadmin/minioadmin)

## 🛠️ Local Development Setup

### 1. Create Python Virtual Environment
```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Set Environment Variables
```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your settings
# Key variables:
HEALTHCARE_SERVICE_URL=http://localhost:8080
MLFLOW_TRACKING_URI=http://localhost:5001
POSTGRES_USER=mlops
POSTGRES_PASSWORD=mlops123
```

### 3. Run Services Locally
```bash
# Start infrastructure services only
docker compose up -d postgres redis minio

# Run Healthcare AI locally
cd models/healthcare-ai
python service.py

# In another terminal, run MLOps services
cd services/model-registry
python main.py
```

### 4. Run Tests
```bash
# Run all tests
make test

# Run specific test suites
pytest tests/unit/ -v          # Unit tests
pytest tests/integration/ -v    # Integration tests
pytest tests/e2e/ -v           # End-to-end tests

# Check test coverage
pytest tests/ --cov=models/healthcare-ai/src --cov-report=html
```

## 📦 Working with MLOps Services

### Model Registry
```python
# Register a new model
import requests

response = requests.post("http://localhost:8000/api/v1/models", json={
    "name": "healthcare-classifier-v2",
    "framework": "sklearn",
    "model_type": "classification",
    "description": "Improved healthcare query classifier"
})
model_id = response.json()["id"]
```

### Pipeline Orchestrator
```python
# Create and run a pipeline
pipeline = {
    "name": "healthcare-training-pipeline",
    "tasks": [
        {
            "name": "prepare-data",
            "operator": "data_validation"
        },
        {
            "name": "train-model",
            "operator": "model_training",
            "upstream_tasks": ["prepare-data"]
        }
    ]
}

# Create pipeline
resp = requests.post("http://localhost:8001/api/v1/pipelines", json=pipeline)
pipeline_id = resp.json()["id"]

# Run pipeline
run = requests.post("http://localhost:8001/api/v1/runs", json={
    "pipeline_id": pipeline_id
})
```

### Feature Store
```python
# Create feature set
feature_set = {
    "name": "user_health_features",
    "description": "User health interaction features",
    "entities": ["user_id"],
    "features": [
        {
            "name": "query_count_7d",
            "data_type": "int",
            "description": "Queries in last 7 days"
        }
    ]
}

resp = requests.post("http://localhost:8002/api/v1/feature-sets", json=feature_set)
```

## 🔧 Configuration

### Service Ports
| Service | Port | Description |
|---------|------|-------------|
| Healthcare AI | 8080 | Main application |
| Model Registry | 8000 | Model management |
| Pipeline Orchestrator | 8001 | Workflow engine |
| Feature Store | 8002 | Feature serving |
| MLflow | 5001 | Experiment tracking |
| PostgreSQL | 5432 | Database |
| Redis | 6379 | Caching |
| MinIO | 9000/9001 | Object storage |

### Memory Allocation
```yaml
# docker-compose.yml service limits
services:
  healthcare-ai:
    mem_limit: 2g
  postgres:
    mem_limit: 1g
  redis:
    mem_limit: 512m
```

## 🐛 Troubleshooting

### Service Won't Start
```bash
# Check logs
docker compose logs healthcare-ai

# Common issues:
# - Port already in use: Change port in docker-compose.yml
# - Memory issues: Increase Docker memory allocation
# - Permission issues: Run with proper user permissions
```

### Database Connection Issues
```bash
# Check PostgreSQL is running
docker compose ps postgres

# Test connection
docker compose exec postgres psql -U mlops -d mlops_platform

# Reset database if needed
docker compose down -v
docker compose up -d
```

### Model Loading Errors
```bash
# Ensure model file exists
ls models/healthcare-ai/model.pkl

# Retrain if missing
python scripts/train_healthcare_model.py
```

## 📚 Next Steps

1. **Explore the API**: Visit http://localhost:8080/docs
2. **Try Different Queries**: Test various healthcare scenarios
3. **Monitor Services**: Check Grafana dashboards
4. **Customize Responses**: Modify contextual overrides
5. **Train New Models**: Use the MLOps pipeline

## 🎯 Common Tasks

### Update Healthcare Responses
```python
# Edit contextual scenarios
vim models/healthcare-ai/src/healthcare_trained_engine.py

# Restart service
docker compose restart healthcare-ai
```

### Add New ML Model
```bash
# Train new model
python scripts/train_with_mlflow_logging.py

# Register with Model Registry
python scripts/register_model.py
```

### Monitor Performance
```bash
# View real-time metrics
open http://localhost:3000  # Grafana

# Check service stats
curl http://localhost:8080/stats
```

## 🤝 Getting Help

- **Documentation**: Browse `/docs` folder
- **Issues**: [GitHub Issues](https://github.com/sushil-negi/mlops-project/issues)
- **Logs**: `docker compose logs -f [service-name]`
- **Community**: Join our Discord/Slack (if available)