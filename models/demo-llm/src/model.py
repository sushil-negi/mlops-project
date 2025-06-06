"""
Simple Demo LLM Model for MLOps Pipeline
A lightweight text generation model for demonstration purposes
"""

import torch
import torch.nn as nn
from transformers import (
    GPT2LMHeadModel, 
    GPT2Tokenizer, 
    GPT2Config,
    PreTrainedModel,
    PreTrainedTokenizer
)
from typing import Dict, List, Optional, Tuple
import json
import os
import logging

logger = logging.getLogger(__name__)


class SimpleLLM(nn.Module):
    """
    Simple LLM implementation based on GPT-2 architecture
    Optimized for demo purposes with reduced complexity
    """
    
    def __init__(self, config: Dict):
        super().__init__()
        self.config = config
        
        # Use small GPT-2 configuration for demo
        self.gpt_config = GPT2Config(
            vocab_size=config.get('vocab_size', 50257),
            n_positions=config.get('max_length', 512),
            n_embd=config.get('hidden_size', 384),  # Smaller than default
            n_layer=config.get('num_layers', 6),    # Fewer layers
            n_head=config.get('num_heads', 6),      # Fewer attention heads
            resid_pdrop=config.get('dropout', 0.1),
            embd_pdrop=config.get('dropout', 0.1),
            attn_pdrop=config.get('dropout', 0.1),
        )
        
        # Initialize the model
        self.transformer = GPT2LMHeadModel(self.gpt_config)
        
        # Model metadata
        self.model_name = config.get('model_name', 'demo-llm')
        self.version = config.get('version', '1.0.0')
        
    def forward(self, input_ids, attention_mask=None, labels=None):
        """Forward pass through the model"""
        return self.transformer(
            input_ids=input_ids,
            attention_mask=attention_mask,
            labels=labels
        )
    
    def generate(
        self, 
        input_ids: torch.Tensor, 
        max_length: int = 100,
        temperature: float = 0.7,
        top_p: float = 0.9,
        do_sample: bool = True,
        pad_token_id: int = None
    ) -> torch.Tensor:
        """Generate text from input"""
        return self.transformer.generate(
            input_ids=input_ids,
            max_length=max_length,
            temperature=temperature,
            top_p=top_p,
            do_sample=do_sample,
            pad_token_id=pad_token_id,
            eos_token_id=pad_token_id
        )
    
    def get_model_info(self) -> Dict:
        """Get model information for registry"""
        return {
            "model_name": self.model_name,
            "version": self.version,
            "architecture": "GPT-2 Based",
            "parameters": sum(p.numel() for p in self.parameters()),
            "config": {
                "vocab_size": self.gpt_config.vocab_size,
                "hidden_size": self.gpt_config.n_embd,
                "num_layers": self.gpt_config.n_layer,
                "num_heads": self.gpt_config.n_head,
                "max_length": self.gpt_config.n_positions
            }
        }


class DemoLLMWrapper:
    """
    Wrapper class for the demo LLM with MLOps integration
    """
    
    def __init__(self, model_path: Optional[str] = None, config_path: Optional[str] = None):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # Load configuration
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                self.config = json.load(f)
        else:
            self.config = self._get_default_config()
        
        # Initialize tokenizer
        self.tokenizer = GPT2Tokenizer.from_pretrained('gpt2')
        self.tokenizer.pad_token = self.tokenizer.eos_token
        
        # Initialize model
        self.model = SimpleLLM(self.config)
        
        # Load pretrained weights if path provided
        if model_path and os.path.exists(model_path):
            self.load_model(model_path)
        
        self.model.to(self.device)
        self.model.eval()
        
        logger.info(f"Demo LLM initialized with {self.model.get_model_info()['parameters']:,} parameters")
    
    def _get_default_config(self) -> Dict:
        """Get default configuration for demo model"""
        return {
            "model_name": "demo-llm",
            "version": "1.0.0",
            "vocab_size": 50257,
            "max_length": 512,
            "hidden_size": 384,
            "num_layers": 6,
            "num_heads": 6,
            "dropout": 0.1,
            "learning_rate": 5e-5,
            "batch_size": 4,
            "max_epochs": 3
        }
    
    def preprocess(self, text: str) -> Dict[str, torch.Tensor]:
        """Preprocess input text"""
        encoding = self.tokenizer(
            text,
            return_tensors='pt',
            max_length=self.config['max_length'],
            truncation=True,
            padding=True
        )
        return {k: v.to(self.device) for k, v in encoding.items()}
    
    def predict(self, text: str, max_length: int = 100, **kwargs) -> str:
        """Generate text prediction"""
        inputs = self.preprocess(text)
        
        with torch.no_grad():
            outputs = self.model.generate(
                inputs['input_ids'],
                max_length=max_length,
                **kwargs
            )
        
        generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        return generated_text
    
    def batch_predict(self, texts: List[str], **kwargs) -> List[str]:
        """Generate predictions for batch of texts"""
        results = []
        for text in texts:
            result = self.predict(text, **kwargs)
            results.append(result)
        return results
    
    def save_model(self, save_path: str):
        """Save model state"""
        os.makedirs(save_path, exist_ok=True)
        
        # Save model weights
        torch.save(self.model.state_dict(), os.path.join(save_path, 'model.pt'))
        
        # Save configuration
        with open(os.path.join(save_path, 'config.json'), 'w') as f:
            json.dump(self.config, f, indent=2)
        
        # Save tokenizer
        self.tokenizer.save_pretrained(save_path)
        
        # Save model info
        model_info = self.model.get_model_info()
        with open(os.path.join(save_path, 'model_info.json'), 'w') as f:
            json.dump(model_info, f, indent=2)
        
        logger.info(f"Model saved to {save_path}")
    
    def load_model(self, model_path: str):
        """Load model state"""
        if os.path.exists(os.path.join(model_path, 'model.pt')):
            state_dict = torch.load(os.path.join(model_path, 'model.pt'), map_location=self.device)
            self.model.load_state_dict(state_dict)
            logger.info(f"Model loaded from {model_path}")
        else:
            logger.warning(f"No model weights found at {model_path}")
    
    def get_model_metrics(self) -> Dict:
        """Get model performance metrics"""
        return {
            "model_name": self.config['model_name'],
            "version": self.config['version'],
            "parameters": self.model.get_model_info()['parameters'],
            "device": str(self.device),
            "memory_usage": torch.cuda.memory_allocated() if torch.cuda.is_available() else 0
        }


def create_demo_model(config: Optional[Dict] = None) -> DemoLLMWrapper:
    """Factory function to create demo model"""
    if config is None:
        config = {}
    
    model = DemoLLMWrapper()
    model.config.update(config)
    
    return model


if __name__ == "__main__":
    # Quick test
    model = create_demo_model()
    
    test_text = "The future of machine learning is"
    result = model.predict(test_text, max_length=50)
    
    print(f"Input: {test_text}")
    print(f"Output: {result}")
    print(f"Model Info: {model.get_model_metrics()}")