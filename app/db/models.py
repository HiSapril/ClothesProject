from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SqEnum, JSON, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base
import enum
from app.domain.fashion_taxonomy import FashionCategory, ClassificationStatus

class OccasionEnum(str, enum.Enum):
    CASUAL = "casual"
    FORMAL = "formal"
    SPORT = "sport"

class UserRole(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"

class ClothingTypeEnum(str, enum.Enum):
    TOP = "top" # Shirt, T-shirt
    BOTTOM = "bottom" # Jeans, Shorts
    SHOES = "shoes"
    OUTERWEAR = "outerwear" # Jacket, Coat
    FULL = "full" # Dress, Jumpsuit
    SLIPPER = "slipper" # Slides, Sandals
    EYEWEAR = "eyewear"
    BRACELET = "bracelet"
    WATCH = "watch"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String, nullable=True) # Nullable for Google-only users
    role = Column(SqEnum(UserRole), default=UserRole.USER)
    refresh_token_hash = Column(String, nullable=True) # For revocation
    google_token = Column(String, nullable=True) # Stores OAuth token JSON string
    
    # Profile Stats
    gender = Column(String, nullable=True) # "Nam", "Nữ", "Khác"
    age = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True) # cm
    weight = Column(Integer, nullable=True) # kg
    
    items = relationship("ClothingItem", back_populates="owner")
    logs = relationship("OutfitLog", back_populates="user")

class ClothingItem(Base):
    __tablename__ = "clothing_items"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # Paths
    original_image_path = Column(String)
    processed_image_path = Column(String) # Bg removed
    
    # AI Extracted Features
    category_label = Column(String) # e.g. "Mắt kính"
    category_raw = Column(String, nullable=True) # e.g. "sunglass"
    main_color_hex = Column(String) # e.g. "#00FF00"
    image_hash = Column(String, index=True, nullable=True) # SHA256 for deduplication
    
    # Classification for Logic
    category = Column(SqEnum(FashionCategory), default=FashionCategory.UNKNOWN)
    confidence_score = Column(Float, nullable=True)
    classification_status = Column(SqEnum(ClassificationStatus), default=ClassificationStatus.UNKNOWN)
    raw_model_output = Column(JSON, nullable=True) # Full output for auditing
    
    type = Column(SqEnum(ClothingTypeEnum), nullable=True) # Legacy, keeping for compatibility
    occasion = Column(SqEnum(OccasionEnum), default=OccasionEnum.CASUAL)
    
    # Task Tracking
    status = Column(String, default="pending") # pending, processing, completed, failed
    task_id = Column(String, nullable=True) # Celery task ID
    failure_reason = Column(String, nullable=True)
    failure_code = Column(String, nullable=True)   # Typed failure (e.g. LOW_CONFIDENCE)
    suggested_action = Column(String, nullable=True) # Actionable help for user
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    owner = relationship("User", back_populates="items")

class OutfitLog(Base):
    __tablename__ = "outfit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # Storing IDs of items worn
    items_ids = Column(JSON) # e.g. [1, 5, 20]
    
    worn_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="logs")
