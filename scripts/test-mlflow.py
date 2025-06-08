#!/usr/bin/env python3
"""Test MLflow tracking by creating a sample experiment"""

import mlflow
import mlflow.sklearn
import numpy as np
from sklearn.datasets import make_classification
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

# Set MLflow tracking URI
mlflow.set_tracking_uri("http://localhost:5001")

# Create or get experiment
experiment_name = "Demo-LLM-Experiment"
mlflow.set_experiment(experiment_name)

print(f"Starting MLflow experiment: {experiment_name}")
print(f"Tracking URI: {mlflow.get_tracking_uri()}")

# Start MLflow run
with mlflow.start_run(run_name="test-run-001"):
    # Log parameters
    n_estimators = 100
    max_depth = 10
    mlflow.log_param("n_estimators", n_estimators)
    mlflow.log_param("max_depth", max_depth)
    mlflow.log_param("model_type", "RandomForest")

    # Generate dummy data
    X, y = make_classification(
        n_samples=1000, n_features=20, n_informative=15, random_state=42
    )
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # Train model
    print("Training model...")
    model = RandomForestClassifier(
        n_estimators=n_estimators, max_depth=max_depth, random_state=42
    )
    model.fit(X_train, y_train)

    # Calculate metrics
    train_score = model.score(X_train, y_train)
    test_score = model.score(X_test, y_test)

    # Log metrics
    mlflow.log_metric("train_accuracy", train_score)
    mlflow.log_metric("test_accuracy", test_score)

    # Log model
    mlflow.sklearn.log_model(model, "model")

    # Log additional metrics over "epochs"
    for epoch in range(5):
        mlflow.log_metric("loss", 2.5 - (epoch * 0.3), step=epoch)
        mlflow.log_metric("learning_rate", 0.01 * (0.95**epoch), step=epoch)

    print(f"Run completed!")
    print(f"Train accuracy: {train_score:.3f}")
    print(f"Test accuracy: {test_score:.3f}")
    print(f"Check the MLflow UI at http://localhost:5001")
