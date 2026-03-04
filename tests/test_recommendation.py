import pytest
from app.services.recommendation_engine import RecommendationEngine
from app.domain.fashion_taxonomy import FashionCategory
from app.db import models

@pytest.fixture
def engine():
    return RecommendationEngine()

def test_deterministic_scoring(engine):
    """Test that the same input yields the same score and explanation."""
    item = models.ClothingItem(
        id=1, 
        category=FashionCategory.TOP, 
        category_label="T-shirt",
        main_color_hex="#FFFFFF"
    )
    
    # Simulating weather & context
    weather = {"main": "Clear", "temp": 25}
    occasion = "casual"
    
    result1 = engine._evaluate_outfit([item], weather, occasion)
    result2 = engine._evaluate_outfit([item], weather, occasion)
    
    assert result1["score"] == result2["score"]
    assert result1["reason"] == result2["reason"]
    assert "Base score" in result1["reason"]

def test_low_confidence_penalty(engine):
    """Test that items with low confidence receive a penalty score."""
    # We'll mock the internal scoring constants or just check the delta
    item_confirmed = models.ClothingItem(category=FashionCategory.TOP, classification_status="CONFIRMED")
    item_low = models.ClothingItem(category=FashionCategory.TOP, classification_status="LOW_CONFIDENCE")
    
    weather = {"main": "Clear", "temp": 25}
    
    result_confirmed = engine._evaluate_outfit([item_confirmed], weather, "casual")
    result_low = engine._evaluate_outfit([item_low], weather, "casual")
    
    assert result_low["score"] < result_confirmed["score"]
