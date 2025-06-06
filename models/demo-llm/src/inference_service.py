"""
Inference Service for Demo LLM Model
FastAPI-based service for model serving
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import asyncio
import logging
import time
import os
import json
from pathlib import Path
import uvicorn

from model import DemoLLMWrapper

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Request/Response models
class GenerationRequest(BaseModel):
    """Request model for text generation"""
    text: str = Field(..., description="Input text to continue", max_length=1000)
    max_length: int = Field(default=100, description="Maximum length of generated text", ge=1, le=500)
    temperature: float = Field(default=0.7, description="Sampling temperature", ge=0.1, le=2.0)
    top_p: float = Field(default=0.9, description="Top-p sampling parameter", ge=0.1, le=1.0)
    num_return_sequences: int = Field(default=1, description="Number of sequences to generate", ge=1, le=5)
    
    class Config:
        schema_extra = {
            "example": {
                "text": "The future of machine learning is",
                "max_length": 100,
                "temperature": 0.7,
                "top_p": 0.9,
                "num_return_sequences": 1
            }
        }


class GenerationResponse(BaseModel):
    """Response model for text generation"""
    generated_text: List[str] = Field(..., description="Generated text continuations")
    input_text: str = Field(..., description="Original input text")
    generation_time: float = Field(..., description="Time taken for generation in seconds")
    model_info: Dict[str, Any] = Field(..., description="Model information")
    
    class Config:
        schema_extra = {
            "example": {
                "generated_text": ["The future of machine learning is bright with new developments in AI"],
                "input_text": "The future of machine learning is",
                "generation_time": 0.15,
                "model_info": {
                    "model_name": "demo-llm",
                    "version": "1.0.0",
                    "parameters": 124000000
                }
            }
        }


class BatchGenerationRequest(BaseModel):
    """Request model for batch text generation"""
    texts: List[str] = Field(..., description="List of input texts", max_items=10)
    max_length: int = Field(default=100, description="Maximum length of generated text")
    temperature: float = Field(default=0.7, description="Sampling temperature")
    top_p: float = Field(default=0.9, description="Top-p sampling parameter")


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    model_loaded: bool
    timestamp: float
    version: str


class ModelMetrics(BaseModel):
    """Model performance metrics"""
    total_requests: int
    average_response_time: float
    error_rate: float
    uptime: float


# Initialize FastAPI app
app = FastAPI(
    title="Demo LLM Inference Service",
    description="Text generation service using a lightweight demo LLM model",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables
model: Optional[DemoLLMWrapper] = None
model_metrics = {
    "total_requests": 0,
    "total_response_time": 0.0,
    "errors": 0,
    "start_time": time.time()
}


@app.on_event("startup")
async def startup_event():
    """Initialize model on startup"""
    global model
    
    try:
        # Load model
        model_path = os.getenv("MODEL_PATH", None)
        config_path = os.getenv("CONFIG_PATH", None)
        
        logger.info("Loading Demo LLM model...")
        model = DemoLLMWrapper(model_path=model_path, config_path=config_path)
        logger.info("Model loaded successfully")
        
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy" if model is not None else "unhealthy",
        model_loaded=model is not None,
        timestamp=time.time(),
        version="1.0.0"
    )


@app.get("/model/info")
async def get_model_info():
    """Get model information"""
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    return model.get_model_metrics()


@app.get("/metrics", response_model=ModelMetrics)
async def get_metrics():
    """Get service metrics"""
    uptime = time.time() - model_metrics["start_time"]
    avg_response_time = (
        model_metrics["total_response_time"] / model_metrics["total_requests"]
        if model_metrics["total_requests"] > 0 else 0.0
    )
    error_rate = (
        model_metrics["errors"] / model_metrics["total_requests"]
        if model_metrics["total_requests"] > 0 else 0.0
    )
    
    return ModelMetrics(
        total_requests=model_metrics["total_requests"],
        average_response_time=avg_response_time,
        error_rate=error_rate,
        uptime=uptime
    )


@app.post("/generate", response_model=GenerationResponse)
async def generate_text(request: GenerationRequest):
    """Generate text continuation"""
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    start_time = time.time()
    
    try:
        # Update metrics
        model_metrics["total_requests"] += 1
        
        # Generate text
        generated_texts = []
        for _ in range(request.num_return_sequences):
            generated_text = model.predict(
                text=request.text,
                max_length=request.max_length,
                temperature=request.temperature,
                top_p=request.top_p,
                do_sample=True
            )
            generated_texts.append(generated_text)
        
        generation_time = time.time() - start_time
        model_metrics["total_response_time"] += generation_time
        
        # Get model info
        model_info = model.get_model_metrics()
        
        return GenerationResponse(
            generated_text=generated_texts,
            input_text=request.text,
            generation_time=generation_time,
            model_info=model_info
        )
        
    except Exception as e:
        model_metrics["errors"] += 1
        logger.error(f"Generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")


@app.post("/generate/batch")
async def generate_batch(request: BatchGenerationRequest):
    """Generate text for multiple inputs"""
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    start_time = time.time()
    
    try:
        model_metrics["total_requests"] += len(request.texts)
        
        # Generate for each text
        results = []
        for text in request.texts:
            generated_text = model.predict(
                text=text,
                max_length=request.max_length,
                temperature=request.temperature,
                top_p=request.top_p
            )
            results.append({
                "input": text,
                "output": generated_text
            })
        
        generation_time = time.time() - start_time
        model_metrics["total_response_time"] += generation_time
        
        return {
            "results": results,
            "generation_time": generation_time,
            "model_info": model.get_model_metrics()
        }
        
    except Exception as e:
        model_metrics["errors"] += len(request.texts)
        logger.error(f"Batch generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Batch generation failed: {str(e)}")


@app.post("/model/reload")
async def reload_model():
    """Reload the model (useful for model updates)"""
    global model
    
    try:
        model_path = os.getenv("MODEL_PATH", None)
        config_path = os.getenv("CONFIG_PATH", None)
        
        logger.info("Reloading model...")
        model = DemoLLMWrapper(model_path=model_path, config_path=config_path)
        logger.info("Model reloaded successfully")
        
        return {"status": "success", "message": "Model reloaded"}
        
    except Exception as e:
        logger.error(f"Failed to reload model: {e}")
        raise HTTPException(status_code=500, detail=f"Model reload failed: {str(e)}")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Demo LLM Inference Service",
        "version": "1.0.0",
        "status": "running",
        "model_loaded": model is not None,
        "endpoints": {
            "health": "/health",
            "generate": "/generate",
            "batch_generate": "/generate/batch",
            "model_info": "/model/info",
            "metrics": "/metrics",
            "docs": "/docs"
        }
    }


# Background task for logging metrics
async def log_metrics():
    """Background task to log metrics periodically"""
    while True:
        await asyncio.sleep(300)  # Log every 5 minutes
        if model_metrics["total_requests"] > 0:
            logger.info(f"Service metrics: {model_metrics}")


@app.on_event("startup")
async def start_background_tasks():
    """Start background tasks"""
    asyncio.create_task(log_metrics())


if __name__ == "__main__":
    # For development
    uvicorn.run(
        "inference_service:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )