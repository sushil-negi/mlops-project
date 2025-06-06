"""
Model Registration Script for Demo LLM
Registers trained model with MLOps platform
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path
from typing import Dict, Optional
import requests
import hashlib
import tarfile
import shutil
from datetime import datetime

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))
from model import DemoLLMWrapper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ModelRegistrationClient:
    """Client for registering models with the MLOps platform"""
    
    def __init__(self, registry_url: str, api_key: Optional[str] = None):
        self.registry_url = registry_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()
        
        if api_key:
            self.session.headers.update({'Authorization': f'Bearer {api_key}'})
    
    def register_model(self, model_metadata: Dict) -> Dict:
        """Register a new model"""
        url = f"{self.registry_url}/api/v1/models/register"
        
        response = self.session.post(url, json=model_metadata)
        response.raise_for_status()
        
        return response.json()
    
    def upload_model_artifact(self, model_id: str, artifact_path: str) -> Dict:
        """Upload model artifact"""
        url = f"{self.registry_url}/api/v1/models/{model_id}/artifacts"
        
        with open(artifact_path, 'rb') as f:
            files = {'artifact': f}
            response = self.session.post(url, files=files)
        
        response.raise_for_status()
        return response.json()
    
    def update_model_stage(self, model_id: str, stage: str) -> Dict:
        """Update model stage (Development, Staging, Production)"""
        url = f"{self.registry_url}/api/v1/models/{model_id}/stage"
        
        response = self.session.put(url, json={'stage': stage})
        response.raise_for_status()
        
        return response.json()
    
    def get_model_info(self, model_id: str) -> Dict:
        """Get model information"""
        url = f"{self.registry_url}/api/v1/models/{model_id}"
        
        response = self.session.get(url)
        response.raise_for_status()
        
        return response.json()


def calculate_file_hash(filepath: str) -> str:
    """Calculate SHA256 hash of file"""
    hash_sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()


def create_model_package(model_dir: str, output_path: str) -> str:
    """Create a model package (tar.gz) for upload"""
    logger.info(f"Creating model package from {model_dir}")
    
    with tarfile.open(output_path, "w:gz") as tar:
        tar.add(model_dir, arcname=os.path.basename(model_dir))
    
    logger.info(f"Model package created: {output_path}")
    return output_path


def extract_model_metadata(model_dir: str) -> Dict:
    """Extract metadata from trained model"""
    metadata = {}
    
    # Load model config
    config_path = os.path.join(model_dir, 'config.json')
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = json.load(f)
        metadata['config'] = config
    
    # Load model info
    info_path = os.path.join(model_dir, 'model_info.json')
    if os.path.exists(info_path):
        with open(info_path, 'r') as f:
            model_info = json.load(f)
        metadata.update(model_info)
    
    # Load training metrics if available
    metrics_path = os.path.join(model_dir, 'training_metrics.json')
    if os.path.exists(metrics_path):
        with open(metrics_path, 'r') as f:
            metrics = json.load(f)
        metadata['training_metrics'] = metrics
    
    return metadata


def validate_model(model_dir: str) -> bool:
    """Validate that model directory contains required files"""
    required_files = ['model.pt', 'config.json', 'model_info.json']
    
    for file in required_files:
        if not os.path.exists(os.path.join(model_dir, file)):
            logger.error(f"Required file missing: {file}")
            return False
    
    # Test model loading
    try:
        model = DemoLLMWrapper(model_path=model_dir)
        test_result = model.predict("Test input", max_length=10)
        logger.info(f"Model validation successful. Test output: {test_result[:50]}...")
        return True
    except Exception as e:
        logger.error(f"Model validation failed: {e}")
        return False


def create_model_metadata(
    model_dir: str,
    model_name: str,
    version: str,
    description: str,
    tags: list,
    stage: str = "Development"
) -> Dict:
    """Create complete model metadata for registration"""
    
    # Extract model metadata
    extracted_metadata = extract_model_metadata(model_dir)
    
    # Create registration metadata
    metadata = {
        "name": model_name,
        "version": version,
        "description": description,
        "framework": "pytorch",
        "framework_version": "2.0.0+",
        "model_type": "language_model",
        "task": "text_generation",
        "stage": stage,
        "tags": tags,
        "created_at": datetime.utcnow().isoformat(),
        "model_config": extracted_metadata.get('config', {}),
        "model_info": {
            "architecture": extracted_metadata.get('architecture', 'GPT-2 Based'),
            "parameters": extracted_metadata.get('parameters', 0),
            "size_mb": 0,  # Will be calculated after packaging
        },
        "training_info": {
            "training_framework": "pytorch",
            "training_time": extracted_metadata.get('training_metrics', {}).get('training_time', 0),
            "dataset": "demo_dataset",
            "hyperparameters": extracted_metadata.get('config', {}),
            "metrics": extracted_metadata.get('training_metrics', {})
        },
        "deployment_info": {
            "serving_framework": "fastapi",
            "input_schema": {
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "max_length": {"type": "integer", "default": 100}
                },
                "required": ["text"]
            },
            "output_schema": {
                "type": "object",
                "properties": {
                    "generated_text": {"type": "array", "items": {"type": "string"}}
                }
            }
        },
        "quality_metrics": {
            "accuracy": extracted_metadata.get('training_metrics', {}).get('accuracy', 0),
            "loss": extracted_metadata.get('training_metrics', {}).get('val_loss', 0),
            "perplexity": extracted_metadata.get('training_metrics', {}).get('perplexity', 0)
        }
    }
    
    return metadata


def register_demo_model(
    model_dir: str,
    registry_url: str,
    model_name: str = "demo-llm",
    version: str = "1.0.0",
    description: str = "Demo LLM model for MLOps pipeline demonstration",
    tags: list = None,
    stage: str = "Development",
    api_key: str = None
) -> Dict:
    """Main function to register demo model"""
    
    if tags is None:
        tags = ["demo", "llm", "gpt2-based", "mlops"]
    
    logger.info(f"Starting model registration for {model_name} v{version}")
    
    # Validate model
    if not validate_model(model_dir):
        raise ValueError("Model validation failed")
    
    # Create model metadata
    metadata = create_model_metadata(
        model_dir, model_name, version, description, tags, stage
    )
    
    # Create model package
    package_path = f"/tmp/{model_name}-{version}.tar.gz"
    create_model_package(model_dir, package_path)
    
    # Calculate package size and hash
    package_size = os.path.getsize(package_path)
    package_hash = calculate_file_hash(package_path)
    
    metadata["model_info"]["size_mb"] = round(package_size / (1024 * 1024), 2)
    metadata["artifact_hash"] = package_hash
    
    try:
        # Initialize registry client
        client = ModelRegistrationClient(registry_url, api_key)
        
        # Register model
        logger.info("Registering model with registry...")
        registration_response = client.register_model(metadata)
        model_id = registration_response["model_id"]
        
        logger.info(f"Model registered successfully. Model ID: {model_id}")
        
        # Upload artifact
        logger.info("Uploading model artifact...")
        upload_response = client.upload_model_artifact(model_id, package_path)
        
        logger.info("Model artifact uploaded successfully")
        
        # Update stage if not Development
        if stage != "Development":
            logger.info(f"Updating model stage to {stage}...")
            client.update_model_stage(model_id, stage)
        
        # Get final model info
        final_model_info = client.get_model_info(model_id)
        
        result = {
            "model_id": model_id,
            "status": "registered",
            "registry_url": registry_url,
            "artifact_url": upload_response.get("artifact_url"),
            "model_info": final_model_info
        }
        
        logger.info("Model registration completed successfully!")
        return result
        
    finally:
        # Cleanup
        if os.path.exists(package_path):
            os.remove(package_path)


def main():
    parser = argparse.ArgumentParser(description="Register Demo LLM Model")
    parser.add_argument('--model-dir', type=str, required=True, help='Path to trained model directory')
    parser.add_argument('--registry-url', type=str, required=True, help='Model registry URL')
    parser.add_argument('--model-name', type=str, default='demo-llm', help='Model name')
    parser.add_argument('--version', type=str, default='1.0.0', help='Model version')
    parser.add_argument('--description', type=str, 
                       default='Demo LLM model for MLOps pipeline demonstration', 
                       help='Model description')
    parser.add_argument('--tags', type=str, nargs='+', 
                       default=['demo', 'llm', 'gpt2-based', 'mlops'], 
                       help='Model tags')
    parser.add_argument('--stage', type=str, default='Development',
                       choices=['Development', 'Staging', 'Production'],
                       help='Model stage')
    parser.add_argument('--api-key', type=str, help='API key for registry authentication')
    parser.add_argument('--output', type=str, help='Output file for registration result')
    
    args = parser.parse_args()
    
    try:
        result = register_demo_model(
            model_dir=args.model_dir,
            registry_url=args.registry_url,
            model_name=args.model_name,
            version=args.version,
            description=args.description,
            tags=args.tags,
            stage=args.stage,
            api_key=args.api_key
        )
        
        # Save result if output specified
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(result, f, indent=2)
            logger.info(f"Registration result saved to {args.output}")
        
        # Print result
        print(json.dumps(result, indent=2))
        
    except Exception as e:
        logger.error(f"Model registration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()