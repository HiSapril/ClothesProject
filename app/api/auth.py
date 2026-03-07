from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
import logging

from app.db.database import get_db
from app.db import models
from app.core import security
from app.core.config import settings
from app.schemas import schemas

router = APIRouter()
logger = logging.getLogger("app")
# Trigger uvicorn reload


@router.post("/register", response_model=schemas.UserResponse)
def register_user(
    user_in: schemas.UserCreate, 
    db: Session = Depends(get_db)
):
    """
    POST /auth/register
    Create a new user.
    """
    # Check if user exists
    user = db.query(models.User).filter(
        (models.User.username == user_in.username) | (models.User.email == user_in.email)
    ).first()
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered"
        )
    
    db_user = models.User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=security.get_password_hash(user_in.password),
        role=models.UserRole.USER # Default role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    logger.info(f"New user registered: {db_user.username}")
    return db_user

@router.post("/login", response_model=schemas.Token)
def login_for_access_token(
    db: Session = Depends(get_db), 
    form_data: OAuth2PasswordRequestForm = Depends()
):
    """
    POST /auth/login
    Issue Access and Refresh tokens.
    """
    # 1. Authenticate User
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not user.hashed_password or not security.verify_password(form_data.password, user.hashed_password):
        logger.warning(f"Failed login attempt for user: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 2. Create Tokens
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        subject=user.id, 
        role=user.role.value, 
        expires_delta=access_token_expires
    )
    
    refresh_token = security.create_refresh_token(subject=user.id)
    
    # 3. Store Refresh Token Hash for revocation
    user.refresh_token_hash = security.get_password_hash(refresh_token)
    db.commit()
    
    logger.info(f"User {user.username} logged in successfully")
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": refresh_token
    }

@router.post("/demo/guest", response_model=schemas.Token)
def guest_login(db: Session = Depends(get_db)):
    """
    Public guest login for demo environments.
    Only available if DEMO_MODE is enabled.
    """
    if not settings.DEMO_MODE:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Demo mode is disabled"
        )
    
    guest_username = "guest_visitor"
    user = db.query(models.User).filter(models.User.username == guest_username).first()
    
    if not user:
        user = models.User(
            username=guest_username,
            email="guest@outfit.ai",
            role=models.UserRole.USER, # Full features for demo
            hashed_password=None # Passwordless
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    # Issue short-lived guest tokens
    access_token = security.create_access_token(
        subject=user.id, 
        role=user.role.value,
        expires_delta=timedelta(hours=2)
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": "guest_no_refresh"
    }

@router.post("/refresh", response_model=schemas.Token)
def refresh_access_token(
    refresh_token: str,
    db: Session = Depends(get_db)
):
    """
    POST /auth/refresh
    Rotate access tokens using a valid refresh token.
    """
    try:
        from jose import jwt
        payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        if token_type != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
            
    except Exception:
        raise HTTPException(status_code=401, detail="Could not validate refresh token")
    
    user = db.query(models.User).filter(models.User.id == int(user_id)).first()
    if not user or not user.refresh_token_hash or not security.verify_password(refresh_token, user.refresh_token_hash):
        raise HTTPException(status_code=401, detail="Refresh token revoked or invalid")
    
    # Create new access token
    access_token = security.create_access_token(subject=user.id, role=user.role.value)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": refresh_token # Keep same refresh token or rotate if desired
    }

@router.post("/logout")
def logout(
    user_id: int, # This should ideally come from current_user dependency
    db: Session = Depends(get_db)
):
    """
    POST /auth/logout
    Revoke refresh token.
    """
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user:
        user.refresh_token_hash = None
        db.commit()
    return {"message": "Successfully logged out"}
