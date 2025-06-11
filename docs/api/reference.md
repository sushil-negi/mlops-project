# API Reference

## Overview

This document provides a comprehensive reference for all APIs in the Healthcare AI MLOps Platform.

## Base URLs

| Service | Base URL | API Docs |
|---------|----------|----------|
| Healthcare AI | `http://localhost:8080` | `/docs` |
| Model Registry | `http://localhost:8000` | `/docs` |
| Pipeline Orchestrator | `http://localhost:8001` | `/docs` |
| Feature Store | `http://localhost:8002` | `/docs` |

## Healthcare AI API

### Chat Endpoint

#### POST `/chat`
Process healthcare queries with AI assistance.

**Request:**
```json
{
  "message": "string",
  "session_id": "string (optional)"
}
```

**Response:**
```json
{
  "response": "string",
  "category": "string",
  "confidence": 0.95,
  "method": "ml_classification | contextual_analysis",
  "cached": false,
  "generation_time": 0.023,
  "is_crisis": false
}
```

**Example:**
```bash
curl -X POST http://localhost:8080/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "I need help managing my medications"}'
```

### Health Check

#### GET `/health`
Check service health status.

**Response:**
```json
{
  "status": "healthy",
  "model_loaded": true,
  "cache_connected": true,
  "response_time_ms": 1.2
}
```

### Statistics

#### GET `/stats`
Get service statistics and metrics.

**Response:**
```json
{
  "total_requests": 1523,
  "cache_hits": 892,
  "cache_hit_rate": 0.585,
  "average_response_time": 0.045,
  "categories_distribution": {
    "senior_medication": 234,
    "adl_mobility": 189
  },
  "crisis_detections": 3,
  "model_type": "ml_classification"
}
```

## Model Registry API

### Models

#### POST `/api/v1/models`
Register a new model.

**Request:**
```json
{
  "name": "string",
  "framework": "sklearn|tensorflow|pytorch|xgboost",
  "model_type": "classification|regression|clustering",
  "description": "string",
  "team": "string",
  "project": "string",
  "metadata": {}
}
```

**Response:**
```json
{
  "id": "uuid",
  "name": "string",
  "framework": "string",
  "created_at": "2024-01-15T10:30:00Z",
  "stage": "development"
}
```

#### GET `/api/v1/models`
List all models with filtering.

**Query Parameters:**
- `framework`: Filter by ML framework
- `team`: Filter by team
- `stage`: Filter by lifecycle stage
- `page`: Page number (default: 1)
- `size`: Page size (default: 20)

**Response:**
```json
{
  "models": [...],
  "total": 45,
  "page": 1,
  "size": 20
}
```

#### GET `/api/v1/models/{model_id}`
Get specific model details.

#### PUT `/api/v1/models/{model_id}/stage`
Update model stage.

**Request:**
```json
{
  "stage": "development|staging|production|archived"
}
```

### Model Versions

#### POST `/api/v1/models/{model_id}/versions`
Create new model version.

**Request:**
```json
{
  "version": "1.0.0",
  "storage_uri": "s3://models/path",
  "metrics": {
    "accuracy": 0.95,
    "f1_score": 0.93
  },
  "hyperparameters": {},
  "training_data": "dataset_v1"
}
```

### Experiments

#### POST `/api/v1/experiments`
Create new experiment.

**Request:**
```json
{
  "name": "string",
  "model_id": "uuid",
  "description": "string",
  "parameters": {}
}
```

## Pipeline Orchestrator API

### Pipelines

#### POST `/api/v1/pipelines`
Create new pipeline.

**Request:**
```json
{
  "name": "string",
  "description": "string",
  "owner": "string",
  "schedule": "cron expression (optional)",
  "tasks": [
    {
      "name": "string",
      "operator": "data_ingestion|data_validation|model_training|model_registration|custom_script",
      "parameters": {},
      "upstream_tasks": ["task_name"],
      "retry_count": 3,
      "cpu": 1.0,
      "memory_gb": 2.0,
      "gpu": 0
    }
  ]
}
```

#### GET `/api/v1/pipelines`
List all pipelines.

#### PUT `/api/v1/pipelines/{pipeline_id}`
Update pipeline definition.

#### DELETE `/api/v1/pipelines/{pipeline_id}`
Delete pipeline.

### Pipeline Runs

#### POST `/api/v1/runs`
Start pipeline execution.

**Request:**
```json
{
  "pipeline_id": "uuid",
  "parameters": {},
  "triggered_by": "manual|scheduled|api"
}
```

**Response:**
```json
{
  "run_id": "uuid",
  "pipeline_id": "uuid",
  "status": "queued",
  "start_time": null,
  "task_executions": [...]
}
```

#### GET `/api/v1/runs/{run_id}`
Get run status.

