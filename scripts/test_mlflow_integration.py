#!/usr/bin/env python3
"""Test MLflow integration with all core services"""

import time

import mlflow
import mlflow.sklearn
import numpy as np
import requests
from sklearn.datasets import make_classification
from sklearn.ensemble import RandomForestClassifier


def test_mlflow_connection():
    """Test basic MLflow connectivity"""
    print("Testing MLflow connection...")
    mlflow.set_tracking_uri("http://localhost:5050")

    try:
        experiments = mlflow.search_experiments()
        print(f"✓ Connected to MLflow. Found {len(experiments)} experiments")
        return True
    except Exception as e:
        print(f"✗ Failed to connect to MLflow: {e}")
        return False


def test_minio_integration():
    """Test MLflow artifact storage in MinIO"""
    print("\nTesting MinIO integration...")
    mlflow.set_tracking_uri("http://localhost:5050")

    try:
        # Create a test experiment
        experiment_name = "test-minio-integration"
        experiment = mlflow.create_experiment(
            experiment_name, artifact_location="s3://mlflow-artifacts/test"
        )

        # Train a simple model
        X, y = make_classification(n_samples=100, n_features=4, random_state=42)
        model = RandomForestClassifier(n_estimators=10, random_state=42)
        model.fit(X, y)

        # Log model to MLflow
        with mlflow.start_run(experiment_id=experiment):
            mlflow.log_param("n_estimators", 10)
            mlflow.log_metric("accuracy", 0.95)
            mlflow.sklearn.log_model(model, "model")

            # Log an artifact
            with open("test_artifact.txt", "w") as f:
                f.write("Test artifact for MinIO integration")
            mlflow.log_artifact("test_artifact.txt")

            run_id = mlflow.active_run().info.run_id

        print(f"✓ Model and artifacts logged successfully (run_id: {run_id})")

        # Clean up
        import os

        os.remove("test_artifact.txt")

        return True
    except Exception as e:
        print(f"✗ Failed MinIO integration test: {e}")
        return False


def test_redis_caching():
    """Test Redis connectivity"""
    print("\nTesting Redis connection...")
    try:
        import redis

        r = redis.Redis(host="localhost", port=6379, db=0)
        r.set("test_key", "test_value", ex=10)
        value = r.get("test_key")

        if value == b"test_value":
            print("✓ Redis caching working correctly")
            return True
        else:
            print("✗ Redis test failed")
            return False
    except Exception as e:
        print(f"✗ Failed to connect to Redis: {e}")
        return False


def test_postgres_metadata():
    """Test PostgreSQL metadata store"""
    print("\nTesting PostgreSQL metadata store...")
    try:
        import psycopg2

        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="mlflow",
            user="mlflow",
            password="mlflow123",
        )
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM experiments;")
        count = cur.fetchone()[0]
        print(f"✓ PostgreSQL connected. Found {count} experiments in database")
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"✗ Failed to connect to PostgreSQL: {e}")
        return False


def test_services_endpoints():
    """Test all service endpoints"""
    print("\nTesting service endpoints...")

    endpoints = [
        ("MLflow UI", "http://localhost:5050"),
        ("MinIO Console", "http://localhost:9001"),
        ("MinIO API", "http://localhost:9000"),
    ]

    results = []
    for name, url in endpoints:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code < 400:
                print(f"✓ {name} accessible at {url}")
                results.append(True)
            else:
                print(f"✗ {name} returned status {response.status_code}")
                results.append(False)
        except Exception as e:
            print(f"✗ {name} not accessible: {e}")
            results.append(False)

    return all(results)


def main():
    """Run all integration tests"""
    print("=== MLOps Core Services Integration Test ===\n")

    tests = [
        test_mlflow_connection,
        test_minio_integration,
        test_redis_caching,
        test_postgres_metadata,
        test_services_endpoints,
    ]

    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"Test failed with error: {e}")
            results.append(False)
        time.sleep(1)

    print("\n=== Summary ===")
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total} tests")

    if passed == total:
        print("\n✓ All MLOps core services are working correctly!")
        print("\nAccess the services at:")
        print("  - MLflow UI: http://localhost:5050")
        print("  - MinIO Console: http://localhost:9001 (minioadmin/minioadmin123)")
        print("  - PostgreSQL: localhost:5432 (mlflow/mlflow123)")
        print("  - Redis: localhost:6379")
    else:
        print("\n⚠️  Some services need attention")

    return passed == total


if __name__ == "__main__":
    # Install required packages
    import subprocess
    import sys

    packages = ["mlflow", "scikit-learn", "redis", "psycopg2-binary"]
    for package in packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            print(f"Installing {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])

    exit(0 if main() else 1)
