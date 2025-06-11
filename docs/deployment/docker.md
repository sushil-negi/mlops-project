# Docker Deployment Guide

This guide covers deploying the Healthcare AI MLOps Platform using Docker and Docker Compose.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Service Architecture](#service-architecture)
4. [Configuration](#configuration)
5. [Deployment Options](#deployment-options)
6. [Monitoring and Logging](#monitoring-and-logging)
7. [Troubleshooting](#troubleshooting)
8. [Production Considerations](#production-considerations)

## Prerequisites

### System Requirements

- Docker Engine 20.10+
- Docker Compose 2.0+
- Minimum 8GB RAM
- 20GB available disk space

### Installation

```bash
# Install Docker (Ubuntu/Debian)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

## Quick Start

1. Clone the repository:
   ```bash
   git clone https://github.com/your-org/mlops-project.git
   cd mlops-project
   ```

2. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. Start all services:
   ```bash
   docker-compose up -d
   ```

4. Verify deployment:
   ```bash
   docker-compose ps
   curl http://localhost:8080/health
   ```

## Service Architecture

### Core Services

```yaml
services:
  # Healthcare AI Model Service
  healthcare-ai:
    build: ./models/healthcare-ai
    ports:
      - "8080:8080"
    environment:
      - MODEL_PATH=/app/models
      - LOG_LEVEL=INFO
    volumes:
      - ./models:/app/models
    depends_on:
      - postgres
      - redis

  # MLflow Tracking Server
  mlflow:
    build: ./services/mlflow
    ports:
      - "5000:5000"
    environment:
      - BACKEND_STORE_URI=postgresql://mlflow:password@postgres/mlflow
      - ARTIFACT_ROOT=s3://mlflow-artifacts
    depends_on:
      - postgres
      - minio

  # Model Registry API
  model-registry:
    build: ./services/model-registry
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:password@postgres/modelregistry
    depends_on:
      - postgres
```

### Supporting Services

```yaml
services:
  # PostgreSQL Database
  postgres:
    image: postgres:14-alpine
    environment:
      - POSTGRES_USER=admin
      - POSTGRES_PASSWORD=password
      - POSTGRES_MULTIPLE_DATABASES=mlflow,modelregistry
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./infrastructure/docker/postgres/init.sql:/docker-entrypoint-initdb.d/init.sql

  # Redis Cache
  redis:
    image: redis:7-alpine
    command: redis-server --requirepass password
    volumes:
      - redis_data:/data

  # MinIO Object Storage
  minio:
    image: minio/minio:latest
    command: server /data --console-address ":9001"
    environment:
      - MINIO_ROOT_USER=admin
      - MINIO_ROOT_PASSWORD=password
    volumes:
      - minio_data:/data
    ports:
      - "9000:9000"
      - "9001:9001"
```

### Monitoring Stack

```yaml
services:
  # Prometheus
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./infrastructure/docker/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"

  # Grafana
  grafana:
    image: grafana/grafana:latest
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - ./infrastructure/docker/grafana/provisioning:/etc/grafana/provisioning
      - grafana_data:/var/lib/grafana
    ports:
      - "3000:3000"
```

## Configuration

### Environment Variables

Create a `.env` file with the following variables:

```bash
# Database Configuration
POSTGRES_USER=admin
POSTGRES_PASSWORD=secure_password
POSTGRES_DB=mlops

# MLflow Configuration
MLFLOW_TRACKING_URI=http://mlflow:5000
MLFLOW_S3_ENDPOINT_URL=http://minio:9000
AWS_ACCESS_KEY_ID=admin
AWS_SECRET_ACCESS_KEY=password

# Model Service Configuration
MODEL_SERVICE_PORT=8080
MODEL_CACHE_SIZE=1000
MODEL_TIMEOUT=30

# Monitoring
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000
```

### Docker Compose Profiles

Use profiles for different deployment scenarios:

```yaml
# docker-compose.yml
services:
  healthcare-ai:
    profiles: ["core", "all"]
  
  prometheus:
    profiles: ["monitoring", "all"]
  
  grafana:
    profiles: ["monitoring", "all"]
```

Deploy specific profiles:
```bash
# Core services only
docker-compose --profile core up -d

# With monitoring
docker-compose --profile all up -d
```

## Deployment Options

### Development Mode

```bash
# Start with hot-reload and debug logging
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

### Production Mode

```bash
# Build optimized images
docker-compose -f docker-compose.yml -f docker-compose.prod.yml build

# Deploy with production settings
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Scaling Services

```bash
# Scale the model service
docker-compose up -d --scale healthcare-ai=3

# Check scaled instances
docker-compose ps healthcare-ai
```

## Monitoring and Logging

### Accessing Logs

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f healthcare-ai

# Export logs
docker-compose logs > deployment.log
```

### Health Checks

All services include health check endpoints:

```bash
# Healthcare AI Service
curl http://localhost:8080/health

# MLflow
curl http://localhost:5000/health

# Model Registry
curl http://localhost:8000/health
```

### Metrics and Dashboards

1. Access Prometheus: http://localhost:9090
2. Access Grafana: http://localhost:3000
   - Default login: admin/admin
   - Pre-configured dashboards available

## Troubleshooting

### Common Issues

#### 1. Container Fails to Start

```bash
# Check logs
docker-compose logs <service-name>

# Inspect container
docker-compose ps
docker inspect <container-id>
```

#### 2. Database Connection Issues

```bash
# Verify database is running
docker-compose exec postgres pg_isready

# Check database logs
docker-compose logs postgres
```

#### 3. Port Conflicts

```bash
# Check port usage
sudo lsof -i :8080
sudo netstat -tulpn | grep 8080

# Use alternative ports in .env
MODEL_SERVICE_PORT=8081
```

#### 4. Volume Permission Issues

```bash
# Fix permissions
sudo chown -R $USER:$USER ./data
sudo chmod -R 755 ./data
```

### Debugging Commands

```bash
# Execute commands in running container
docker-compose exec healthcare-ai bash

# Check resource usage
docker stats

# Clean up resources
docker-compose down -v
docker system prune -a
```

## Production Considerations

### Security

1. **Use secrets management**:
   ```yaml
   services:
     healthcare-ai:
       secrets:
         - db_password
         - api_key
   
   secrets:
     db_password:
       external: true
     api_key:
       external: true
   ```

2. **Network isolation**:
   ```yaml
   networks:
     frontend:
     backend:
     monitoring:
   ```

3. **Read-only filesystems**:
   ```yaml
   services:
     healthcare-ai:
       read_only: true
       tmpfs:
         - /tmp
   ```

### Performance Optimization

1. **Resource limits**:
   ```yaml
   services:
     healthcare-ai:
       deploy:
         resources:
           limits:
             cpus: '2'
             memory: 4G
           reservations:
             cpus: '1'
             memory: 2G
   ```

2. **Health checks**:
   ```yaml
   healthcheck:
     test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
     interval: 30s
     timeout: 10s
     retries: 3
     start_period: 40s
   ```

### Backup and Recovery

```bash
# Backup volumes
docker run --rm -v mlops_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz /data

# Restore volumes
docker run --rm -v mlops_postgres_data:/data -v $(pwd):/backup alpine tar xzf /backup/postgres_backup.tar.gz -C /
```

### Monitoring Best Practices

1. Set up alerts for:
   - Container restarts
   - High CPU/memory usage
   - Failed health checks
   - Error rate thresholds

2. Log aggregation:
   - Use log drivers (json-file, syslog, fluentd)
   - Centralize logs with ELK stack or similar

3. Metrics collection:
   - Export custom metrics from applications
   - Set up Grafana dashboards for key metrics

## Next Steps

- [Kubernetes Deployment](./kubernetes.md) - For scalable production deployments
- [Production Guide](./production.md) - Best practices for production
- [Monitoring Setup](../monitoring/setup.md) - Detailed monitoring configuration