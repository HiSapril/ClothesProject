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
import os

# Create Tables (Simple implementation, use Alembic for production)
Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.PROJECT_NAME)

# Mount static for images
from fastapi.responses import FileResponse

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")
app.mount("/processed", StaticFiles(directory=settings.PROCESSED_DIR), name="processed")

app.include_router(endpoints.router, prefix="/api/v1")

@app.get("/")
def read_root():
    return FileResponse("app/static/index.html")

@app.get("/login")
def login_page():
    return FileResponse("app/static/login.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
 
 
 
  
   
    
     
      
