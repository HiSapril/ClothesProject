from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import shutil
import os
import uuid

from app.db.database import get_db
from app.db import models
from app.schemas import schemas
from app.services.ai_service import analyze_image
from app.services.weather_service import weather_service
from app.services.calendar_service import calendar_service
from app.services.recommendation_engine import recommendation_engine
from app.services.tasks import process_clothing_ai
from app.core.celery_app import celery_app
from celery.result import AsyncResult
from app.core.config import settings
from app.api.deps import get_current_user, RoleChecker
try:
    from fastapi_limiter.depends import RateLimiter
except (ImportError, TypeError):
    # Fallback for environments with conflicting redis/aioredis dependencies
    def RateLimiter(*args, **kwargs):
        async def dummy_limiter():
            return True
        return dummy_limiter

from app.core.security import get_password_hash, verify_password, create_access_token
from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter()

@router.get("/version", tags=["Utility"])
async def get_version():
    return {"version": "1.2.0", "status": "Frontend Readiness Active"}

@router.get("/users/me", response_model=schemas.UserResponse, tags=["User"])
async def read_user_me(current_user: models.User = Depends(get_current_user)):
    return current_user

@router.put("/users/me/profile", response_model=schemas.MessageResponse, tags=["User"])
async def update_profile(
    profile: schemas.UserUpdate, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    """Update user profile stats"""
    user = current_user
    if profile.gender is not None: user.gender = profile.gender
    if profile.age is not None: user.age = profile.age
    if profile.height is not None: user.height = profile.height
    if profile.weight is not None: user.weight = profile.weight
    
    db.commit()
    return {"message": "Cập nhật hồ sơ thành công"}

@router.get("/users/me/profile", response_model=schemas.ProfileResponse, tags=["User"])
async def get_profile(current_user: models.User = Depends(get_current_user)):
    user = current_user
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "gender": user.gender,
        "age": user.age,
        "height": user.height,
        "weight": user.weight
    }

