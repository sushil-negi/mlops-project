#!/usr/bin/env python3
"""
Setup script to configure MLflow for system metrics, traces, and artifacts
"""

import os
import sys
import requests
import time
import json
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = [
        'mlflow',
        'psutil', 
        'matplotlib',
        'seaborn'
    ]
    
    optional_packages = [
        'nvidia-ml-py',
        'gpustat'
    ]
    
    print("🔍 Checking dependencies...")
    
    missing_required = []
    missing_optional = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"  ✅ {package}")
        except ImportError:
            missing_required.append(package)
            print(f"  ❌ {package} (REQUIRED)")
    
    for package in optional_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"  ✅ {package}")
        except ImportError:
            missing_optional.append(package)
            print(f"  ⚠️  {package} (OPTIONAL - for GPU monitoring)")
    
    if missing_required:
        print(f"\n❌ Missing required packages: {', '.join(missing_required)}")
        print("Install with: pip install " + " ".join(missing_required))
        return False
    
    if missing_optional:
        print(f"\n⚠️  Missing optional packages: {', '.join(missing_optional)}")
        print("For GPU monitoring, install with: pip install " + " ".join(missing_optional))
    
    return True

def check_mlflow_server():
    """Check if MLflow server is accessible"""
    print("\n🔍 Checking MLflow server...")
    
    mlflow_url = "http://localhost:5001"
    
    try:
        response = requests.get(f"{mlflow_url}/health", timeout=10)
        if response.status_code == 200:
            print(f"  ✅ MLflow server accessible at {mlflow_url}")
            return True
        else:
            print(f"  ❌ MLflow server returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"  ❌ Cannot connect to MLflow server at {mlflow_url}")
        print("  Please ensure MLflow is running with: docker-compose up mlflow")
        return False
    except Exception as e:
        print(f"  ❌ Error checking MLflow server: {e}")
        return False

def setup_system_metrics_experiment():
    """Create a test experiment with system metrics"""
    print("\n🧪 Setting up system metrics test experiment...")
    
    try:
        import mlflow
        import mlflow.sklearn
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.datasets import make_classification
        import psutil
        import matplotlib.pyplot as plt
        import tempfile
        
        # Set tracking URI
        mlflow.set_tracking_uri("http://localhost:5001")
        
        # Create experiment
        experiment_name = "System-Metrics-Test"
        try:
            experiment = mlflow.create_experiment(experiment_name)
            print(f"  ✅ Created experiment: {experiment_name}")
        except Exception:
            # Experiment might already exist
            mlflow.set_experiment(experiment_name)
            experiment = mlflow.get_experiment_by_name(experiment_name)
            print(f"  ✅ Using existing experiment: {experiment_name}")
        
        # Start run with system metrics
        with mlflow.start_run(run_name="system-metrics-test"):
            
            # Enable autolog
            mlflow.sklearn.autolog()
            
            # Log system information
            system_info = {
                "cpu_count": psutil.cpu_count(),
                "memory_total_gb": psutil.virtual_memory().total / (1024**3),
                "python_version": sys.version,
                "platform": sys.platform
            }
            mlflow.log_params(system_info)
            
            # Create and train a simple model
            X, y = make_classification(n_samples=1000, n_features=20, random_state=42)
            model = RandomForestClassifier(n_estimators=10, random_state=42)
            
            # Log system metrics before training
            cpu_before = psutil.cpu_percent(interval=1)
            memory_before = psutil.virtual_memory()
            
            # Train model
            model.fit(X, y)
            accuracy = model.score(X, y)
            
            # Log system metrics after training
            cpu_after = psutil.cpu_percent(interval=1)
            memory_after = psutil.virtual_memory()
            
            # Log metrics
            mlflow.log_metrics({
                "accuracy": accuracy,
                "cpu_before_training": cpu_before,
                "cpu_after_training": cpu_after,
                "memory_percent_before": memory_before.percent,
                "memory_percent_after": memory_after.percent,
                "memory_used_gb": memory_after.used / (1024**3)
            })
            
            # Create and log a simple plot
            plt.figure(figsize=(8, 6))
            plt.bar(['CPU Before', 'CPU After'], [cpu_before, cpu_after])
            plt.title('CPU Usage Before and After Training')
            plt.ylabel('CPU Percentage')
            
            plot_path = tempfile.mktemp(suffix='_cpu_usage.png')
            plt.savefig(plot_path)
            mlflow.log_artifact(plot_path, artifact_path="system_metrics")
            plt.close()
            os.remove(plot_path)
            
            # Get run info
            run = mlflow.active_run()
            run_id = run.info.run_id
            
            print(f"  ✅ Test run completed successfully")
            print(f"  📊 Run ID: {run_id}")
            print(f"  🔗 View at: http://localhost:5001/#/experiments/{experiment.experiment_id}/runs/{run_id}")
            
            return True
            
    except Exception as e:
        print(f"  ❌ Error setting up test experiment: {e}")
        return False

def verify_artifact_storage():
    """Verify that artifacts can be stored and retrieved"""
    print("\n📦 Verifying artifact storage...")
    
    try:
        import mlflow
        import tempfile
        import json
        
        mlflow.set_tracking_uri("http://localhost:5001")
        
        with mlflow.start_run(run_name="artifact-storage-test"):
            
            # Create test artifacts
            
            # 1. JSON artifact
            test_data = {
                "message": "This is a test artifact",
                "timestamp": time.time(),
                "system_info": {
                    "python_version": sys.version,
                    "platform": sys.platform
                }
            }
            
            json_path = tempfile.mktemp(suffix='_test.json')
            with open(json_path, 'w') as f:
                json.dump(test_data, f, indent=2)
            
            mlflow.log_artifact(json_path, artifact_path="test_artifacts")
            
            # 2. Text artifact
            text_path = tempfile.mktemp(suffix='_test.txt')
            with open(text_path, 'w') as f:
                f.write("This is a test text artifact for MLflow storage verification.")
            
            mlflow.log_artifact(text_path, artifact_path="test_artifacts")
            
            # 3. Plot artifact
            import matplotlib.pyplot as plt
            import numpy as np
            
            x = np.linspace(0, 10, 100)
            y = np.sin(x)
            
            plt.figure(figsize=(10, 6))
            plt.plot(x, y, 'b-', linewidth=2)
            plt.title('Test Plot Artifact')
            plt.xlabel('X values')
            plt.ylabel('sin(x)')
            plt.grid(True, alpha=0.3)
            
            plot_path = tempfile.mktemp(suffix='_test_plot.png')
            plt.savefig(plot_path, dpi=150, bbox_inches='tight')
            mlflow.log_artifact(plot_path, artifact_path="test_artifacts")
            plt.close()
            
            # Clean up temp files
            for path in [json_path, text_path, plot_path]:
                try:
                    os.remove(path)
                except:
                    pass
            
            run = mlflow.active_run()
            run_id = run.info.run_id
            
            print(f"  ✅ Artifacts logged successfully")
            print(f"  📦 Logged: JSON, text, and plot artifacts")
            print(f"  🔗 View artifacts at: http://localhost:5001/#/experiments/0/runs/{run_id}")
            
            return True
            
    except Exception as e:
        print(f"  ❌ Error verifying artifact storage: {e}")
        return False

def create_usage_example():
    """Create an example script showing how to use system metrics"""
    print("\n📝 Creating usage example...")
    
    example_script = '''#!/usr/bin/env python3
"""
Example: Training with System Metrics and Artifacts

This script demonstrates how to integrate system metrics collection
and artifact logging into your ML training pipeline.
"""

import mlflow
import mlflow.pytorch
import psutil
import matplotlib.pyplot as plt
import torch
import torch.nn as nn
import tempfile
import os

def log_system_metrics(step=None):
    """Log current system metrics to MLflow"""
    
    # CPU metrics
    cpu_percent = psutil.cpu_percent(interval=1)
    
    # Memory metrics  
    memory = psutil.virtual_memory()
    
    # Disk metrics
    disk = psutil.disk_usage('/')
    
    mlflow.log_metrics({
        "system/cpu_percent": cpu_percent,
        "system/memory_percent": memory.percent,
        "system/memory_used_gb": memory.used / (1024**3),
        "system/disk_percent": disk.percent
    }, step=step)
    
    return {
        "cpu_percent": cpu_percent,
        "memory_percent": memory.percent
    }

def create_training_plot(metrics_history):
    """Create and log training visualization"""
    
    if not metrics_history:
        return
    
    epochs = list(range(len(metrics_history)))
    losses = [m.get('loss', 0) for m in metrics_history]
    
    plt.figure(figsize=(10, 6))
    plt.plot(epochs, losses, 'b-', marker='o')
    plt.title('Training Loss Over Time')
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.grid(True, alpha=0.3)
    
    # Save and log plot
    plot_path = tempfile.mktemp(suffix='_training_loss.png')
    plt.savefig(plot_path, dpi=150, bbox_inches='tight')
    mlflow.log_artifact(plot_path, artifact_path="training_plots")
    plt.close()
    os.remove(plot_path)

def example_training():
    """Example training function with comprehensive logging"""
    
    # Set MLflow
    mlflow.set_tracking_uri("http://localhost:5001")
    mlflow.set_experiment("Example-Training-With-Metrics")
    
    with mlflow.start_run():
        
        # Enable autolog
        mlflow.pytorch.autolog()
        
        # Log system info
        system_info = {
            "cpu_count": psutil.cpu_count(),
            "memory_total_gb": psutil.virtual_memory().total / (1024**3)
        }
        mlflow.log_params(system_info)
        
        # Training loop
        metrics_history = []
        
        for epoch in range(5):
            
            # Simulate training step
            loss = 1.0 - (epoch * 0.1) + (0.05 * (epoch % 2))
            
            # Log training metrics
            mlflow.log_metric("loss", loss, step=epoch)
            
            # Log system metrics
            system_metrics = log_system_metrics(step=epoch)
            
            metrics_history.append({"loss": loss, **system_metrics})
            
            print(f"Epoch {epoch+1}: Loss={loss:.3f}, "
                  f"CPU={system_metrics['cpu_percent']:.1f}%, "
                  f"Memory={system_metrics['memory_percent']:.1f}%")
        
        # Create and log training visualization
        create_training_plot(metrics_history)
        
        print("✅ Training completed with system metrics and artifacts!")

if __name__ == "__main__":
    example_training()
'''
    
    example_path = Path("/Users/snegi/Documents/github/mlops-project/scripts/example_training_with_metrics.py")
    
    try:
        with open(example_path, 'w') as f:
            f.write(example_script)
        
        # Make it executable
        os.chmod(example_path, 0o755)
        
        print(f"  ✅ Created example script: {example_path}")
        print(f"  🚀 Run with: python {example_path}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error creating example script: {e}")
        return False

def print_summary_and_recommendations():
    """Print setup summary and recommendations"""
    
    print("\n" + "="*60)
    print("🎉 MLflow System Metrics Setup Summary")
    print("="*60)
    
    print("\n✅ COMPLETED SETUP:")
    print("  • Updated MLflow Dockerfile with system monitoring dependencies")
    print("  • Added system metrics environment variables")
    print("  • Updated docker-compose.yml configuration")
    print("  • Created enhanced training script with comprehensive logging")
    print("  • Created system metrics configuration")
    print("  • Created usage examples")
    
    print("\n🚀 TO ENABLE SYSTEM METRICS IN YOUR TRAINING:")
    
    print("\n1. Rebuild and restart MLflow:")
    print("   cd /Users/snegi/Documents/github/mlops-project")
    print("   docker-compose down")
    print("   docker-compose build mlflow")
    print("   docker-compose up -d")
    
    print("\n2. Install dependencies in your training environment:")
    print("   pip install psutil nvidia-ml-py gpustat matplotlib seaborn")
    
    print("\n3. Use autolog in your training scripts:")
    print("   import mlflow.pytorch")
    print("   mlflow.pytorch.autolog(log_models=True)")
    
    print("\n4. Add system metrics collection:")
    print("   # See example script for implementation details")
    print("   python scripts/example_training_with_metrics.py")
    
    print("\n5. Run the enhanced training demo:")
    print("   python scripts/enhanced_training_with_metrics.py")
    
    print("\n📊 WHAT YOU'LL SEE IN MLFLOW:")
    print("  • CPU, memory, disk usage metrics")
    print("  • GPU utilization and temperature (if available)")
    print("  • Training progress plots")
    print("  • System performance visualizations")
    print("  • Model artifacts and checkpoints")
    print("  • Training metadata and configuration")
    
    print("\n🔗 ACCESS POINTS:")
    print("  • MLflow UI: http://localhost:5001")
    print("  • Experiments: System-Metrics-Test, Enhanced-Training-With-System-Metrics")
    
    print("\n⚠️  TROUBLESHOOTING:")
    print("  • If GPU metrics not working: Install nvidia-ml-py")
    print("  • If plots not showing: Check matplotlib and seaborn installation")
    print("  • If artifacts not uploading: Check MinIO connection and credentials")
    print("  • For permission issues: Ensure Docker has access to system resources")

def main():
    """Main setup function"""
    
    print("🔧 MLflow System Metrics, Traces & Artifacts Setup")
    print("="*55)
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Please install missing dependencies before continuing")
        return False
    
    # Check MLflow server
    if not check_mlflow_server():
        print("\n❌ Please start MLflow server before continuing")
        print("Run: docker-compose up -d mlflow")
        return False
    
    # Setup test experiment
    if not setup_system_metrics_experiment():
        print("\n❌ Failed to setup test experiment")
        return False
    
    # Verify artifact storage
    if not verify_artifact_storage():
        print("\n❌ Failed to verify artifact storage")
        return False
    
    # Create usage example
    if not create_usage_example():
        print("\n❌ Failed to create usage example")
        return False
    
    # Print summary
    print_summary_and_recommendations()
    
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 Setup completed successfully!")
        print("Follow the recommendations above to enable system metrics in your training.")
    else:
        print("\n❌ Setup failed. Please check the errors above.")
        sys.exit(1)