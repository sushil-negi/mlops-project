#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
MINIO_ENDPOINT="http://localhost:9000"
MINIO_ACCESS_KEY="minioadmin"
MINIO_SECRET_KEY="minioadmin123"
MLFLOW_BUCKET="mlflow-artifacts"
DOCKER_NETWORK="mlops-network"

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Check if MinIO is running
check_minio_running() {
    print_status "Checking if MinIO is running..."
    
    if ! docker ps | grep -q "minio/minio"; then
        print_error "MinIO container is not running!"
        print_status "Starting MinIO with docker-compose..."
        docker-compose up -d minio
        sleep 10
    else
        print_success "MinIO is running"
    fi
}

# Install MinIO client if not present
install_mc_client() {
    print_status "Checking MinIO client (mc)..."
    
    if ! command -v mc &> /dev/null; then
        print_status "Installing MinIO client..."
        
        # Detect OS and install accordingly
        OS="$(uname -s)"
        case "${OS}" in
            Linux*)
                wget https://dl.min.io/client/mc/release/linux-amd64/mc
                chmod +x mc
                sudo mv mc /usr/local/bin/
                ;;
            Darwin*)
                if command -v brew &> /dev/null; then
                    brew install minio/stable/mc
                else
                    curl -O https://dl.min.io/client/mc/release/darwin-amd64/mc
                    chmod +x mc
                    sudo mv mc /usr/local/bin/
                fi
                ;;
            *)
                print_error "Unsupported OS: ${OS}"
                exit 1
                ;;
        esac
    fi
    
    print_success "MinIO client is available"
}

# Configure MinIO client
configure_mc() {
    print_status "Configuring MinIO client..."
    
    # Remove existing alias if it exists
    mc alias remove minio-local 2>/dev/null || true
    
    # Add MinIO server as an alias
    mc alias set minio-local ${MINIO_ENDPOINT} ${MINIO_ACCESS_KEY} ${MINIO_SECRET_KEY}
    
    print_success "MinIO client configured"
}

# Create and configure bucket
setup_bucket() {
    print_status "Setting up MinIO bucket '${MLFLOW_BUCKET}'..."
    
    # Create bucket if it doesn't exist
    if mc ls minio-local/${MLFLOW_BUCKET} 2>/dev/null; then
        print_warning "Bucket '${MLFLOW_BUCKET}' already exists"
    else
        mc mb minio-local/${MLFLOW_BUCKET}
        print_success "Created bucket '${MLFLOW_BUCKET}'"
    fi
    
    # Set bucket policy to allow public read access
    print_status "Setting bucket policy..."
    
    # Create a policy file
    cat > /tmp/bucket-policy.json <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {"AWS": "*"},
            "Action": [
                "s3:GetBucketLocation",
                "s3:ListBucket"
            ],
            "Resource": "arn:aws:s3:::${MLFLOW_BUCKET}"
        },
        {
            "Effect": "Allow",
            "Principal": {"AWS": "*"},
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject"
            ],
            "Resource": "arn:aws:s3:::${MLFLOW_BUCKET}/*"
        }
    ]
}
EOF
    
    # Apply the policy
    mc anonymous set-json /tmp/bucket-policy.json minio-local/${MLFLOW_BUCKET}
    rm /tmp/bucket-policy.json
    
    print_success "Bucket policy applied"
}

