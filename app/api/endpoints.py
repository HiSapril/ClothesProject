from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Form, BackgroundTasks
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, date as py_date
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
from app.core.logging_config import setup_logging, request_id_ctx

logger = setup_logging()
import logging
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
logging.getLogger("uvicorn.error").setLevel(logging.WARNING)
logging.getLogger("app").setLevel(logging.INFO)
try:
    from fastapi_limiter.depends import RateLimiter as RealRateLimiter
    
    def RateLimiter(*args, **kwargs):
        """Safe wrapper for RateLimiter that fails silent if Redis/Limiter is not initialized"""
        real_limiter = RealRateLimiter(*args, **kwargs)
        async def safe_limiter(request = None, response = None):
            try:
                return await real_limiter(request, response)
            except Exception as e:
                # If Redis is down or Limiter not init, just allow the request
                logger.debug(f"RateLimiter fallback triggered: {e}")
                return True
        return safe_limiter
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
    return {"version": "1.3.10", "status": "Scientific Insights & UI Polish"}

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
    background_tasks: BackgroundTasks,
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
    rid = request_id_ctx.get()
    
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
    
    # 3. Offload to Native BackgroundTasks
    # No more Celery/Redis dependency for robustness
    image_hex = content.hex()
    background_tasks.add_task(process_clothing_ai, db_item.id, image_hex, request_id=rid)
    
    db_item.task_id = f"bg_{db_item.id}_{uuid.uuid4().hex[:8]}"
    db.commit()
    
    return schemas.AsyncUploadResponse(
        item_id=db_item.id,
        task_id=db_item.task_id,
        status="QUEUED"
    )

