from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.domain.fashion_taxonomy import FashionCategory, ClassificationStatus
from app.db.models import OccasionEnum

# --- Generic Schemas ---
class MessageResponse(BaseModel):
    message: str
    request_id: Optional[str] = None

# --- Clothing Schemas ---
class ClothingItemBase(BaseModel):
    category_label: Optional[str] = None
    main_color_hex: Optional[str] = None
    category: Optional[FashionCategory] = FashionCategory.UNKNOWN
    confidence_score: Optional[float] = None
    classification_status: Optional[ClassificationStatus] = ClassificationStatus.UNKNOWN
    occasion: Optional[OccasionEnum] = OccasionEnum.CASUAL

class ClothingItemCreate(ClothingItemBase):
    pass 

class ClothingItemResponse(ClothingItemBase):
    id: int
    image_url: str
    processed_image_url: Optional[str] = None
    status: str # QUEUED, PROCESSING, COMPLETED, FAILED
    task_id: Optional[str] = None
    failure_reason: Optional[str] = None
    failure_code: Optional[str] = None
    suggested_action: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "category": "TOP",
                "main_color_hex": "#FFFFFF",
                "status": "COMPLETED",
                "image_url": "/uploads/example.png"
            }
        }
    )

class AsyncUploadResponse(BaseModel):
    item_id: int
    task_id: str
    status: str # QUEUED

class TaskStatusResponse(BaseModel):
    task_id: str
    status: str # PENDING, STARTED, SUCCESS, FAILURE
    result: Optional[dict] = None
    failure_reason: Optional[str] = None
    failure_code: Optional[str] = None
    suggested_action: Optional[str] = None
    retryable: bool = False

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
    
    model_config = ConfigDict(from_attributes=True)

class ProfileResponse(UserResponse):
    pass

class Token(BaseModel):
    access_token: str
    token_type: str
    refresh_token: Optional[str] = None

class TokenData(BaseModel):
    username: Optional[str] = None

class UserUpdate(BaseModel):
    gender: Optional[str] = None
    age: Optional[int] = None
    height: Optional[int] = None
    weight: Optional[int] = None

# --- Recommendation & Research Schemas ---
class RecommendationStrategy(str, Enum):
    BASELINE = "BASELINE"
    CONTEXT_AWARE = "CONTEXT_AWARE"

class RecommendationRequest(BaseModel):
    lat: float
    lon: float
    user_id: Optional[int] = None
    force_occasion: Optional[OccasionEnum] = None 
    event_titles: Optional[List[str]] = []
    selected_event_id: Optional[str] = None  # Google Calendar event ID
    
    # Research Parameters
    strategy: RecommendationStrategy = RecommendationStrategy.CONTEXT_AWARE
    decision_layer_enabled: bool = True
    context_override: Optional[Dict[str, Any]] = None # For manual scenario testing

class OutfitResponse(BaseModel):
    items: List[ClothingItemResponse]
    score: int
    reason: Optional[str] = None
    decision_status: Optional[str] = "CONFIRMED" # CONFIRMED, REJECTED, etc.

class RecommendationResponse(BaseModel):
    outfits: List[OutfitResponse]
    weather_summary: str
    occasion_context: str
    
    # Experimental Metadata
    strategy_used: str
    decision_layer_status: bool

# --- Weather Schemas ---
class WeatherResponse(BaseModel):
    temp: float
    condition: str
    city: Optional[str] = None
    humidity: Optional[int] = None
    wind_speed: Optional[float] = None

# --- Meta Schemas ---
class EnumExposureResponse(BaseModel):
    fashion_categories: List[str]
    classification_statuses: List[str]
    occasions: List[str]
    user_roles: List[str]

# --- Calendar Schemas ---
class CalendarEventBase(BaseModel):
    summary: str
    location: Optional[str] = None
    description: Optional[str] = None
    start_time: str # ISO format string
    end_time: str # ISO format string

class CalendarEventResponse(CalendarEventBase):
    id: str

# --- Event Selection Schemas ---
class DayEventItem(BaseModel):
    id: str
    summary: str
    start_time: str
    end_time: str
    occasion: OccasionEnum
    description: Optional[str] = None

class DayEventsResponse(BaseModel):
    date: str  # YYYY-MM-DD format
    events: List[DayEventItem]

# --- Admin Ops Schemas ---
class ReadinessResponse(BaseModel):
    status: str # READY, DEGRADED
    database: str
    redis: str
    worker: str

class VersionResponse(BaseModel):
    service_name: str
    api_version: str
    git_commit: Optional[str] = "unknown"
    build_time: str
