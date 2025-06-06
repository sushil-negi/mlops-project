"""
Health check endpoints
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
import time
import logging
from typing import Dict, Any

from core.database import check_db_connection
from core.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()


class HealthResponse(BaseModel):
    """Health check response model"""
    status: str
    timestamp: float
    version: str
    service: str
    checks: Dict[str, Any]


@router.get("/", response_model=HealthResponse)
async def health_check():
    """Basic health check endpoint"""
    
    # Check database connection
    db_healthy = await check_db_connection()
    
    # TODO: Add Redis health check
    # TODO: Add storage health check
    
    checks = {
        "database": {
            "status": "healthy" if db_healthy else "unhealthy",
            "checked_at": time.time()
        }
    }
    
    # Determine overall status
    overall_status = "healthy" if all(
        check["status"] == "healthy" for check in checks.values()
    ) else "unhealthy"
    
    return HealthResponse(
        status=overall_status,
        timestamp=time.time(),
        version="1.0.0",
        service="model-registry",
        checks=checks
    )


@router.get("/live")
async def liveness_check():
    """Kubernetes liveness probe endpoint"""
    return {"status": "alive", "timestamp": time.time()}


@router.get("/ready")
async def readiness_check():
    """Kubernetes readiness probe endpoint"""
    
    # Check if service is ready to handle requests
    db_healthy = await check_db_connection()
    
    if not db_healthy:
        return {"status": "not_ready", "reason": "database_unavailable"}
    
    return {"status": "ready", "timestamp": time.time()}