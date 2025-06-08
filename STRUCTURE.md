# Healthcare AI MLOps Platform - Project Structure

## Core Components

### 🧠 Healthcare AI Models (`models/healthcare-ai/`)
```
models/healthcare-ai/
├── src/
│   ├── healthcare_ai_engine.py      # Advanced AI engine with LLM support
│   ├── healthcare_model.py          # Rule-based healthcare responses  
│   └── healthcare_trained_engine.py # ML-trained classification engine
├── config/                          # Training and data configurations
├── pipelines/                       # ML training pipeline definitions
├── model.pkl                        # Trained TfidfVectorizer + MultinomialNB model
├── Dockerfile                       # Container for healthcare AI service
└── requirements.txt                 # Python dependencies
```

### 📊 Data Pipeline (`data/`)
```
data/
├── *_healthcare_data.json          # Healthcare conversation datasets
├── *_healthcare_data.jsonl         # Line-delimited JSON format
├── *_healthcare_stats.json         # Dataset statistics and metadata
└── combined_healthcare_training_data.json # 525K combined training dataset
```

### 🔧 Scripts & Utilities (`scripts/`)
```
scripts/
├── start_healthcare_ai_service.py   # Launch healthcare AI service (Port 8091)
├── start_healthcare_service.py      # Launch basic healthcare service (Port 8090)
├── train_real_healthcare_model.py   # Train ML model with 11 categories
├── healthcare_data_generator.py     # Generate diverse healthcare datasets
├── enhanced_training_with_metrics.py # Advanced training with MLflow
├── production_data_pipeline.py      # Production data collection
├── real_data_collector.py          # Real-time data collection
├── specialized_healthcare_pipeline.py # End-to-end training pipeline
└── run_tests.py                    # Test execution and coverage
```

### 🧪 Testing Suite (`tests/`)
```
tests/
├── conftest.py                     # Shared test fixtures and configuration
├── unit/                           # Unit tests (45 tests)
│   ├── test_healthcare_simple.py      # Basic functionality tests
│   └── test_coverage_boost.py         # Comprehensive coverage tests
├── integration/                    # Integration tests (34 tests)
│   └── test_training_integration.py   # Training pipeline integration
└── e2e/                           # End-to-end tests (13 tests)
    └── test_healthcare_workflows.py   # Complete user workflows
```

### 🌐 Web Interface (`web-interface/`)
```
web-interface/
├── chat.html                      # General healthcare chat interface
└── healthcare_chat.html           # Specialized healthcare chat UI
```

### ⚙️ Infrastructure (`infrastructure/`)
```
infrastructure/
├── docker/                        # Service-specific Docker configurations
│   ├── grafana/                       # Monitoring dashboards
│   ├── postgres/                      # Database initialization
│   └── prometheus/                    # Metrics collection
└── kubernetes/                     # Kubernetes deployment manifests
    ├── namespace.yaml                 # MLOps platform namespace
    └── storage/                       # Persistent storage definitions
```

### 📚 Documentation (`docs/`)
```
docs/
├── mlops-implementation-plan.md    # Implementation strategy
├── mlops-implementation-timeline.md # Development timeline
├── mlops-modular-architecture.md   # Architecture documentation
├── mlops-rollout-plan.md          # Deployment strategy
├── mlops-testing-strategy.md      # Testing methodology
├── production-data-sources.md     # Data source documentation
└── fix-minio-permissions.md       # MinIO configuration guide
```

## Service Architecture

### Healthcare AI Services
- **Port 8090**: Basic healthcare service with rule-based responses
- **Port 8091**: Advanced ML-trained healthcare AI with 11 categories
- **Port 5001**: MLflow tracking server for experiment management

### Model Capabilities
- **11 Healthcare Categories**: ADL, mental health, medications, crisis intervention
- **55+ Unique Responses**: Diverse, professional healthcare guidance
- **Crisis Detection**: Automatic detection and emergency response protocols
- **98.18% Accuracy**: Trained TfidfVectorizer + MultinomialNB pipeline

### Data Sources
- **525K Healthcare Conversations**: Comprehensive training dataset
- **Multiple Specializations**: ADL, senior care, mental health, disabilities, respite care
- **Real-time Collection**: Production data pipeline integration
- **Quality Validation**: Automated content quality and safety checks

## Development Workflow

### 1. Model Training
```bash
python3 scripts/train_real_healthcare_model.py
```

### 2. Service Deployment
```bash
python3 scripts/start_healthcare_ai_service.py
```

### 3. Testing & Validation
```bash
python3 scripts/run_tests.py
```

### 4. Data Pipeline
```bash
python3 scripts/specialized_healthcare_pipeline.py
```

## Key Features

✅ **Enterprise-Ready**: Professional medical disclaimers and safety protocols  
✅ **Crisis-Safe**: Automatic crisis detection with emergency resource provision  
✅ **ML-Powered**: Trained machine learning models for accurate categorization  
✅ **Comprehensive Testing**: 80%+ code coverage with unit, integration, and E2E tests  
✅ **Production-Ready**: Containerized services with health checks and monitoring  
✅ **Compliance-Focused**: Healthcare-appropriate responses with professional guidance  

## Technology Stack

- **ML Framework**: scikit-learn (TfidfVectorizer + MultinomialNB)
- **Experiment Tracking**: MLflow with MinIO artifact storage
- **Services**: Python HTTP servers with JSON APIs
- **Testing**: pytest with coverage reporting
- **Containerization**: Docker with multi-stage builds
- **Orchestration**: Kubernetes manifests for production deployment
- **Monitoring**: Prometheus + Grafana stack