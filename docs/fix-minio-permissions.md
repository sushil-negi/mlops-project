# Fixing MinIO S3 Permissions for MLflow

This guide helps resolve "Access Denied" errors when MLflow tries to upload artifacts to MinIO.

## Quick Fix

Run the automated fix script:

```bash
./scripts/fix-minio-permissions.sh
```

This script will:
1. Check if MinIO is running
2. Install MinIO client (mc) if needed
3. Create the `mlflow-artifacts` bucket
4. Set proper bucket permissions
5. Test the connection
6. Restart MLflow with correct configuration

## Manual Steps

### 1. Access MinIO Console

Open your browser and go to: http://localhost:9001

Login credentials:
- Username: `minioadmin`
- Password: `minioadmin123`

### 2. Create Buckets

In the MinIO console:
1. Click on "Buckets" in the left sidebar
2. Click "Create Bucket"
3. Create these buckets:
   - `mlflow-artifacts`
   - `models`
   - `datasets`
   - `experiments`

### 3. Set Bucket Policies

For each bucket, set the access policy:
1. Click on the bucket name
2. Go to "Access Policy" tab
3. Set to "Public" or add custom policy

### 4. Using MinIO Client (mc)

Install MinIO client:
```bash
# macOS
brew install minio/stable/mc

# Linux
wget https://dl.min.io/client/mc/release/linux-amd64/mc
chmod +x mc
sudo mv mc /usr/local/bin/
```

Configure and use:
```bash
# Add MinIO server
mc alias set minio-local http://localhost:9000 minioadmin minioadmin123

# Create bucket
mc mb minio-local/mlflow-artifacts

# Set public policy
mc anonymous set download minio-local/mlflow-artifacts

# List contents
mc ls minio-local/mlflow-artifacts
```

## Environment Variables

Ensure these are set for MLflow:

```bash
export AWS_ACCESS_KEY_ID=minioadmin
export AWS_SECRET_ACCESS_KEY=minioadmin123
export MLFLOW_S3_ENDPOINT_URL=http://localhost:9000
export MLFLOW_DEFAULT_ARTIFACT_ROOT=s3://mlflow-artifacts/
```

## Docker Configuration

The `docker-compose.override.yml` file includes:
- Automatic MinIO initialization
- Bucket creation on startup
- Proper permissions setup

## Debugging

Use the debug script to check configuration:

```bash
python scripts/debug-s3-config.py
```

This will:
- Check environment variables
- Test S3 connection
- Verify bucket permissions
- Test artifact upload

## Common Issues

### 1. "The specified bucket does not exist"
- Run: `mc mb minio-local/mlflow-artifacts`

### 2. "Access Denied"
- Check credentials match in all services
- Verify bucket policy is set correctly
- Ensure MLflow has S3 endpoint URL configured

### 3. "Connection refused"
- Check MinIO is running: `docker ps | grep minio`
- Verify port 9000 is accessible
- Check docker network connectivity

### 4. SSL/TLS Errors
- Set `MLFLOW_S3_IGNORE_TLS=true`
- Use `http://` not `https://` for local MinIO

## Testing

After fixing permissions, test with:

```python
import mlflow
import tempfile

mlflow.set_tracking_uri("http://localhost:5001")

with mlflow.start_run():
    # Log a parameter
    mlflow.log_param("test", "minio-permissions")
    
    # Create and log an artifact
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt') as f:
        f.write("Test artifact content")
        f.flush()
        mlflow.log_artifact(f.name)
    
    print("✅ Artifact uploaded successfully!")
```

## Service URLs

- MinIO Console: http://localhost:9001
- MinIO API: http://localhost:9000
- MLflow UI: http://localhost:5001

## Reset Everything

If you need to start fresh:

```bash
# Stop all services
docker-compose down

# Remove volumes (WARNING: This deletes all data)
docker-compose down -v

# Start fresh
docker-compose up -d
```