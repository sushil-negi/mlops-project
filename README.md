# Healthcare AI Assistant Platform

A sophisticated healthcare chatbot system that provides specific, contextual responses for healthcare-related queries using machine learning and rule-based contextual overrides.

## Overview

This platform provides intelligent healthcare assistance through:
- **ML-powered classification** across 11 healthcare categories
- **Contextual response generation** for specific scenarios (bed mobility, medication management, etc.)
- **Crisis detection and emergency response** with immediate 988 hotline connection
- **Professional healthcare guidance** with appropriate medical disclaimers
- **Comprehensive testing suite** ensuring 80%+ code coverage

## System Architecture

```
Healthcare AI (Port 8080)
├── ML Model: TfidfVectorizer + MultinomialNB (98.18% accuracy)
├── Contextual Override System
├── Crisis Detection
├── Response Caching
└── Professional Healthcare Responses (55+)

Supporting Services:
├── MLflow (Port 5001) - Experiment tracking
├── PostgreSQL (Port 5432) - Metadata storage  
├── MinIO (Ports 9000-9001) - Artifact storage
└── Redis (Port 6379) - Caching layer
```

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.11+ (for development)

### Running the System

```bash
# Start all services
docker compose up -d

# Check service health
curl http://localhost:8080/health

# Test the chat interface
curl -X POST -H "Content-Type: application/json" \
  -d '{"message": "My elderly father has trouble getting out of bed"}' \
  http://localhost:8080/chat
```

### Access Points
- **Chat Interface**: http://localhost:8080
- **Health Check**: http://localhost:8080/health
- **Statistics**: http://localhost:8080/stats
- **MLflow UI**: http://localhost:5001

## Key Features

### 🎯 Contextual Response System
Provides specific, actionable responses for common healthcare scenarios:
- Elderly bed mobility assistance
- Medication reminders for memory issues
- Caregiver overwhelm support  
- Senior exercise recommendations
- Adaptive eating equipment
- Wheelchair transfer guidance
- Mental health support (depression, anxiety)

### 🚨 Crisis Detection
Automatically detects suicide/self-harm mentions and provides:
- Immediate 988 crisis line connection
- Emergency resources and support
- 24/7 crisis intervention guidance

### 🧠 ML Classification
- **11 Healthcare Categories**: ADL, mental health, medications, crisis intervention
- **98.18% Accuracy**: Trained TfidfVectorizer + MultinomialNB model
- **55+ Professional Responses**: Diverse, healthcare-appropriate guidance

### 🔒 Safety Features
- Professional medical disclaimers on all responses
- Crisis intervention protocols
- Healthcare provider consultation recommendations
- HIPAA-compliant response patterns

## Testing

### Run Tests
```bash
# Unit tests
python -m pytest tests/unit/ -v

# Integration tests  
python -m pytest tests/integration/ -v

# E2E tests (requires services running)
python -m pytest tests/e2e/ -v

# All tests with coverage
python -m pytest tests/ --cov=models/healthcare-ai/src --cov-report=html
```

### Test Coverage
- **82% coverage** on core healthcare engine
- **25+ unit tests** for contextual overrides
- **Integration tests** for ML classification
- **E2E tests** for complete system validation

## Development

### Project Structure
```
├── models/healthcare-ai/          # Core AI service
│   ├── src/                      # Python source code
│   ├── Dockerfile               # Container configuration
│   └── requirements.txt         # Dependencies
├── tests/                        # Comprehensive test suite
├── data/                        # Training datasets
├── scripts/                     # Utility scripts
└── infrastructure/             # Docker & K8s configs
```

### Training New Models
```bash
# Generate training data
python scripts/train_real_healthcare_model.py

# Train with MLflow tracking
python scripts/train_with_mlflow_logging.py
```

### Adding New Contextual Scenarios
1. Update `_check_specific_scenarios()` in `healthcare_trained_engine.py`
2. Add corresponding unit tests
3. Update test suite documentation

## Healthcare Categories

The system handles 11 specialized healthcare categories:
- **ADL Mobility**: Transfer assistance, balance, walking aids
- **ADL Self-Care**: Bathing, dressing, eating, grooming
- **Senior Medication**: Pill organization, reminders, safety
- **Senior Social**: Isolation, community connection, activities
- **Mental Health**: Anxiety and depression support
- **Caregiver Support**: Respite care, burnout prevention
- **Disability Equipment**: Adaptive tools, accessibility
- **Disability Rights**: ADA accommodations, advocacy
- **Crisis Mental Health**: Emergency intervention, 988 support

## Response Quality Standards

All responses include:
- ✅ Numbered, actionable steps
- ✅ Professional healthcare disclaimers (⚠️)
- ✅ Specific, contextual advice
- ✅ Safety considerations
- ✅ Professional consultation recommendations

## Configuration

### Environment Variables
- `HEALTHCARE_SERVICE_URL`: Service endpoint (default: http://localhost:8080)
- `MLFLOW_TRACKING_URI`: MLflow server URL
- `POSTGRES_*`: Database configuration
- `MINIO_*`: Object storage configuration

### Docker Services
All services are configured via `docker-compose.yml`:
- Healthcare AI service with health checks
- MLflow server with PostgreSQL backend
- MinIO for artifact storage
- Redis for caching

## Contributing

1. Add new contextual scenarios in `healthcare_trained_engine.py`
2. Write corresponding tests in `tests/unit/`
3. Update documentation
4. **Review pipeline requirements** - See [Pipeline Guide](docs/pipeline-guide.md) for CI/CD workflow
5. Run full test suite before committing
6. Ensure 80%+ test coverage maintained

## Development Workflows

### 📋 **Pipeline Usage Guide**
See [docs/pipeline-guide.md](docs/pipeline-guide.md) for detailed information on:
- **When to use** CI vs ML vs Security pipelines
- **Expected runtimes** and trigger conditions  
- **Local testing** procedures before pushing
- **Pipeline artifacts** and troubleshooting
- **Healthcare AI specific** validation requirements

## License

This project is for educational and demonstration purposes.

## Support

For technical issues:
- Check service health: `curl http://localhost:8080/health`
- View logs: `docker logs mlops-healthcare-ai`
- Review test output: `python -m pytest tests/ -v`

For healthcare emergencies: **Call 911 or 988 immediately**