# Test bucket access from container
test_container_access() {
    print_status "Testing MinIO access from MLflow container..."
    
    # Run a test from within the docker network
    docker run --rm \
        --network ${DOCKER_NETWORK} \
        -e AWS_ACCESS_KEY_ID=${MINIO_ACCESS_KEY} \
        -e AWS_SECRET_ACCESS_KEY=${MINIO_SECRET_KEY} \
        -e MLFLOW_S3_ENDPOINT_URL=http://minio:9000 \
        python:3.11-slim bash -c "
            pip install boto3 --quiet
            python -c '
import boto3
from botocore.client import Config

# Configure S3 client
s3 = boto3.client(
    \"s3\",
    endpoint_url=\"http://minio:9000\",
    aws_access_key_id=\"${MINIO_ACCESS_KEY}\",
    aws_secret_access_key=\"${MINIO_SECRET_KEY}\",
    config=Config(signature_version=\"s3v4\"),
    region_name=\"us-east-1\"
)

# List buckets
try:
    buckets = s3.list_buckets()
    print(\"✅ Successfully connected to MinIO\")
    print(\"Buckets:\", [b[\"Name\"] for b in buckets[\"Buckets\"]])
    
    # Test write access
    s3.put_object(
        Bucket=\"${MLFLOW_BUCKET}\",
        Key=\"test/connection.txt\",
        Body=b\"Test connection successful\"
    )
    print(\"✅ Successfully wrote test file\")
    
    # Test read access
    response = s3.get_object(Bucket=\"${MLFLOW_BUCKET}\", Key=\"test/connection.txt\")
    content = response[\"Body\"].read()
    print(\"✅ Successfully read test file:\", content.decode())
    
    # Clean up
    s3.delete_object(Bucket=\"${MLFLOW_BUCKET}\", Key=\"test/connection.txt\")
    print(\"✅ Successfully deleted test file\")
    
except Exception as e:
    print(\"❌ Error:\", str(e))
    exit(1)
'
        "
    
    if [ $? -eq 0 ]; then
        print_success "Container access test passed"
    else
        print_error "Container access test failed"
        return 1
    fi
}

# Restart MLflow service
restart_mlflow() {
    print_status "Restarting MLflow service..."
    
    docker-compose restart mlflow
    
    print_status "Waiting for MLflow to be ready..."
    sleep 10
    
    # Check if MLflow is responding
    for i in {1..30}; do
        if curl -s http://localhost:5001/health > /dev/null 2>&1; then
            print_success "MLflow is ready"
            return 0
        fi
        echo -n "."
        sleep 1
    done
    
    print_error "MLflow failed to start properly"
    return 1
}

# Display access information
display_info() {
    echo ""
    print_status "MinIO Access Information:"
    echo -e "${BLUE}MinIO Console:${NC} http://localhost:9001"
    echo -e "${BLUE}Username:${NC} ${MINIO_ACCESS_KEY}"
    echo -e "${BLUE}Password:${NC} ${MINIO_SECRET_KEY}"
    echo -e "${BLUE}Bucket:${NC} ${MLFLOW_BUCKET}"
    echo ""
    print_status "MLflow Configuration:"
    echo -e "${BLUE}MLflow UI:${NC} http://localhost:5001"
    echo -e "${BLUE}Artifact Root:${NC} s3://${MLFLOW_BUCKET}/"
    echo ""
}

# Test MLflow artifact upload
test_mlflow_artifacts() {
    print_status "Testing MLflow artifact upload..."
    
    python3 - <<EOF
import mlflow
import os
import tempfile

# Configure MLflow
mlflow.set_tracking_uri("http://localhost:5001")

try:
    # Create a test experiment
    experiment_name = "test-minio-permissions"
    experiment = mlflow.create_experiment(
        experiment_name,
        artifact_location="s3://${MLFLOW_BUCKET}/test-experiment"
    )
    
    # Start a run
    with mlflow.start_run(experiment_id=experiment) as run:
        # Log a parameter
        mlflow.log_param("test_param", "test_value")
        
        # Create and log an artifact
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("This is a test artifact for MinIO permissions")
            artifact_path = f.name
        
        mlflow.log_artifact(artifact_path)
        os.unlink(artifact_path)
        
        print(f"✅ Successfully uploaded artifact to run: {run.info.run_id}")
        print(f"   View in MLflow UI: http://localhost:5001/#/experiments/{experiment}/runs/{run.info.run_id}")
        
except Exception as e:
    print(f"❌ Failed to upload artifact: {e}")
    exit(1)
EOF
    
    if [ $? -eq 0 ]; then
        print_success "MLflow artifact upload test passed"
    else
        print_error "MLflow artifact upload test failed"
        return 1
    fi
}

# Main execution
main() {
    echo "🔧 Fixing MinIO permissions for MLflow artifacts..."
    echo ""
    
    check_minio_running
    install_mc_client
    configure_mc
    setup_bucket
    test_container_access
    restart_mlflow
    test_mlflow_artifacts
    display_info
    
    print_success "MinIO permissions fixed successfully! 🎉"
    echo ""
    echo "You can now:"
    echo "1. Access MinIO console at http://localhost:9001"
    echo "2. View MLflow experiments at http://localhost:5001"
    echo "3. Upload artifacts without permission errors"
}

# Run main function
main "$@"