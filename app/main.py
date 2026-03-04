import os
import certifi

# Fix SSL certificate issue globally for AI and Google APIs
os.environ['SSL_CERT_FILE'] = certifi.where()
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.api import endpoints
from app.db.database import engine, Base
from app.core.config import settings
from app.core.logging_config import setup_logging
from app.middleware.logging_middleware import LoggingMiddleware
from app.api.auth import router as auth_router
from app.api.admin_ops import router as admin_router
from app.api.meta import router as meta_router
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse, FileResponse
from fastapi.exceptions import RequestValidationError
from app.core.logging_config import request_id_ctx
import redis.asyncio as redis
from contextlib import asynccontextmanager
try:
    from fastapi_limiter import FastApiLimiter
except (ImportError, TypeError):
    FastApiLimiter = None

# Initialize Logging
logger = setup_logging()

# Create Tables: Managed by Alembic migrations
# Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup ---
    logger.info("Application starting up...")
    
    # Initialize Redis for Rate Limiting
    redis_client = None
    if FastApiLimiter:
        try:
            redis_client = redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
            await FastApiLimiter.init(redis_client)
            logger.info("FastAPI Limiter initialized with Redis")
        except Exception as e:
            logger.warning(f"FastAPI Limiter failed to initialize: {e}")
    else:
        logger.warning("FastAPI Limiter not available due to dependency issues")

    # Optional: Validate DB Connection
    try:
        engine.connect()
        logger.info("Database connection validated")
    except Exception as e:
        logger.critical(f"Database connection FAILED: {e}")

    yield

    # --- Shutdown ---
    logger.info("Application shutting down...")
    if redis_client:
        await redis_client.close()
        logger.info("Redis connection closed gracefully")

app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

# Add Logging Middleware
app.add_middleware(LoggingMiddleware)

# Add CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Global Error Standardization ---

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    # Specialized handling for Rate Limiting (429)
    if exc.status_code == 429:
        retry_after = exc.headers.get("Retry-After", "60")
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            headers={"Retry-After": retry_after},
            content={
                "error_code": "RATE_LIMIT_EXCEEDED",
                "message": f"Too many requests. Please try again after {retry_after} seconds.",
                "request_id": request_id_ctx.get() or "unknown",
                "retry_after": int(retry_after)
            }
        )
        
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error_code": f"HTTP_{exc.status_code}",
            "message": exc.detail,
            "request_id": request_id_ctx.get() or "unknown"
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error_code": "VALIDATION_ERROR",
            "message": str(exc.errors()),
            "request_id": request_id_ctx.get() or "unknown"
        }
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error_code": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred. Please try again later.",
            "request_id": request_id_ctx.get() or "unknown"
        }
    )

# Mount Routers
# Move Auth under v1 for productization
api_v1_router = FastAPI() # Or just include directly in app with prefix
app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(endpoints.router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1/admin", tags=["Admin Operations"])
app.include_router(meta_router, prefix="/api/v1/meta", tags=["Metadata"])

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")
app.mount("/processed", StaticFiles(directory=settings.PROCESSED_DIR), name="processed")

@app.get("/")
def read_root():
    return FileResponse("app/static/index.html")

@app.get("/login")
def login_page():
    return FileResponse("app/static/login.html")

@app.get("/api/v1/meta/config")
def get_public_config():
    """Expose non-sensitive public configuration to frontend"""
    return {
        "env": settings.ENV_MODE,
        "demo_mode": settings.DEMO_MODE,
        "api_version": "1.2.2"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
 
 
 
  
   
    
     
      
