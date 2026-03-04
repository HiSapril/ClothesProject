from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict, Any
import logging

from app.db.database import get_db
from app.db import models
from app.api.deps import get_current_user, RoleChecker
from app.core.cache import cache
from app.core.celery_app import celery_app
from celery.result import AsyncResult
from app.schemas import schemas
import datetime
import os

router = APIRouter()
logger = logging.getLogger("app")

@router.get("/health", response_model=Dict[str, Any])
def health_check(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    is_admin=Depends(RoleChecker([models.UserRole.ADMIN]))
):
    """
    Deep health check verifying DB and Redis/Worker connectivity.
    """
    health_status = {
        "status": "healthy",
        "database": "connected",
        "redis": "connected",
        "worker": "offline"
    }
    
    # 1. Check DB
    try:
         db.execute("SELECT 1")
    except Exception as e:
        health_status["database"] = f"error: {str(e)}"
        health_status["status"] = "degraded"

    # 2. Check Redis/Worker
    try:
        ping = celery_app.control.ping(timeout=0.5)
        if ping:
            health_status["worker"] = "online"
        
        # Simple cache check
        cache_test = cache.get("health_ping")
        if cache_test is None:
            cache.set("health_ping", "pong", ttl=10)
    except Exception as e:
        health_status["redis"] = f"error: {str(e)}"
        health_status["status"] = "degraded"

    return health_status

@router.get("/metrics", response_model=Dict[str, Any])
def get_metrics(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    is_admin=Depends(RoleChecker([models.UserRole.ADMIN]))
):
    """
    Basic system metrics for administrative observability.
    """
    try:
        total_users = db.query(models.User).count()
        total_items = db.query(models.ClothingItem).count()
        items_by_status = db.query(models.ClothingItem.status, func.count(models.ClothingItem.id)).group_by(models.ClothingItem.status).all()
        
        return {
            "total_users": total_users,
            "total_items": total_items,
            "items_by_status": dict(items_by_status),
            "cache_enabled": True # Config check could be added here
        }
    except Exception as e:
        logger.error(f"Failed to fetch metrics: {e}")
        raise HTTPException(status_code=500, detail="Could not retrieve system metrics")

@router.get("/tasks/{task_id}", response_model=Dict[str, Any])
def inspect_task(
    task_id: str,
    current_user: models.User = Depends(get_current_user),
    is_admin=Depends(RoleChecker([models.UserRole.ADMIN]))
):
    """
    Safe inspection of background job states for admins.
    """
    task_result = AsyncResult(task_id, app=celery_app)
    return {
        "task_id": task_id,
        "status": task_result.status,
        "ready": task_result.ready(),
        "failed": task_result.failed()
    }

@router.get("/readiness", response_model=schemas.ReadinessResponse, tags=["Operations"])
def readiness_check(db: Session = Depends(get_db)):
    """
    Lightweight readiness check for orchestration (K8s/Docker).
    No authentication required as it doesn't expose sensitive data.
    """
    status = "READY"
    db_ok = "OK"
    redis_ok = "OK"
    worker_ok = "OK"

    try:
        db.execute("SELECT 1")
    except:
        db_ok = "DOWN"
        status = "DEGRADED"

    try:
        ping = celery_app.control.ping(timeout=0.2)
        if not ping:
            worker_ok = "DOWN"
            status = "DEGRADED"
        
        # Redis check via cache
        if not cache.get("readiness_ping"):
            cache.set("readiness_ping", "1", ttl=5)
    except:
        redis_ok = "DOWN"
        status = "DEGRADED"

    return {
        "status": status,
        "database": db_ok,
        "redis": redis_ok,
        "worker": worker_ok
    }

@router.get("/version", response_model=schemas.VersionResponse, tags=["Operations"])
def get_version():
    """
    Expose build information for debugging and audit.
    """
    return {
        "service_name": "Outfit AI Backend",
        "api_version": "1.2.2",
        "git_commit": os.getenv("GIT_COMMIT", "unknown"),
        "build_time": datetime.datetime.now().isoformat()
    }