@router.get("/items/me", response_model=List[schemas.ClothingItemResponse], tags=["Clothing"])
def get_my_items(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    items = db.query(models.ClothingItem).filter(models.ClothingItem.user_id == current_user.id).order_by(models.ClothingItem.created_at.desc()).all()
    
    res = []
    for item in items:
        res.append(schemas.ClothingItemResponse(
            id=item.id,
            category_label=item.category_label,
            main_color_hex=item.main_color_hex,
            category=item.category,
            confidence_score=item.confidence_score,
            classification_status=item.classification_status,
            occasion=item.occasion,
            status=item.status,
            task_id=item.task_id,
            image_url=f"/uploads/{os.path.basename(item.original_image_path)}",
            processed_image_url=f"/processed/{os.path.basename(item.processed_image_path)}" if item.processed_image_path else None,
            created_at=item.created_at
        ))
    return res

@router.get("/items/user/{user_id}", response_model=List[schemas.ClothingItemResponse], tags=["Clothing"])
def get_user_items(user_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(RoleChecker([models.UserRole.ADMIN]))):
    items = db.query(models.ClothingItem).filter(models.ClothingItem.user_id == user_id).order_by(models.ClothingItem.created_at.desc()).all()
    
    res = []
    for item in items:
        res.append(schemas.ClothingItemResponse(
            id=item.id,
            category_label=item.category_label,
            main_color_hex=item.main_color_hex,
            category=item.category,
            confidence_score=item.confidence_score,
            classification_status=item.classification_status,
            occasion=item.occasion,
            status=item.status,
            task_id=item.task_id,
            image_url=f"/uploads/{os.path.basename(item.original_image_path)}",
            processed_image_url=f"/processed/{os.path.basename(item.processed_image_path)}" if item.processed_image_path else None,
            created_at=item.created_at
        ))
    return res

@router.get("/weather", response_model=schemas.WeatherResponse, tags=["Weather"])
def get_weather(lat: float, lon: float):
    return weather_service.get_current_weather(lat, lon)

@router.post("/items/upload", response_model=schemas.AsyncUploadResponse, tags=["Clothing"], dependencies=[Depends(RateLimiter(times=5, seconds=60))])
async def upload_clothing_item(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    1. Save uploaded file
    2. Create pending DB record (with SHA256 hash)
    3. Offload AI processing to Celery
    4. Return task_id and item_id
    """
    # 1. Save original
    file_ext = file.filename.split(".")[-1]
    filename = f"{uuid.uuid4()}.{file_ext}"
    file_path = os.path.join(settings.UPLOAD_DIR, filename)
    
    content = await file.read()
    import hashlib
    image_hash = hashlib.sha256(content).hexdigest()
    
    with open(file_path, "wb") as buffer:
        buffer.write(content)
        
    # 2. Check for Idempotency
    existing_item = db.query(models.ClothingItem).filter(
        models.ClothingItem.image_hash == image_hash,
        models.ClothingItem.user_id == current_user.id
    ).first()
    if existing_item:
        from app.core.logging_config import setup_logging
        logger = setup_logging()
        logger.info(f"Idempotent upload detected for user {current_user.id}, hash {image_hash}")
        return schemas.AsyncUploadResponse(
            item_id=existing_item.id,
            task_id=existing_item.task_id or "ALREADY_PROCESSED",
            status=existing_item.status
        )

    # 3. Save to DB (Pending -> QUEUED)
    db_item = models.ClothingItem(
        original_image_path=file_path,
        user_id=current_user.id,
        image_hash=image_hash,
        status="QUEUED"
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    
    # 3. Offload to Celery
    from app.core.logging_config import request_id_ctx
    rid = request_id_ctx.get()
    
    image_hex = content.hex()
    task = process_clothing_ai.delay(db_item.id, image_hex, request_id=rid)
    
    # Update item with task_id
    db_item.task_id = task.id
    db.commit()
    
    return schemas.AsyncUploadResponse(
        item_id=db_item.id,
        task_id=task.id,
        status="QUEUED"
    )

@router.get("/items/task/{task_id}", response_model=schemas.TaskStatusResponse, tags=["AI"])
async def get_task_status(task_id: str, db: Session = Depends(get_db)):
    """Check status of an AI processing job with detailed failure info"""
    task_result = AsyncResult(task_id, app=celery_app)
    
    # Sync with DB for persistent failure info
    db_item = db.query(models.ClothingItem).filter(models.ClothingItem.task_id == task_id).first()
    
    status = task_result.status
    failure_reason = None
    retryable = False
    result = None

    if task_result.ready():
        if task_result.failed():
            status = "FAILURE"
            failure_reason = str(task_result.result)
            retryable = True # System errors are usually retryable
        else:
            result = {"result": task_result.result}
            
    # Overlay DB info if available (more specific logic)
    if db_item:
        if db_item.status == "FAILED":
            status = "FAILURE"
            failure_reason = db_item.failure_reason or failure_reason
            # Domain errors like "No clothing found" are NOT retryable
            if failure_reason and "No clothing found" in failure_reason:
                retryable = False
            else:
                retryable = True

    return schemas.TaskStatusResponse(
        task_id=task_id,
        status=status,
        result=result,
        failure_reason=failure_reason,
        retryable=retryable
    )

@router.post("/recommend", response_model=schemas.RecommendationResponse, tags=["Recommendation"], dependencies=[Depends(RateLimiter(times=10, seconds=60))])
def get_recommendations(
    req: schemas.RecommendationRequest, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    user_id = current_user.id
    weather = weather_service.get_current_weather(req.lat, req.lon)
    
    if req.selected_event_id and current_user.google_token:
        event_info, new_token = calendar_service.get_event_by_id(current_user.google_token, req.selected_event_id)
        if new_token:
            current_user.google_token = new_token
            db.commit()
        
        if event_info:
            occasion = event_info['occasion']
            event_context = f"{event_info['summary']}"
        else:
            occasion = models.OccasionEnum.CASUAL
            event_context = "Thường ngày"
    elif req.force_occasion:
        occasion = req.force_occasion
        event_context = {
            "casual": "Đi chơi / Thường ngày",
            "formal": "Trang trọng / Sự kiện",
            "sport": "Thể thao"
        }.get(occasion.value, occasion.value)
    else:
        if current_user.google_token:
            cal_info, new_token = calendar_service.get_current_occasion_from_calendar(current_user.google_token)
            if new_token:
                current_user.google_token = new_token
                db.commit()
            
            if cal_info:
                occasion = cal_info["occasion"]
                event_context = cal_info["summary"]
            else:
                occasion = models.OccasionEnum.CASUAL
                event_context = "Thường ngày"
        else:
            occasion = models.OccasionEnum.CASUAL
            event_context = "Thường ngày"
        
    outfits_data = recommendation_engine.recommend(
        db, user_id, weather, occasion, 
        strategy=req.strategy, 
        decision_layer_enabled=req.decision_layer_enabled,
        context_override=req.context_override
    )
    
    outfits_pydantic = []
    for outfit in outfits_data:
        items_pydantic = []
        for item in outfit["items"]:
             items_pydantic.append(schemas.ClothingItemResponse(
                id=item.id,
                category_label=item.category_label,
                main_color_hex=item.main_color_hex,
                category=item.category,
                confidence_score=item.confidence_score,
                classification_status=item.classification_status,
                occasion=item.occasion,
                status=item.status,
                task_id=item.task_id,
                image_url=f"/uploads/{os.path.basename(item.original_image_path or '')}",
                processed_image_url=f"/processed/{os.path.basename(item.processed_image_path)}" if item.processed_image_path else None,
                created_at=item.created_at
             ))
             
        outfits_pydantic.append(schemas.OutfitResponse(
            items=items_pydantic,
            score=outfit["score"],
            reason=outfit.get("reason"),
            decision_status=outfit.get("decision_status", "CONFIRMED")
        ))
        
    return schemas.RecommendationResponse(
        outfits=outfits_pydantic,
        weather_summary=f"{weather['temp']}°C, {weather['condition']}",
        occasion_context=event_context,
        strategy_used=req.strategy,
        decision_layer_status=req.decision_layer_enabled
    )

@router.delete("/items/{item_id}", response_model=schemas.MessageResponse, tags=["Clothing"])
def delete_item(item_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    item = db.query(models.ClothingItem).filter(models.ClothingItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    for path_attr in ["original_image_path", "processed_image_path"]:
        rel_path = getattr(item, path_attr)
        if rel_path:
            abs_path = os.path.abspath(rel_path)
            try:
                if os.path.exists(abs_path):
                    os.remove(abs_path)
            except Exception as e:
                print(f"Error deleting file {abs_path}: {e}")

    db.delete(item)
    db.commit()
    return {"message": "Món đồ đã được xóa thành công"}

@router.delete("/items/all", response_model=schemas.MessageResponse, tags=["Clothing"])
def delete_all_items(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    user_id = current_user.id
    items = db.query(models.ClothingItem).filter(models.ClothingItem.user_id == user_id).all()
    
    for item in items:
        for path_attr in ["original_image_path", "processed_image_path"]:
            rel_path = getattr(item, path_attr)
            if rel_path:
                abs_path = os.path.abspath(rel_path)
                try:
                    if os.path.exists(abs_path):
                        os.remove(abs_path)
                except: pass
        db.delete(item)
    
    db.commit()
    return {"message": "Đã dọn dẹp toàn bộ tủ đồ cá nhân"}

@router.get("/calendar/login", tags=["Calendar"])
async def calendar_login():
    redirect_uri = "http://localhost:8000/api/v1/calendar/callback"
    flow = calendar_service.get_calendar_flow(redirect_uri)
    if not flow:
         raise HTTPException(status_code=400, detail="Thiếu file credentials.json.")
    
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'
    )
    return RedirectResponse(authorization_url)

@router.get("/calendar/callback", tags=["Calendar"])
async def calendar_callback(code: str, db: Session = Depends(get_db)):
    try:
        redirect_uri = "http://localhost:8000/api/v1/calendar/callback"
        flow = calendar_service.get_calendar_flow(redirect_uri)
        flow.fetch_token(code=code)
        creds = flow.credentials
        token_json = creds.to_json()
        user_info = calendar_service.get_user_info(creds)
        email = user_info.get('email')
        if not email:
            raise HTTPException(status_code=400, detail="Google không trả về Email.")
        username = email.split('@')[0]
        user = db.query(models.User).filter(models.User.email == email).first()
        if not user:
            user = models.User(username=username, email=email)
            db.add(user)
        user.google_token = token_json
        db.commit()
        db.refresh(user)
        access_token = create_access_token(data={"sub": user.username})
        from fastapi.responses import HTMLResponse
        content = f"<html><body><script>localStorage.setItem('token', '{access_token}'); window.location.href='/';</script></body></html>"
        return HTMLResponse(content=content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi: {str(e)}")

@router.get("/calendar/events", tags=["Calendar"])
async def get_calendar_events(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.google_token:
        return {"connected": False, "events": []}
    events, new_token = calendar_service.get_upcoming_events_summary(current_user.google_token)
    if new_token:
        current_user.google_token = new_token
        db.commit()
    return {"connected": True, "events": events}

@router.get("/admin/users", response_model=List[schemas.UserResponse], dependencies=[Depends(RoleChecker([models.UserRole.ADMIN]))])
def list_all_users(db: Session = Depends(get_db)):
    return db.query(models.User).all()
