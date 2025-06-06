"""
Training script for Demo LLM Model
Simple training pipeline with MLOps integration
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple
import yaml

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset
from transformers import get_linear_schedule_with_warmup
import mlflow
import mlflow.pytorch
from datasets import load_dataset
from tqdm import tqdm

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))
from model import DemoLLMWrapper, SimpleLLM

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SimpleTextDataset(Dataset):
    """Simple text dataset for training"""
    
    def __init__(self, texts: list, tokenizer, max_length: int = 512):
        self.texts = texts
        self.tokenizer = tokenizer
        self.max_length = max_length
    
    def __len__(self):
        return len(self.texts)
    
    def __getitem__(self, idx):
        text = self.texts[idx]
        
        # Tokenize
        encoding = self.tokenizer(
            text,
            max_length=self.max_length,
            truncation=True,
            padding='max_length',
            return_tensors='pt'
        )
        
        input_ids = encoding['input_ids'].squeeze()
        attention_mask = encoding['attention_mask'].squeeze()
        
        # For language modeling, labels are the same as input_ids
        labels = input_ids.clone()
        
        return {
            'input_ids': input_ids,
            'attention_mask': attention_mask,
            'labels': labels
        }


class DemoLLMTrainer:
    """Trainer class for Demo LLM"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # Initialize model
        self.model = DemoLLMWrapper(config_path=None)
        self.model.config.update(config)
        
        # Training components
        self.optimizer = None
        self.scheduler = None
        self.train_dataloader = None
        self.val_dataloader = None
        
        # MLflow tracking
        self.use_mlflow = config.get('use_mlflow', True)
        if self.use_mlflow:
            mlflow.set_experiment(config.get('experiment_name', 'demo-llm-training'))
    
    def prepare_data(self, data_config: Dict):
        """Prepare training and validation data"""
        
        if data_config.get('dataset_name'):
            # Load from HuggingFace datasets
            dataset_name = data_config['dataset_name']
            dataset = load_dataset(dataset_name, split='train[:1000]')  # Small subset for demo
            texts = dataset['text'] if 'text' in dataset.features else dataset[list(dataset.features.keys())[0]]
        else:
            # Use default demo data
            texts = self._get_demo_data()
        
        # Split data
        split_idx = int(0.8 * len(texts))
        train_texts = texts[:split_idx]
        val_texts = texts[split_idx:]
        
        # Create datasets
        train_dataset = SimpleTextDataset(
            train_texts, 
            self.model.tokenizer, 
            max_length=self.config['max_length']
        )
        val_dataset = SimpleTextDataset(
            val_texts, 
            self.model.tokenizer, 
            max_length=self.config['max_length']
        )
        
        # Create dataloaders
        self.train_dataloader = DataLoader(
            train_dataset,
            batch_size=self.config['batch_size'],
            shuffle=True,
            num_workers=2
        )
        
        self.val_dataloader = DataLoader(
            val_dataset,
            batch_size=self.config['batch_size'],
            shuffle=False,
            num_workers=2
        )
        
        logger.info(f"Prepared {len(train_texts)} training and {len(val_texts)} validation samples")
    
    def _get_demo_data(self) -> list:
        """Get demo training data"""
        demo_texts = [
            "Machine learning is revolutionizing how we approach complex problems.",
            "The future of artificial intelligence lies in creating systems that can learn and adapt.",
            "Deep learning models have shown remarkable success in natural language processing.",
            "MLOps practices ensure reliable deployment and monitoring of machine learning models.",
            "Transformers have become the backbone of modern language understanding systems.",
            "Continuous integration and deployment are crucial for ML model lifecycle management.",
            "Data quality and model monitoring are essential for production ML systems.",
            "AutoML tools democratize machine learning by making it accessible to non-experts.",
            "Edge computing enables real-time inference for resource-constrained environments.",
            "Federated learning allows training models without centralizing sensitive data.",
            "Explainable AI helps build trust and understanding in machine learning decisions.",
            "Model versioning and experiment tracking improve reproducibility in ML projects.",
            "Kubernetes provides scalable infrastructure for deploying ML workloads.",
            "Feature stores centralize feature engineering and ensure consistency across models.",
            "A/B testing frameworks enable data-driven model performance evaluation.",
        ] * 10  # Repeat for more training data
        
        return demo_texts
    
    def setup_training(self):
        """Setup optimizer and scheduler"""
        # Optimizer
        self.optimizer = torch.optim.AdamW(
            self.model.model.parameters(),
            lr=self.config['learning_rate'],
            weight_decay=0.01
        )
        
        # Scheduler
        total_steps = len(self.train_dataloader) * self.config['max_epochs']
        self.scheduler = get_linear_schedule_with_warmup(
            self.optimizer,
            num_warmup_steps=total_steps // 10,
            num_training_steps=total_steps
        )
    
    def train_epoch(self) -> Dict:
        """Train for one epoch"""
        self.model.model.train()
        total_loss = 0
        num_batches = 0
        
        progress_bar = tqdm(self.train_dataloader, desc="Training")
        
        for batch in progress_bar:
            # Move to device
            input_ids = batch['input_ids'].to(self.device)
            attention_mask = batch['attention_mask'].to(self.device)
            labels = batch['labels'].to(self.device)
            
            # Forward pass
            outputs = self.model.model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                labels=labels
            )
            
            loss = outputs.loss
            
            # Backward pass
            self.optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.model.model.parameters(), 1.0)
            self.optimizer.step()
            self.scheduler.step()
            
            # Track metrics
            total_loss += loss.item()
            num_batches += 1
            
            progress_bar.set_postfix({'loss': loss.item()})
        
        avg_loss = total_loss / num_batches
        return {'train_loss': avg_loss}
    
    def validate(self) -> Dict:
        """Validate the model"""
        self.model.model.eval()
        total_loss = 0
        num_batches = 0
        
        with torch.no_grad():
            for batch in tqdm(self.val_dataloader, desc="Validation"):
                input_ids = batch['input_ids'].to(self.device)
                attention_mask = batch['attention_mask'].to(self.device)
                labels = batch['labels'].to(self.device)
                
                outputs = self.model.model(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    labels=labels
                )
                
                total_loss += outputs.loss.item()
                num_batches += 1
        
        avg_loss = total_loss / num_batches
        perplexity = torch.exp(torch.tensor(avg_loss))
        
        return {
            'val_loss': avg_loss,
            'perplexity': perplexity.item()
        }
    
    def train(self, output_dir: str):
        """Full training loop"""
        logger.info("Starting training...")
        
        if self.use_mlflow:
            mlflow.start_run()
            mlflow.log_params(self.config)
        
        best_val_loss = float('inf')
        
        try:
            for epoch in range(self.config['max_epochs']):
                logger.info(f"Epoch {epoch + 1}/{self.config['max_epochs']}")
                
                # Train
                train_metrics = self.train_epoch()
                
                # Validate
                val_metrics = self.validate()
                
                # Log metrics
                metrics = {**train_metrics, **val_metrics, 'epoch': epoch + 1}
                logger.info(f"Epoch {epoch + 1} metrics: {metrics}")
                
                if self.use_mlflow:
                    mlflow.log_metrics(metrics, step=epoch)
                
                # Save best model
                if val_metrics['val_loss'] < best_val_loss:
                    best_val_loss = val_metrics['val_loss']
                    self.save_model(output_dir, is_best=True)
                
                # Save checkpoint
                self.save_checkpoint(output_dir, epoch, metrics)
        
        finally:
            if self.use_mlflow:
                # Log final model
                mlflow.pytorch.log_model(self.model.model, "model")
                mlflow.end_run()
        
        logger.info("Training completed!")
    
    def save_model(self, output_dir: str, is_best: bool = False):
        """Save trained model"""
        os.makedirs(output_dir, exist_ok=True)
        
        # Save model using wrapper's save method
        save_path = os.path.join(output_dir, 'best_model' if is_best else 'final_model')
        self.model.save_model(save_path)
        
        logger.info(f"Model saved to {save_path}")
    
    def save_checkpoint(self, output_dir: str, epoch: int, metrics: Dict):
        """Save training checkpoint"""
        checkpoint_dir = os.path.join(output_dir, 'checkpoints')
        os.makedirs(checkpoint_dir, exist_ok=True)
        
        checkpoint = {
            'epoch': epoch,
            'model_state_dict': self.model.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'scheduler_state_dict': self.scheduler.state_dict(),
            'metrics': metrics,
            'config': self.config
        }
        
        checkpoint_path = os.path.join(checkpoint_dir, f'checkpoint_epoch_{epoch}.pt')
        torch.save(checkpoint, checkpoint_path)


def load_config(config_path: str) -> Dict:
    """Load training configuration"""
    with open(config_path, 'r') as f:
        if config_path.endswith('.yaml') or config_path.endswith('.yml'):
            return yaml.safe_load(f)
        else:
            return json.load(f)


def main():
    parser = argparse.ArgumentParser(description="Train Demo LLM Model")
    parser.add_argument('--config', type=str, required=True, help='Path to config file')
    parser.add_argument('--output-dir', type=str, required=True, help='Output directory')
    parser.add_argument('--data-config', type=str, help='Data configuration file')
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Load data configuration
    data_config = {}
    if args.data_config:
        data_config = load_config(args.data_config)
    
    # Initialize trainer
    trainer = DemoLLMTrainer(config)
    
    # Prepare data
    trainer.prepare_data(data_config)
    
    # Setup training
    trainer.setup_training()
    
    # Train
    trainer.train(args.output_dir)


if __name__ == "__main__":
    main()