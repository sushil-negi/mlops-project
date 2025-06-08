# MinIO + MLflow Quick Start Guide

## 🚀 Quick Fix for "Access Denied" Errors

If you're getting "Access Denied" errors when MLflow tries to upload artifacts to MinIO, follow these steps:

### Option 1: Automated Fix (Recommended)

```bash
# Run the fix script
./scripts/fix-minio-permissions.sh
```

This will automatically:
- Install MinIO client
- Create required buckets
- Set proper permissions
- Test the connection
- Restart services if needed

### Option 2: Manual Fix

1. **Access MinIO Console**
   - URL: http://localhost:9001
   - Username: `minioadmin`
   - Password: `minioadmin123`

2. **Create the mlflow-artifacts bucket** (if it doesn't exist)
   - Click "Buckets" → "Create Bucket"
   - Name: `mlflow-artifacts`
   - Click "Create"

3. **Set bucket to public**
   - Click on the bucket
   - Go to "Access Policy"
   - Set to "Public"

### Option 3: Using Docker Compose Override

The project includes a `docker-compose.override.yml` that automatically initializes MinIO:

```bash
# Restart services with the override
docker compose down
docker compose up -d
```

## 🧪 Test the Configuration

Run the test script to verify everything works:

```bash
python scripts/test-minio-mlflow.py
```

Or test manually:

```python
import mlflow
mlflow.set_tracking_uri("http://localhost:5001")

with mlflow.start_run():
    mlflow.log_param("test", "success")
    mlflow.log_artifact("any_file.txt")  # This should work without errors
```

## 🔍 Debug Issues

If you're still having issues:

```bash
# Check detailed configuration
python scripts/debug-s3-config.py

# Check container logs
docker logs mlops-project-minio-1
docker logs mlops-mlflow
```

## 📋 Configuration Details

### Environment Variables (already set in docker-compose.yml)
- `AWS_ACCESS_KEY_ID=minioadmin`
- `AWS_SECRET_ACCESS_KEY=minioadmin123`
- `MLFLOW_S3_ENDPOINT_URL=http://minio:9000`
- `MLFLOW_DEFAULT_ARTIFACT_ROOT=s3://mlflow-artifacts/`

### Service URLs
- **MinIO Console**: http://localhost:9001
- **MinIO API**: http://localhost:9000
- **MLflow UI**: http://localhost:5001

## 🛠️ Common Issues & Solutions

### Issue: "The specified bucket does not exist"
```bash
# Create bucket manually
docker exec -it mlops-project-minio-1 mc alias set local http://localhost:9000 minioadmin minioadmin123
docker exec -it mlops-project-minio-1 mc mb local/mlflow-artifacts
```

### Issue: "Network connection error"
```bash
# Ensure services are on the same network
docker network ls
docker network inspect mlops-network
```

### Issue: "SSL certificate problem"
Add to your Python code:
```python
os.environ['MLFLOW_S3_IGNORE_TLS'] = 'true'
```

## 📚 More Information

- Detailed guide: `docs/fix-minio-permissions.md`
- MinIO docs: https://docs.min.io/
- MLflow docs: https://mlflow.org/docs/latest/tracking.html#artifact-stores