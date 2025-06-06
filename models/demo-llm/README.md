# Demo LLM Model

A lightweight Large Language Model (LLM) implementation designed for demonstrating the Cirruslabs MLOps platform capabilities.

## Overview

This demo LLM is based on the GPT-2 architecture but with reduced complexity to make it suitable for demonstration and testing purposes. It showcases the complete ML lifecycle including training, evaluation, registration, and deployment through the MLOps pipeline.

## Model Architecture

- **Base Architecture**: GPT-2 inspired transformer
- **Parameters**: ~124M (configurable)
- **Hidden Size**: 384 (smaller than standard GPT-2)
- **Layers**: 6 (vs 12 in GPT-2 small)
- **Attention Heads**: 6
- **Vocabulary Size**: 50,257 (GPT-2 tokenizer)
- **Max Sequence Length**: 512 tokens

## Features

- **Lightweight**: Optimized for quick training and inference
- **MLOps Ready**: Full integration with the MLOps platform
- **Configurable**: Easy to adjust model size and training parameters
- **Production Ready**: Includes serving infrastructure and monitoring
- **Containerized**: Docker support for consistent deployment

## Directory Structure

```
demo-llm/
├── src/
│   ├── model.py              # Model implementation
│   └── inference_service.py  # FastAPI serving service
├── scripts/
│   ├── train.py              # Training script
│   └── register_model.py     # Model registration script
├── config/
│   ├── training_config.yaml  # Training configuration
│   └── data_config.yaml      # Data configuration
├── pipelines/
│   └── training_pipeline.yaml # MLOps pipeline definition
├── requirements.txt          # Python dependencies
├── Dockerfile               # Container definition
└── README.md               # This file
```

## Quick Start

### 1. Environment Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Or use Docker
docker build -t demo-llm .
```

### 2. Training the Model

```bash
# Local training
python scripts/train.py \
    --config config/training_config.yaml \
    --output-dir ./models/demo-llm-v1 \
    --data-config config/data_config.yaml

# Using Docker
docker run -v $(pwd)/models:/app/models demo-llm \
    python scripts/train.py \
    --config config/training_config.yaml \
    --output-dir /app/models/demo-llm-v1
```

### 3. Testing the Model

```python
from src.model import DemoLLMWrapper

# Load trained model
model = DemoLLMWrapper(model_path="./models/demo-llm-v1/best_model")

# Generate text
result = model.predict(
    text="The future of machine learning is",
    max_length=100,
    temperature=0.7
)
print(result)
```

### 4. Starting Inference Service

```bash
# Local development
cd src && python inference_service.py

# Using Docker
docker run -p 8000:8000 \
    -v $(pwd)/models:/app/models \
    -e MODEL_PATH=/app/models/demo-llm-v1/best_model \
    demo-llm

# Test the API
curl -X POST "http://localhost:8000/generate" \
     -H "Content-Type: application/json" \
     -d '{"text": "Machine learning is", "max_length": 50}'
```

### 5. Registering with MLOps Platform

```bash
python scripts/register_model.py \
    --model-dir ./models/demo-llm-v1/best_model \
    --registry-url http://localhost:8001 \
    --model-name demo-llm \
    --version 1.0.0 \
    --stage Development
```

## MLOps Pipeline Integration

### Training Pipeline

The model integrates with the MLOps platform through a complete training pipeline:

1. **Data Preparation**: Loads and preprocesses demo text data
2. **Data Validation**: Validates data quality and format
3. **Model Training**: Trains the LLM with configurable parameters
4. **Model Evaluation**: Evaluates performance metrics
5. **Quality Gates**: Validates model meets quality criteria
6. **Model Registration**: Registers approved models in the registry
7. **Auto Deployment**: Deploys to staging environment

### Running the Pipeline

```bash
# Deploy pipeline to Kubernetes
kubectl apply -f pipelines/training_pipeline.yaml

# Trigger pipeline execution
argo submit pipelines/training_pipeline.yaml \
    --parameter model-version=1.1.0 \
    --parameter max-epochs=5
```

## API Endpoints

The inference service provides the following endpoints:

- `GET /` - Service information
- `GET /health` - Health check
- `GET /model/info` - Model information
- `GET /metrics` - Performance metrics
- `POST /generate` - Generate text
- `POST /generate/batch` - Batch text generation
- `POST /model/reload` - Reload model

### Example API Usage

```python
import requests

# Generate text
response = requests.post("http://localhost:8000/generate", json={
    "text": "Artificial intelligence will",
    "max_length": 100,
    "temperature": 0.8,
    "top_p": 0.9
})

result = response.json()
print(result["generated_text"][0])
```

## Configuration

### Training Configuration

Key training parameters in `config/training_config.yaml`:

```yaml
model_name: "demo-llm"
version: "1.0.0"
learning_rate: 5e-5
batch_size: 4
max_epochs: 3
hidden_size: 384
num_layers: 6
```

### Model Serving Configuration

Environment variables for inference service:

- `MODEL_PATH`: Path to trained model directory
- `CONFIG_PATH`: Path to model configuration file
- `HOST`: Service host (default: 0.0.0.0)
- `PORT`: Service port (default: 8000)

## Monitoring and Metrics

The model includes comprehensive monitoring:

### Training Metrics
- Training/validation loss
- Perplexity
- Generation time
- Model parameters

### Serving Metrics
- Request count
- Response time
- Error rate
- Model memory usage

### MLOps Integration
- Model registry tracking
- Experiment logging with MLflow
- Performance monitoring
- Drift detection ready

## Performance Characteristics

### Training Performance
- Training time: ~5 minutes on CPU (demo data)
- Memory usage: ~2GB RAM
- Model size: ~500MB

### Inference Performance
- Latency: ~100-200ms per request
- Throughput: ~5-10 requests/second (CPU)
- Memory: ~1GB for serving

## Scaling and Deployment

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: demo-llm-serving
spec:
  replicas: 3
  selector:
    matchLabels:
      app: demo-llm
  template:
    spec:
      containers:
      - name: demo-llm
        image: demo-llm:latest
        resources:
          requests:
            cpu: 500m
            memory: 1Gi
          limits:
            cpu: 1000m
            memory: 2Gi
```

### Auto-scaling

The service supports horizontal pod autoscaling based on CPU/memory usage and custom metrics.

## Limitations

This is a demo model with the following limitations:

1. **Reduced Parameters**: Smaller than production LLMs
2. **Limited Training Data**: Uses synthetic demo data
3. **Simplified Architecture**: Optimized for speed over capability
4. **No Fine-tuning**: Basic pre-training only
5. **English Only**: No multilingual support

## Contributing

To improve the demo model:

1. Adjust model architecture in `src/model.py`
2. Modify training parameters in `config/training_config.yaml`
3. Update pipeline steps in `pipelines/training_pipeline.yaml`
4. Test changes with the MLOps platform

## Integration Examples

### With Model Registry
```python
from scripts.register_model import register_demo_model

result = register_demo_model(
    model_dir="./models/demo-llm-v1/best_model",
    registry_url="http://model-registry:8000",
    model_name="demo-llm",
    version="1.0.0"
)
```

### With Monitoring
```python
import mlflow

mlflow.set_tracking_uri("http://mlflow:5000")
with mlflow.start_run():
    # Training code here
    mlflow.log_metrics({"loss": 0.5, "perplexity": 1.6})
    mlflow.pytorch.log_model(model, "demo-llm")
```

This demo model serves as a complete example of integrating an LLM with the Cirruslabs MLOps platform, demonstrating best practices for model development, training, deployment, and monitoring.