**Response:**
```json
{
  "run_id": "uuid",
  "status": "running|success|failed|cancelled",
  "progress": 0.45,
  "start_time": "2024-01-15T10:30:00Z",
  "end_time": null,
  "task_executions": [
    {
      "task_id": "string",
      "status": "success",
      "duration_seconds": 45.2,
      "error_message": null
    }
  ]
}
```

#### POST `/api/v1/runs/{run_id}/cancel`
Cancel running pipeline.

#### GET `/api/v1/runs/{run_id}/logs`
Get execution logs.

### Monitoring

#### GET `/monitoring/metrics`
Get system metrics.

**Response:**
```json
{
  "scheduler": {
    "active_runs": 3,
    "queued_runs": 1,
    "success_rate": 0.92
  },
  "resources": {
    "cpu_utilization": 45.2,
    "memory_utilization": 62.8,
    "available_workers": 7
  }
}
```

## Feature Store API

### Feature Sets

#### POST `/api/v1/feature-sets`
Create feature set.

**Request:**
```json
{
  "name": "string",
  "description": "string",
  "entities": ["user_id"],
  "owner": "string",
  "source_type": "batch|stream",
  "offline_enabled": true,
  "online_enabled": true,
  "materialization_schedule": "0 */6 * * *"
}
```

#### GET `/api/v1/feature-sets`
List feature sets.

### Features

#### POST `/api/v1/features`
Define new feature.

**Request:**
```json
{
  "name": "string",
  "feature_set_id": "uuid",
  "description": "string",
  "data_type": "int|float|string|boolean",
  "default_value": null,
  "transformation": "SQL or Python expression",
  "validation_rules": {
    "min_value": 0,
    "max_value": 100
  }
}
```

### Feature Serving

#### POST `/api/v1/serving/online`
Get features for online serving.

**Request:**
```json
{
  "feature_sets": ["user_profile"],
  "entities": {
    "user_id": ["123", "456"]
  },
  "features": ["age", "purchase_count"]
}
```

**Response:**
```json
{
  "features": {
    "123": {
      "age": 28,
      "purchase_count": 156
    }
  },
  "metadata": {
    "latency_ms": 3.2,
    "cache_hit": true
  }
}
```

#### POST `/api/v1/serving/historical`
Get historical features for training.

**Request:**
```json
{
  "feature_sets": ["user_profile"],
  "entity_df": {
    "columns": ["user_id", "timestamp"],
    "data": [
      ["123", "2024-01-01T00:00:00"],
      ["456", "2024-01-01T00:00:00"]
    ]
  },
  "features": ["age", "purchase_count"]
}
```

### Feature Materialization

#### POST `/api/v1/feature-sets/{id}/materialize`
Trigger feature computation.

**Request:**
```json
{
  "start_date": "2024-01-01T00:00:00",
  "end_date": "2024-01-31T23:59:59",
  "incremental": true
}
```

## Common Patterns

### Authentication
```bash
# API Key authentication (when enabled)
curl -H "X-API-Key: your-api-key" http://localhost:8000/api/v1/models
```

### Pagination
```bash
# Standard pagination parameters
?page=2&size=50
```

### Filtering
```bash
# Multiple filters
?framework=sklearn&stage=production&team=ml-team
```

### Error Responses
```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Model with ID 'xyz' not found",
    "details": {}
  }
}
```

### Rate Limiting
- Healthcare AI: 100 requests/minute
- Model Registry: 1000 requests/minute
- Pipeline Orchestrator: 500 requests/minute
- Feature Store: 10000 requests/minute (online serving)

## SDKs and Client Libraries

### Python SDK
```python
from mlops_platform import ModelRegistry, PipelineOrchestrator, FeatureStore

# Initialize clients
registry = ModelRegistry("http://localhost:8000")
orchestrator = PipelineOrchestrator("http://localhost:8001")
feature_store = FeatureStore("http://localhost:8002")

# Use the services
model = registry.register_model(name="my-model", framework="sklearn")
pipeline = orchestrator.create_pipeline(name="training-pipeline")
features = feature_store.get_online_features(entities={"user": "123"})
```

### REST Client Examples
```python
import requests

class MLOpsClient:
    def __init__(self, base_url):
        self.base_url = base_url
        self.session = requests.Session()
    
    def create_model(self, **kwargs):
        return self.session.post(
            f"{self.base_url}/api/v1/models",
            json=kwargs
        ).json()
```

## Webhooks

### Pipeline Events
```json
{
  "event": "pipeline.completed",
  "pipeline_id": "uuid",
  "run_id": "uuid",
  "status": "success",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Model Events
```json
{
  "event": "model.promoted",
  "model_id": "uuid",
  "from_stage": "staging",
  "to_stage": "production",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## API Versioning

All APIs follow semantic versioning:
- Current version: `v1`
- Version in URL: `/api/v1/...`
- Deprecation policy: 6 months notice
- Version header: `X-API-Version: 1`