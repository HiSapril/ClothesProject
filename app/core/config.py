import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Personal Outfit Recommender"
    DEBUG: bool = False
    ENV_MODE: str = "development" # development | production
    DEMO_MODE: bool = False       # If True, enables guest login & specific banners
    
    # CORS
    CORS_ORIGINS: list[str] = ["*"] # Change to specific domains in production
    # Update this with your real postgres credentials
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/clothes_db"
    
    # File Storage
    UPLOAD_DIR: str = "uploads"
    PROCESSED_DIR: str = "processed_uploads"
    
    # Security
    SECRET_KEY: str = "supersecretkey_change_me_in_production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Redis for Rate Limiting & Caching
    REDIS_URL: str = "redis://localhost:6379/0"
    ENABLE_CACHING: bool = True
    
    # External APIs
    OPENWEATHER_API_KEY: str = "your_openweather_api_key_here"
    
    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    
    model_config = SettingsConfigDict(case_sensitive=True, env_file=".env", extra="ignore")

settings = Settings()

# --- Settings Validation ---
def validate_settings():
    if not settings.OPENWEATHER_API_KEY or settings.OPENWEATHER_API_KEY == "your_openweather_api_key_here":
        print("WARNING: OPENWEATHER_API_KEY is not set. Weather features will use sample data.")
        
    if settings.ENV_MODE == "production":
        if settings.SECRET_KEY == "supersecretkey_change_me_in_production":
            raise ValueError("CRITICAL: You must provide a custom SECRET_KEY in production environments.")
        if settings.DEBUG:
            print("WARNING: DEBUG is enabled in production mode. This is NOT recommended.")
            
    if settings.DEMO_MODE:
        print("INFO: DEMO_MODE is enabled. Guest features will be available.")

validate_settings()

# Ensure directories exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.PROCESSED_DIR, exist_ok=True)