@router.get("/items/task/{task_id}", response_model=schemas.TaskStatusResponse, tags=["AI"])
async def get_task_status(task_id: str, db: Session = Depends(get_db)):
    if task_id == "SYNC_PROCESSED":
        # Handle cases where processing was done synchronously.
        # We need to find the item and check its status in DB.
        db_item = db.query(models.ClothingItem).filter(
            (models.ClothingItem.task_id == "SYNC_PROCESSED") | 
            (models.ClothingItem.status.in_(["COMPLETED", "FAILED"]))
        ).order_by(models.ClothingItem.created_at.desc()).first()
        
        status = "SUCCESS" if db_item and db_item.status == "COMPLETED" else "PENDING"
        if db_item and db_item.status == "FAILED": status = "FAILURE"
        
        return schemas.TaskStatusResponse(
            task_id=task_id,
            status=status,
            result=None,
            failure_reason=db_item.failure_reason if db_item else None,
            retryable=True
        )

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
    
    # If version says 1.2.x, user might have ghost processes.
    # Logic is now ultra-permissive for the minimalist UI.
    actual_strategy = schemas.RecommendationStrategy.CONTEXT_AWARE
    if str(req.strategy).upper() == "BASELINE":
        actual_strategy = schemas.RecommendationStrategy.BASELINE

    weather = weather_service.get_current_weather(req.lat, req.lon)
    real_event_name = None  # Only set when an actual calendar event is selected

    if req.selected_event_id and current_user.google_token:
        event_info, new_token = calendar_service.get_event_by_id(current_user.google_token, req.selected_event_id)
        if new_token:
            current_user.google_token = new_token
            db.commit()

        if event_info:
            occasion = event_info['occasion']
            event_context = f"{event_info['summary']}"
            real_event_name = event_info['summary']  # e.g. "Hop team", "Di gym"
        else:
            occasion = models.OccasionEnum.CASUAL
            event_context = "Thuong ngay"
    elif req.force_occasion:
        occasion = req.force_occasion
        event_context = {
            "casual": "Thuong ngay",
            "formal": "Trang trong",
            "sport": "The thao"
        }.get(occasion.value, occasion.value)
        # real_event_name stays None - user picked occasion manually, not a specific event
    else:
        if current_user.google_token:
            cal_info, new_token = calendar_service.get_current_occasion_from_calendar(current_user.google_token)
            if new_token:
                current_user.google_token = new_token
                db.commit()

            if cal_info:
                occasion = cal_info["occasion"]
                event_context = cal_info["summary"]
                real_event_name = cal_info["summary"]  # Auto-detected event
            else:
                occasion = models.OccasionEnum.CASUAL
                event_context = "Thuong ngay"
        else:
            occasion = models.OccasionEnum.CASUAL
            event_context = "Thuong ngay"

    outfits_data = recommendation_engine.recommend(
        db, user_id, weather, occasion,
        strategy=actual_strategy,
        decision_layer_enabled=req.decision_layer_enabled,
        context_override=req.context_override,
        event_name=real_event_name  # None when no real calendar event selected
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
             
        # Score from algorithm: max possible score is exactly 100 points.
        suitability_pct = min(100, max(0, round(outfit["score"])))
        
        outfits_pydantic.append(schemas.OutfitResponse(
            items=items_pydantic,
            score=outfit["score"],
            suitability_pct=suitability_pct,
            breakdown=outfit.get("explanations", []),
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
        access_token = create_access_token(subject=user.id, role=user.role.value)
        from fastapi.responses import HTMLResponse
        content = f"<html><body><script>localStorage.setItem('access_token', '{access_token}'); window.location.href='/';</script></body></html>"
        return HTMLResponse(content=content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi: {str(e)}")

@router.get("/calendar/events", tags=["Calendar"])
async def get_upcoming_events(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Fetch upcoming events summary"""
    if not current_user.google_token:
        return {"connected": False, "events": []}
    
    try:
        events, new_token = calendar_service.get_upcoming_events_summary(current_user.google_token)
        if new_token:
            current_user.google_token = new_token
            db.commit()
        return {"connected": True, "events": events}
    except Exception as e:
        logger.error(f"Error fetching upcoming events: {e}")
        raise HTTPException(status_code=500, detail="Không thể tải danh sách sự kiện")


@router.get("/calendar/events/daily", tags=["Calendar"])
async def get_daily_events(date: str, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Fetch events for a specific day (YYYY-MM-DD)"""
    if not current_user.google_token:
        return {"events": []}
    
    try:
        target_date = py_date.fromisoformat(date) if isinstance(date, str) else date
        events, new_token = calendar_service.get_events_for_day(current_user.google_token, target_date)
        if new_token:
            current_user.google_token = new_token
            db.commit()
        return {"date": date, "events": events}
    except ValueError:
        raise HTTPException(status_code=400, detail="Định dạng ngày không hợp lệ (YYYY-MM-DD)")

@router.get("/calendar/events/month", tags=["Calendar"])
async def get_monthly_events(year: int, month: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Fetch all events for a specific month"""
    if not current_user.google_token:
        return {"events": []}
    
    try:
        events, new_token = calendar_service.get_events_for_month(current_user.google_token, year, month)
        if new_token:
            current_user.google_token = new_token
            db.commit()
        return {"year": year, "month": month, "events": events}
    except Exception as e:
        logger.error(f"Error fetching monthly events: {e}")
        raise HTTPException(status_code=500, detail="Không thể tải lịch tháng")

@router.get("/calendar/events/{event_id}", tags=["Calendar"])
async def get_calendar_event(event_id: str, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.google_token:
        raise HTTPException(status_code=400, detail="Chưa kết nối Google Calendar")
    
    event, new_token = calendar_service.get_event_by_id(current_user.google_token, event_id)
    if new_token:
        current_user.google_token = new_token
        db.commit()
    
    if not event:
        raise HTTPException(status_code=404, detail="Sự kiện không tồn tại")
    return event


@router.post("/calendar/events", tags=["Calendar"])
async def create_calendar_event(event: schemas.CalendarEventBase, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.google_token:
        raise HTTPException(status_code=400, detail="Chưa kết nối Google Calendar")
    
    event_dict = event.model_dump()
    created, new_token = calendar_service.create_event(current_user.google_token, event_dict)
    if new_token:
        current_user.google_token = new_token
        db.commit()
    return created

@router.put("/calendar/events/{event_id}", tags=["Calendar"])
async def update_calendar_event(event_id: str, event: schemas.CalendarEventBase, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.google_token:
        raise HTTPException(status_code=400, detail="Chưa kết nối Google Calendar")
    
    event_dict = event.model_dump()
    updated, new_token = calendar_service.update_event(current_user.google_token, event_id, event_dict)
    if new_token:
        current_user.google_token = new_token
        db.commit()
    return updated


@router.delete("/calendar/events/{event_id}", tags=["Calendar"])
async def delete_calendar_event(event_id: str, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.google_token:
        raise HTTPException(status_code=400, detail="Chưa kết nối Google Calendar")
    
    success, new_token = calendar_service.delete_event(current_user.google_token, event_id)
    if new_token:
        current_user.google_token = new_token
        db.commit()
    return {"success": success}

# --- Item Management Enhancements ---

@router.patch("/items/{item_id}", response_model=schemas.ClothingItemResponse, tags=["Clothing"])
async def update_item(item_id: int, update_data: schemas.ClothingItemBase, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    item = db.query(models.ClothingItem).filter(models.ClothingItem.id == item_id, models.ClothingItem.user_id == current_user.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Không tìm thấy món đồ")
    
    for key, value in update_data.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    
    # Update type if category changed
    from app.db.models import ClothingTypeEnum
    type_map = {
        "TOP": ClothingTypeEnum.TOP,
        "BOTTOM": ClothingTypeEnum.BOTTOM,
        "FOOTWEAR": ClothingTypeEnum.SHOES,
        "OUTERWEAR": ClothingTypeEnum.OUTERWEAR,
        "FULL_BODY": ClothingTypeEnum.FULL
    }
    if item.category:
        item.type = type_map.get(item.category.name, item.type)

    db.commit()
    db.refresh(item)
    return item

@router.get("/admin/users", response_model=List[schemas.UserResponse], dependencies=[Depends(RoleChecker([models.UserRole.ADMIN]))])
def list_all_users(db: Session = Depends(get_db)):
    return db.query(models.User).all()
