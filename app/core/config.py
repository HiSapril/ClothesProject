import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Personal Outfit Recommender"
    # Update this with your real postgres credentials
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/clothes_db"
    
    # File Storage
    UPLOAD_DIR: str = "uploads"
    PROCESSED_DIR: str = "processed_uploads"
    
    # External APIs
    OPENWEATHER_API_KEY: str = "63d0ab7d3f6e447eb0d113454261201" # Add your key
    
    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()

# Ensure directories exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.PROCESSED_DIR, exist_ok=True)
