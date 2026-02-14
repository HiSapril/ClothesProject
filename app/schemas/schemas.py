from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from app.db.models import ClothingTypeEnum, OccasionEnum

# --- Clothing Schemas ---
class ClothingItemBase(BaseModel):
    category_label: Optional[str] = None
    main_color_hex: Optional[str] = None
    type: Optional[ClothingTypeEnum] = None
    occasion: Optional[OccasionEnum] = OccasionEnum.CASUAL

class ClothingItemCreate(ClothingItemBase):
    pass 

class ClothingItemResponse(ClothingItemBase):
    id: int
    image_url: str
    processed_image_url: str
    created_at: datetime

    class Config:
        from_attributes = True

# --- User & Auth Schemas ---
class UserBase(BaseModel):
    username: str
    email: str

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    gender: Optional[str] = None
    age: Optional[int] = None
    height: Optional[int] = None
    weight: Optional[int] = None
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class UserUpdate(BaseModel):
    gender: Optional[str] = None
    age: Optional[int] = None
    height: Optional[int] = None
    weight: Optional[int] = None

# --- Recommendation Schemas ---
class RecommendationRequest(BaseModel):
    lat: float
    lon: float
    user_id: Optional[int] = None
    force_occasion: Optional[OccasionEnum] = None 
    event_titles: Optional[List[str]] = []
    selected_event_id: Optional[str] = None  # Google Calendar event ID

class OutfitResponse(BaseModel):
    items: List[ClothingItemResponse]
    score: int
    reason: Optional[str] = None

class RecommendationResponse(BaseModel):
    outfits: List[OutfitResponse]
    weather_summary: str
    occasion_context: str
# --- Calendar Schemas ---
class CalendarEventBase(BaseModel):
    summary: str
    location: Optional[str] = None
    description: Optional[str] = None
    start_time: str # ISO format string
    end_time: str # ISO format string

class CalendarEventCreate(CalendarEventBase):
    pass

class CalendarEventResponse(CalendarEventBase):
    id: str

# --- Event Selection Schemas ---
class DayEventItem(BaseModel):
    """Represents a single event on a specific day"""
    id: str
    summary: str
    start_time: str
    end_time: str
    occasion: OccasionEnum
    description: Optional[str] = None

class DayEventsResponse(BaseModel):
    """Response containing all events for a specific day"""
    date: str  # YYYY-MM-DD format
    events: List[DayEventItem]
    
class EventRecommendationRequest(BaseModel):
    """Request for outfit recommendations based on a specific event"""
    lat: float
    lon: float
    user_id: Optional[int] = None
    event_id: str  # Google Calendar event ID
