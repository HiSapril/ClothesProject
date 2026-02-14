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
from app.core.config import settings
from app.core.auth import get_password_hash, verify_password, create_access_token, get_current_user
from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter()

@router.get("/version")
async def get_version():
    return {"version": "1.1.0", "status": "Multiple Outfits Fix Active"}

@router.post("/auth/register")
async def register(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    # Check if user exists
    user = db.query(models.User).filter(
        (models.User.username == user_in.username) | (models.User.email == user_in.email)
    ).first()
    if user:
        raise HTTPException(status_code=400, detail="Username or email already registered")
    
    db_user = models.User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password)
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return {"message": "User created successfully"}

@router.post("/auth/login", response_model=schemas.Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not user.hashed_password or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/users/me", response_model=schemas.UserResponse)
async def read_user_me(current_user: models.User = Depends(get_current_user)):
    return current_user

@router.put("/users/me/profile")
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

@router.get("/users/me/profile")
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

@router.get("/items/me", response_model=List[schemas.ClothingItemResponse])
def get_my_items(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    items = db.query(models.ClothingItem).filter(models.ClothingItem.user_id == current_user.id).order_by(models.ClothingItem.created_at.desc()).all()
    
    # Map to schema
    res = []
    for item in items:
        res.append(schemas.ClothingItemResponse(
            id=item.id,
            category_label=item.category_label,
            main_color_hex=item.main_color_hex,
            type=item.type,
            occasion=item.occasion,
            image_url=f"/uploads/{os.path.basename(item.original_image_path)}",
            processed_image_url=f"/processed/{os.path.basename(item.processed_image_path)}",
            created_at=item.created_at
        ))
    return res

@router.get("/items/user/{user_id}", response_model=List[schemas.ClothingItemResponse])
def get_user_items(user_id: int, db: Session = Depends(get_db)):
    items = db.query(models.ClothingItem).filter(models.ClothingItem.user_id == user_id).order_by(models.ClothingItem.created_at.desc()).all()
    
    # Map to schema
    res = []
    for item in items:
        res.append(schemas.ClothingItemResponse(
            id=item.id,
            category_label=item.category_label,
            main_color_hex=item.main_color_hex,
            type=item.type,
            occasion=item.occasion,
            image_url=f"/uploads/{os.path.basename(item.original_image_path)}",
            processed_image_url=f"/processed/{os.path.basename(item.processed_image_path)}",
            created_at=item.created_at
        ))
    return res

@router.get("/weather")
def get_weather(lat: float, lon: float):
    return weather_service.get_current_weather(lat, lon)

@router.post("/items/upload", response_model=schemas.ClothingItemResponse)
async def upload_clothing_item(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    1. Save uploaded file
    2. Process with AI (BG remove, classify)
    3. Save processed file
    4. Save to DB
    """
    # 1. Save original
    file_ext = file.filename.split(".")[-1]
    filename = f"{uuid.uuid4()}.{file_ext}"
    file_path = os.path.join(settings.UPLOAD_DIR, filename)
    
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
        
    # 2. AI Processing
    try:
        ai_result = analyze_image(content)
    except Exception as e:
        print(f"AI Error: {e}")
        raise HTTPException(status_code=500, detail=f"AI processing failed: {str(e)}")
    
    # 3. Save processed
    processed_filename = f"proc_{filename}.png" # It returns PNG
    processed_path = os.path.join(settings.PROCESSED_DIR, processed_filename)
    
    with open(processed_path, "wb") as buffer:
        buffer.write(ai_result["processed_image"])
        
    # Determine Type/Occasion from Category (Simple Heuristic for demo)
    # In real app, user might verify/edit this
    cat_raw = ai_result["category_raw"].lower()
    c_type = models.ClothingTypeEnum.TOP
    occasion = models.OccasionEnum.CASUAL
    
    # Translation & Simple Heuristic
    # Default to a safe generic label if no specific match is found later
    label_vi = "Hàng khác" 
    
    if "jean" in cat_raw:
        c_type = models.ClothingTypeEnum.BOTTOM
        label_vi = "Quần"
    elif "skirt" in cat_raw:
        c_type = models.ClothingTypeEnum.BOTTOM
        label_vi = "Váy"
    elif "pant" in cat_raw or "trouser" in cat_raw or "short" in cat_raw:
        c_type = models.ClothingTypeEnum.BOTTOM
        label_vi = "Quần"
    # Jewelry & Accessories (more specific)
    elif any(kw in cat_raw for kw in ["watch", "stopwatch", "clock", "chronometer", "timer"]):
        c_type = models.ClothingTypeEnum.WATCH
        label_vi = "Đồng hồ"
    elif any(kw in cat_raw for kw in ["bracelet", "bangle", "wrist", "armlet", "bead", "jewelry", "trinket", "pendant", "chain"]):
        c_type = models.ClothingTypeEnum.BRACELET
        label_vi = "Vòng tay"
    elif any(kw in cat_raw for kw in ["sunglass", "spectacle", "goggle"]) or (("glass" in cat_raw) and not any(kw in cat_raw for kw in ["hour", "bead", "bracelet"])):
        c_type = models.ClothingTypeEnum.EYEWEAR
        label_vi = "Mắt kính"
    # Footwear (Dép before Giày)
    elif any(kw in cat_raw for kw in ["slipper", "slide", "flip-flop", "sandal", "thong"]):
        c_type = models.ClothingTypeEnum.SLIPPER
        label_vi = "Dép"
    elif any(kw in cat_raw for kw in ["shoe", "boot", "sneaker", "clog", "loafer", "footwear"]):
        c_type = models.ClothingTypeEnum.SHOES
        label_vi = "Giày"
    # Upper body
    elif any(kw in cat_raw for kw in ["jacket", "coat", "parka", "outerwear", "windbreaker", "overcoat", "cardigan", "sweatshirt", "hoodie"]):
        c_type = models.ClothingTypeEnum.OUTERWEAR
        label_vi = "Áo khoác"
    elif any(kw in cat_raw for kw in ["jersey", "t-shirt", "top", "shirt", "sweater", "blouse", "polo"]):
        c_type = models.ClothingTypeEnum.TOP
        label_vi = "Áo"
    # Dresses & Suits
    elif "dress" in cat_raw or "gown" in cat_raw or "robe" in cat_raw or "kimono" in cat_raw:
        c_type = models.ClothingTypeEnum.FULL
        label_vi = "Váy"
    elif "suit" in cat_raw:
        c_type = models.ClothingTypeEnum.FULL
        occasion = models.OccasionEnum.FORMAL
        label_vi = "Bộ Đồ"
    else:
        # Final fallback - if it's very small or recognized as jewelry but not caught above
        if any(kw in cat_raw for kw in ["jewelry", "pin", "ornament"]):
             c_type = models.ClothingTypeEnum.BRACELET # Vòng tay is a safe guess for generic jewelry
             label_vi = "Vòng tay"
        else:
             # Default back to a specific accessory type but one that is less common to hit by accident
             c_type = models.ClothingTypeEnum.EYEWEAR
             label_vi = "Mắt kính"
        
    # 4. Save to DB
    db_item = models.ClothingItem(
        user_id=current_user.id,
        original_image_path=file_path,
        processed_image_path=processed_path,
        category_label=label_vi,
        category_raw=cat_raw, # cat_raw is the variable containing ImageNet label
        main_color_hex=ai_result["color_hex"],
        type=c_type,
        occasion=occasion
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    
    # Map to schema (converting paths to URLs if we had a static mount)
    return schemas.ClothingItemResponse(
        id=db_item.id,
        category_label=db_item.category_label,
        main_color_hex=db_item.main_color_hex,
        type=db_item.type,
        occasion=db_item.occasion,
        image_url=f"/uploads/{filename}",
        processed_image_url=f"/processed/{processed_filename}",
        created_at=db_item.created_at
    )

@router.post("/recommend", response_model=schemas.RecommendationResponse)
def get_recommendations(
    req: schemas.RecommendationRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Use actual logged-in user ID
    user_id = current_user.id
    # 1. Context
    weather = weather_service.get_current_weather(req.lat, req.lon)
    
    # Determine occasion based on priority: selected_event_id > force_occasion > current calendar event
    if req.selected_event_id and current_user.google_token:
        # User selected a specific event
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
        # Try to get current event from calendar
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
        
    # 2. Recommend
    outfits_data = recommendation_engine.recommend(db, user_id, weather, occasion)
    
    # 3. Format Response
    outfits_pydantic = []
    for outfit in outfits_data:
        items_pydantic = []
        for item in outfit["items"]:
             items_pydantic.append(schemas.ClothingItemResponse(
                id=item.id,
                category_label=item.category_label,
                main_color_hex=item.main_color_hex,
                type=item.type,
                occasion=item.occasion,
                image_url=f"/uploads/{os.path.basename(item.original_image_path)}",
                processed_image_url=f"/processed/{os.path.basename(item.processed_image_path)}",
                created_at=item.created_at
             ))
             
        outfits_pydantic.append(schemas.OutfitResponse(
            items=items_pydantic,
            score=outfit["score"],
            reason=outfit.get("reason")
        ))
        
    return schemas.RecommendationResponse(
        outfits=outfits_pydantic,
        weather_summary=f"{weather['temp']}°C, {weather['condition']}",
        occasion_context=event_context
    )

@router.delete("/items/{item_id}")
def delete_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(models.ClothingItem).filter(models.ClothingItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Delete physical files using absolute paths
    for path_attr in ["original_image_path", "processed_image_path"]:
        rel_path = getattr(item, path_attr)
        if rel_path:
            abs_path = os.path.abspath(rel_path)
            try:
                if os.path.exists(abs_path):
                    os.remove(abs_path)
                    print(f"Successfully deleted: {abs_path}")
                else:
                    print(f"File not found for deletion: {abs_path}")
            except Exception as e:
                print(f"Error deleting file {abs_path}: {e}")

    db.delete(item)
    db.commit()
    return {"message": "Món đồ đã được xóa thành công"}

@router.delete("/items/all")
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

# --- Google Calendar OAuth Endpoints ---

@router.get("/calendar/login")
async def calendar_login():
    """Initial Google Login/Connect redirect"""
    redirect_uri = "http://localhost:8000/api/v1/calendar/callback"
    flow = calendar_service.get_calendar_flow(redirect_uri)
    if not flow:
         raise HTTPException(status_code=400, detail="Thiếu file credentials.json. Vui lòng tải file từ Google Console và đặt vào thư mục dự án.")
    
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'
    )
    return RedirectResponse(authorization_url)

@router.get("/calendar/callback")
async def calendar_callback(code: str, db: Session = Depends(get_db)):
    """Handle callback from Google: Sign in user AND save token to DB"""
    try:
        redirect_uri = "http://localhost:8000/api/v1/calendar/callback"
        flow = calendar_service.get_calendar_flow(redirect_uri)
        print(f"DEBUG: Fetching token with code: {code[:10]}...")
        flow.fetch_token(code=code)
        
        creds = flow.credentials
        print("DEBUG: Token fetched successfully.")
        token_json = creds.to_json()
        
        # Get profile info
        user_info = calendar_service.get_user_info(creds)
        print(f"DEBUG: User info: {user_info}")
        email = user_info.get('email')
        if not email:
            raise HTTPException(status_code=400, detail="Google không trả về Email.")
            
        username = email.split('@')[0]
        
        # Find or create user
        user = db.query(models.User).filter(models.User.email == email).first()
        if not user:
            # Check for username collision
            existing_user = db.query(models.User).filter(models.User.username == username).first()
            if existing_user:
                username = f"{username}_{uuid.uuid4().hex[:4]}"
                
            user = models.User(
                username=username,
                email=email,
                gender=user_info.get('gender')
            )
            db.add(user)
        
        # Always update token on entry
        user.google_token = token_json
        print(f"DEBUG: Updating token for user {user.username}")
        db.commit()
        db.refresh(user)
        print("DEBUG: User updated and committed.")
        
        access_token = create_access_token(data={"sub": user.username})
        
        from fastapi.responses import HTMLResponse
        content = f"""
        <html>
        <body style="background: #0F111A; color: white; display: flex; align-items: center; justify-content: center; height: 100vh; font-family: sans-serif;">
            <div style="text-align: center;">
                <h2>Đang hoàn tất đăng nhập...</h2>
                <script>
                    localStorage.setItem('token', '{access_token}');
                    window.location.href = '/';
                </script>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(content=content)
    except Exception as e:
        print(f"CALLBACK ERROR: {e}")
        raise HTTPException(status_code=500, detail=f"Lỗi xử lý đăng nhập: {str(e)}")

@router.get("/calendar/events")
async def get_calendar_events(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get upcoming events using token from database"""
    if not current_user.google_token:
        return {"connected": False, "events": []}
        
    events, new_token = calendar_service.get_upcoming_events_summary(current_user.google_token)
    
    # If token was refreshed, update DB
    if new_token:
        current_user.google_token = new_token
        db.commit()
        
    return {
        "connected": True,
        "events": events
    }

@router.get("/calendar/status")
async def calendar_status(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Check status and current event using DB token"""
    if not current_user.google_token:
        return {"connected": False, "event_info": None}
        
    event_info, new_token = calendar_service.get_current_occasion_from_calendar(current_user.google_token)
    
    if new_token:
        current_user.google_token = new_token
        db.commit()
        
    return {
        "connected": True,
        "event_info": event_info
    }

@router.get("/calendar/refresh")
async def calendar_refresh(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return await get_calendar_events(current_user, db)

@router.get("/calendar/events/month")
async def get_month_events(
    month: int, 
    year: int, 
    current_user: models.User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """Fetch events for a specific month view"""
    if not current_user.google_token:
        return {"connected": False, "events": []}
    
    start_time = datetime(year, month, 1)
    if month == 12:
        end_time = datetime(year + 1, 1, 1)
    else:
        end_time = datetime(year, month + 1, 1)
        
    events, new_token = calendar_service.get_events_for_range(current_user.google_token, start_time, end_time)
    
    if new_token:
        current_user.google_token = new_token
        db.commit()
    
    return {"connected": True, "events": events}

@router.get("/calendar/events/day", response_model=schemas.DayEventsResponse)
async def get_day_events(
    year: int,
    month: int,
    day: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Fetch all events for a specific day
    Returns formatted events with occasion mapping
    """
    if not current_user.google_token:
        raise HTTPException(status_code=400, detail="Calendar not connected")
    
    try:
        target_date = datetime(year, month, day).date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date")
    
    events, new_token = calendar_service.get_events_for_day(current_user.google_token, target_date)
    
    if new_token:
        current_user.google_token = new_token
        db.commit()
    
    # Format response
    day_events = []
    for event in events:
        day_events.append(schemas.DayEventItem(
            id=event['id'],
            summary=event['summary'],
            start_time=event['start_time'],
            end_time=event['end_time'],
            occasion=event['occasion'],
            description=event.get('description', '')
        ))
    
    return schemas.DayEventsResponse(
        date=target_date.isoformat(),
        events=day_events
    )

@router.post("/recommend/with-event", response_model=schemas.RecommendationResponse)
async def get_event_recommendation(
    req: schemas.EventRecommendationRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Generate outfit recommendations based on a specific selected event
    """
    if not current_user.google_token:
        raise HTTPException(status_code=400, detail="Calendar not connected")
    
    # Get event details
    event_info, new_token = calendar_service.get_event_by_id(current_user.google_token, req.event_id)
    
    if new_token:
        current_user.google_token = new_token
        db.commit()
    
    if not event_info:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Get weather
    weather = weather_service.get_current_weather(req.lat, req.lon)
    
    # Get recommendations based on event occasion
    occasion = event_info['occasion']
    outfits_data = recommendation_engine.recommend(db, req.user_id, weather, occasion)
    
    # Format response
    outfits_pydantic = []
    for outfit in outfits_data:
        items_pydantic = []
        for item in outfit["items"]:
            items_pydantic.append(schemas.ClothingItemResponse(
                id=item.id,
                category_label=item.category_label,
                main_color_hex=item.main_color_hex,
                type=item.type,
                occasion=item.occasion,
                image_url=f"/uploads/{os.path.basename(item.original_image_path)}",
                processed_image_url=f"/processed/{os.path.basename(item.processed_image_path)}",
                created_at=item.created_at
            ))
        
        outfits_pydantic.append(schemas.OutfitResponse(
            items=items_pydantic,
            score=outfit["score"],
            reason=outfit.get("reason")
        ))
    
    return schemas.RecommendationResponse(
        outfits=outfits_pydantic,
        weather_summary=f"{weather['temp']}°C, {weather['condition']}",
        occasion_context=f"Sự kiện: {event_info['summary']}"
    )


@router.post("/calendar/events", response_model=schemas.CalendarEventResponse)
async def create_calendar_event(
    event_in: schemas.CalendarEventCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.google_token:
        raise HTTPException(status_code=400, detail="Calendar not connected")
        
    event, new_token = calendar_service.create_event(current_user.google_token, event_in.dict())
    
    if new_token:
        current_user.google_token = new_token
        db.commit()
        
    return {
        "id": event['id'],
        "summary": event.get('summary', ''),
        "location": event.get('location', ''),
        "description": event.get('description', ''),
        "start_time": event['start'].get('dateTime', event['start'].get('date', '')),
        "end_time": event['end'].get('dateTime', event['end'].get('date', ''))
    }

@router.put("/calendar/events/{event_id}", response_model=schemas.CalendarEventResponse)
async def update_calendar_event(
    event_id: str,
    event_in: schemas.CalendarEventCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.google_token:
        raise HTTPException(status_code=400, detail="Calendar not connected")
        
    event, new_token = calendar_service.update_event(current_user.google_token, event_id, event_in.dict())
    
    if new_token:
        current_user.google_token = new_token
        db.commit()
        
    return {
        "id": event['id'],
        "summary": event.get('summary', ''),
        "location": event.get('location', ''),
        "description": event.get('description', ''),
        "start_time": event['start'].get('dateTime', event['start'].get('date', '')),
        "end_time": event['end'].get('dateTime', event['end'].get('date', ''))
    }

@router.delete("/calendar/events/{event_id}")
async def delete_calendar_event(
    event_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.google_token:
        raise HTTPException(status_code=400, detail="Calendar not connected")
        
    success, new_token = calendar_service.delete_event(current_user.google_token, event_id)
    
    if new_token:
        current_user.google_token = new_token
        db.commit()
        
    return {"message": "Event deleted successfully"}

