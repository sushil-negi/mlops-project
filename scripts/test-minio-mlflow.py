#!/usr/bin/env python3
"""
Test MinIO and MLflow integration
"""

import mlflow
import tempfile
import os
import sys
import time
from datetime import datetime

def test_mlflow_artifacts():
    """Test MLflow artifact storage in MinIO"""
    
    print("🧪 Testing MLflow with MinIO artifact storage...\n")
    
    # Set MLflow tracking URI
    mlflow.set_tracking_uri("http://localhost:5001")
    
    # Create experiment
    experiment_name = f"minio-test-{int(time.time())}"
    try:
        experiment_id = mlflow.create_experiment(
            experiment_name,
            artifact_location="s3://mlflow-artifacts/experiments"
        )
        print(f"✅ Created experiment: {experiment_name}")
    except Exception as e:
        print(f"❌ Failed to create experiment: {e}")
        return False
    
    # Start MLflow run
    try:
        with mlflow.start_run(experiment_id=experiment_id) as run:
            print(f"✅ Started MLflow run: {run.info.run_id}")
            
            # Log parameters
            mlflow.log_param("test_type", "minio_integration")
            mlflow.log_param("timestamp", datetime.now().isoformat())
            print("✅ Logged parameters")
            
            # Log metrics
            mlflow.log_metric("test_metric", 0.95)
            mlflow.log_metric("accuracy", 0.87)
            print("✅ Logged metrics")
            
            # Create and log text artifact
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write("MinIO Integration Test\n")
                f.write(f"Timestamp: {datetime.now()}\n")
                f.write(f"Run ID: {run.info.run_id}\n")
                text_path = f.name
            
            mlflow.log_artifact(text_path)
            os.unlink(text_path)
            print("✅ Logged text artifact")
            
            # Create and log JSON artifact
            import json
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                test_data = {
                    "model": "test_model",
                    "version": "1.0.0",
                    "metrics": {
                        "accuracy": 0.87,
                        "loss": 0.13
                    }
                }
                json.dump(test_data, f, indent=2)
                json_path = f.name
            
            mlflow.log_artifact(json_path)
            os.unlink(json_path)
            print("✅ Logged JSON artifact")
            
            # Create and log model (dummy)
            import pickle
            model = {"type": "dummy", "params": {"alpha": 0.5}}
            with tempfile.NamedTemporaryFile(suffix='.pkl', delete=False) as f:
                pickle.dump(model, f)
                model_path = f.name
            
            mlflow.log_artifact(model_path, "model")
            os.unlink(model_path)
            print("✅ Logged model artifact")
            
            print(f"\n📊 MLflow UI: http://localhost:5001/#/experiments/{experiment_id}/runs/{run.info.run_id}")
            print(f"📁 Artifact URI: {run.info.artifact_uri}")
            
            return True
            
    except Exception as e:
        print(f"❌ Error during MLflow run: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_minio_connection():
    """Check if MinIO is accessible"""
    import boto3
    from botocore.client import Config
    
    print("🔍 Checking MinIO connection...\n")
    
    try:
        s3 = boto3.client(
            's3',
            endpoint_url='http://localhost:9000',
            aws_access_key_id='minioadmin',
            aws_secret_access_key='minioadmin123',
            config=Config(signature_version='s3v4'),
            region_name='us-east-1'
        )
        
        # List buckets
        buckets = s3.list_buckets()
        print("✅ Connected to MinIO")
        print("📦 Available buckets:")
        for bucket in buckets['Buckets']:
            print(f"   - {bucket['Name']}")
        
        # Check mlflow-artifacts bucket
        bucket_name = 'mlflow-artifacts'
        try:
            s3.head_bucket(Bucket=bucket_name)
            print(f"\n✅ Bucket '{bucket_name}' exists and is accessible")
            
            # List objects in bucket
            objects = s3.list_objects_v2(Bucket=bucket_name, MaxKeys=5)
            if 'Contents' in objects:
                print(f"📄 Sample objects in '{bucket_name}':")
                for obj in objects['Contents'][:5]:
                    print(f"   - {obj['Key']}")
            
            return True
        except Exception as e:
            print(f"❌ Bucket '{bucket_name}' error: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Failed to connect to MinIO: {e}")
        return False

def main():
    """Main test function"""
    print("\n" + "="*60)
    print("MinIO + MLflow Integration Test")
    print("="*60 + "\n")
    
    # Check MinIO connection first
    if not check_minio_connection():
        print("\n⚠️  Please ensure MinIO is running and accessible")
        print("Run: docker-compose up -d minio")
        sys.exit(1)
    
    print("\n" + "-"*60 + "\n")
    
    # Test MLflow artifacts
    if test_mlflow_artifacts():
        print("\n✅ All tests passed! MinIO integration is working correctly.")
        print("\n🎉 You can now use MLflow with MinIO for artifact storage!")
    else:
        print("\n❌ Tests failed. Please check the configuration.")
        print("\nTroubleshooting:")
        print("1. Run: ./scripts/fix-minio-permissions.sh")
        print("2. Check docker logs: docker-compose logs mlflow minio")
        print("3. Verify environment variables in docker-compose.yml")
        sys.exit(1)

if __name__ == "__main__":
    main()