"""
Health Check Route

Provides health and status endpoints for the API.
"""

import os
import logging
from typing import Optional
from datetime import datetime

from fastapi import APIRouter
from pydantic import BaseModel, Field

from rag import get_qdrant_service

logger = logging.getLogger(__name__)

router = APIRouter()


class DependencyHealth(BaseModel):
    """Health status of a dependency."""
    
    name: str
    status: str  # "healthy", "unhealthy", "unknown"
    message: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response."""
    
    status: str = Field(..., description="Overall health status")
    version: str = Field(..., description="API version")
    timestamp: str = Field(..., description="Current server timestamp")
    dependencies: list[DependencyHealth] = Field(
        default_factory=list,
        description="Health status of dependencies"
    )


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Check the health of the API and its dependencies.
    
    Returns:
        HealthResponse with overall status and dependency health
    """
    dependencies = []
    overall_healthy = True
    
    # Check Qdrant
    qdrant_health = await _check_qdrant()
    dependencies.append(qdrant_health)
    if qdrant_health.status != "healthy":
        overall_healthy = False
    
    # Check LiveKit credentials
    livekit_health = _check_livekit_config()
    dependencies.append(livekit_health)
    if livekit_health.status != "healthy":
        overall_healthy = False
    
    # Check Google API key
    google_health = _check_google_config()
    dependencies.append(google_health)
    if google_health.status != "healthy":
        overall_healthy = False
    
    return HealthResponse(
        status="healthy" if overall_healthy else "degraded",
        version="0.1.0",
        timestamp=datetime.utcnow().isoformat() + "Z",
        dependencies=dependencies
    )


@router.get("/health/live")
async def liveness():
    """
    Kubernetes-style liveness probe.
    Returns 200 if the service is running.
    """
    return {"status": "alive"}


@router.get("/health/ready")
async def readiness():
    """
    Kubernetes-style readiness probe.
    Returns 200 if the service is ready to accept traffic.
    """
    # Check critical dependencies
    qdrant_health = await _check_qdrant()
    
    if qdrant_health.status == "healthy":
        return {"status": "ready"}
    else:
        return {"status": "not_ready", "reason": qdrant_health.message}


async def _check_qdrant() -> DependencyHealth:
    """Check Qdrant connection health."""
    try:
        qdrant = get_qdrant_service()
        info = await qdrant.get_collection_info()
        
        if info:
            return DependencyHealth(
                name="qdrant",
                status="healthy",
                message=f"Collection '{info['name']}' with {info['points_count']} points"
            )
        else:
            return DependencyHealth(
                name="qdrant",
                status="unhealthy",
                message="Collection not found - run ingestion script"
            )
            
    except Exception as e:
        logger.warning(f"Qdrant health check failed: {e}")
        return DependencyHealth(
            name="qdrant",
            status="unhealthy",
            message=str(e)
        )


def _check_livekit_config() -> DependencyHealth:
    """Check LiveKit configuration."""
    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")
    livekit_url = os.getenv("LIVEKIT_URL")
    
    if api_key and api_secret and livekit_url:
        return DependencyHealth(
            name="livekit",
            status="healthy",
            message="Credentials configured"
        )
    else:
        missing = []
        if not api_key:
            missing.append("LIVEKIT_API_KEY")
        if not api_secret:
            missing.append("LIVEKIT_API_SECRET")
        if not livekit_url:
            missing.append("LIVEKIT_URL")
        
        return DependencyHealth(
            name="livekit",
            status="unhealthy",
            message=f"Missing: {', '.join(missing)}"
        )


def _check_google_config() -> DependencyHealth:
    """Check Google API configuration."""
    api_key = os.getenv("GOOGLE_API_KEY")
    
    if api_key:
        return DependencyHealth(
            name="google_ai",
            status="healthy",
            message="API key configured"
        )
    else:
        return DependencyHealth(
            name="google_ai",
            status="unhealthy",
            message="GOOGLE_API_KEY not set"
        )
