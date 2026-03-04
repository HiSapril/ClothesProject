import pytest
import os
import logging
from app.services.tasks import process_clothing_ai
from app.core.cache import cache
from app.services.weather_service import weather_service
from app.services.recommendation_engine import recommendation_engine
from app.domain.fashion_taxonomy import FashionCategory
from app.db import models

def test_cache_fallback_no_redis(mocker):
    from app.core.cache import Cache
    mocker.patch("app.core.cache.settings.ENABLE_CACHING", False)
    fake_cache = Cache()
    assert fake_cache.get("any_key") is None

def test_weather_cache_hit(mocker):
    # Mock the cache object's get method directly on the INSTANCE
    mock_get = mocker.patch.object(cache, "get", return_value={"temp": 20, "condition": "Sunny", "location": "Test", "description": "Test", "forecast": []})
    mock_api = mocker.patch("requests.get")
    
    result = weather_service.get_current_weather(10.0, 20.0)
    
    assert result["temp"] == 20
    assert mock_get.called
    mock_api.assert_not_called()

def test_ai_deduplication_hit(mocker, db):
    # Ensure items belong to a REAL user and have integer IDs
    user = models.User(username="testuser", email="test@test.com")
    db.add(user)
    db.commit()
    
    existing = models.ClothingItem(user_id=user.id, image_hash="abc", status="COMPLETED", category=FashionCategory.TOP)
    new_item = models.ClothingItem(user_id=user.id, image_hash="abc", status="QUEUED")
    db.add(existing)
    db.add(new_item)
    db.commit()
    
    # Use real IDs from DB
    new_id = new_item.id
    
    mock_analyze = mocker.patch("app.services.tasks.analyze_image")
    
    # Call directly, first arg 'self' can be None
    process_clothing_ai(None, new_id, "abc")
    
    db.refresh(new_item)
    assert new_item.status == "COMPLETED"
    assert new_item.category == FashionCategory.TOP
    mock_analyze.assert_not_called()
