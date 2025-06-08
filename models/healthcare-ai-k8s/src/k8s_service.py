"""
Kubernetes-optimized Healthcare AI Service
FastAPI-based service with monitoring, health checks, and production features
"""

import os
import json
import time
import logging
from datetime import datetime
from typing import Dict, Optional
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import redis
from fastapi.responses import Response

# Import healthcare AI engine from main model directory
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent / "healthcare-ai" / "src"))
from healthcare_ai_engine import HealthcareAIEngine

# Prometheus metrics - create new registry to avoid conflicts
from prometheus_client import CollectorRegistry, Counter, Histogram, Gauge, generate_latest
custom_registry = CollectorRegistry()

request_count = Counter('healthcare_ai_requests_total', 'Total requests', ['method', 'endpoint'], registry=custom_registry)
request_duration = Histogram('healthcare_ai_request_duration_seconds', 'Request duration', registry=custom_registry)
model_predictions = Counter('healthcare_ai_predictions_total', 'Total predictions', ['category', 'method'], registry=custom_registry)
active_connections = Gauge('healthcare_ai_active_connections', 'Active connections', registry=custom_registry)
model_accuracy = Gauge('healthcare_ai_model_accuracy', 'Current model accuracy', registry=custom_registry)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="Healthcare AI Service",
    description="Production Healthcare AI with MLOps integration",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response models
class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    category: str
    confidence: float
    method: str
    generation_time: float
    model_version: str
    timestamp: str

class HealthResponse(BaseModel):
    status: str
    service: str
    model_loaded: bool
    redis_connected: bool
    uptime_seconds: float
    version: str

# Global variables
healthcare_engine = None
redis_client = None
start_time = time.time()

def initialize_services():
    """Initialize healthcare AI engine and Redis connection"""
    global healthcare_engine, redis_client
    
    try:
        # Initialize healthcare AI engine
        logger.info("Initializing Healthcare AI Engine...")
        healthcare_engine = HealthcareAIEngine()
        
        # Initialize Redis (optional, for caching)
        try:
            redis_client = redis.Redis(
                host=os.getenv('REDIS_HOST', 'localhost'),
                port=int(os.getenv('REDIS_PORT', 6379)),
                decode_responses=True,
                socket_timeout=5
            )
            redis_client.ping()
            logger.info("Redis connection established")
        except Exception as e:
            logger.warning(f"Redis not available: {e}")
            redis_client = None
        
        logger.info("Healthcare AI Service initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    initialize_services()

@app.middleware("http")
async def add_process_time_header(request, call_next):
    """Add request timing and monitoring"""
    start_time = time.time()
    
    # Update active connections
    active_connections.inc()
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Update metrics
        request_count.labels(method=request.method, endpoint=request.url.path).inc()
        request_duration.observe(process_time)
        
        response.headers["X-Process-Time"] = str(process_time)
        return response
    
    finally:
        active_connections.dec()

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Kubernetes health check endpoint"""
    uptime = time.time() - start_time
    
    redis_status = False
    if redis_client:
        try:
            redis_client.ping()
            redis_status = True
        except:
            redis_status = False
    
    return HealthResponse(
        status="healthy",
        service="healthcare-ai",
        model_loaded=healthcare_engine is not None,
        redis_connected=redis_status,
        uptime_seconds=uptime,
        version="2.0.0"
    )

@app.get("/ready")
async def readiness_check():
    """Kubernetes readiness check"""
    if healthcare_engine is None:
        raise HTTPException(status_code=503, detail="Healthcare AI engine not ready")
    
    return {"status": "ready", "service": "healthcare-ai"}

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(custom_registry), media_type="text/plain")

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Main chat endpoint with monitoring"""
    if healthcare_engine is None:
        raise HTTPException(status_code=503, detail="Healthcare AI engine not initialized")
    
    start_time = time.time()
    
    try:
        # Check cache first (if Redis available)
        cache_key = None
        if redis_client:
            cache_key = f"chat:{hash(request.message.lower())}"
            try:
                cached_response = redis_client.get(cache_key)
                if cached_response:
                    logger.info("Returning cached response")
                    return ChatResponse.parse_raw(cached_response)
            except Exception as e:
                logger.warning(f"Cache read error: {e}")
        
        # Generate response
        response_data = healthcare_engine.generate_response(request.message)
        
        generation_time = time.time() - start_time
        
        # Create response object
        chat_response = ChatResponse(
            response=response_data['response'],
            category=response_data.get('category', 'general'),
            confidence=response_data.get('confidence', 0.0),
            method=response_data.get('method', 'unknown'),
            generation_time=generation_time,
            model_version="2.0.0",
            timestamp=datetime.now().isoformat()
        )
        
        # Update metrics
        model_predictions.labels(
            category=chat_response.category,
            method=chat_response.method
        ).inc()
        
        # Cache response (if Redis available)
        if redis_client and cache_key:
            try:
                redis_client.setex(
                    cache_key, 
                    3600,  # 1 hour cache
                    chat_response.json()
                )
            except Exception as e:
                logger.warning(f"Cache write error: {e}")
        
        # Log request for monitoring
        logger.info(f"Chat request processed: {chat_response.category} in {generation_time:.3f}s")
        
        return chat_response
        
    except Exception as e:
        logger.error(f"Chat processing error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/stats")
async def get_stats():
    """Get service statistics"""
    if healthcare_engine is None:
        raise HTTPException(status_code=503, detail="Healthcare AI engine not ready")
    
    uptime = time.time() - start_time
    
    # Get engine stats if available
    engine_stats = {}
    if hasattr(healthcare_engine, 'get_statistics'):
        engine_stats = healthcare_engine.get_statistics()
    
    return {
        "service": "healthcare-ai",
        "version": "2.0.0",
        "uptime_seconds": uptime,
        "model_loaded": True,
        "redis_connected": redis_client is not None,
        "engine_stats": engine_stats,
        "environment": os.getenv("ENVIRONMENT", "development")
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Healthcare AI",
        "version": "2.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health",
        "metrics": "/metrics"
    }

if __name__ == "__main__":
    # Configuration
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8080))
    workers = int(os.getenv("WORKERS", 1))
    log_level = os.getenv("LOG_LEVEL", "info")
    
    logger.info(f"Starting Healthcare AI Service on {host}:{port}")
    
    # Run with uvicorn
    uvicorn.run(
        "k8s_service:app",
        host=host,
        port=port,
        workers=workers,
        log_level=log_level,
        access_log=True
    )