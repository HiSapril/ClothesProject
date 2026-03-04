import pytest
from app.domain.fashion_taxonomy import FashionCategory, ClassificationStatus, map_imagenet_label

def test_category_mapping():
    """Test that ImageNet labels map to correct FashionCategories."""
    assert map_imagenet_label("jersey, T-shirt") == FashionCategory.TOP
    assert map_imagenet_label("jean, blue jean, denim") == FashionCategory.BOTTOM
    assert map_imagenet_label("sunglass, sunglasses") == FashionCategory.ACCESSORY
    assert map_imagenet_label("unknown_label") == FashionCategory.UNKNOWN

def test_confidence_status_logic():
    """Test logic for setting classification status based on confidence score."""
    CONFIDENCE_THRESHOLD = 0.5
    
    def get_status_logic(score):
        if score >= CONFIDENCE_THRESHOLD:
            return ClassificationStatus.CONFIRMED
        return ClassificationStatus.LOW_CONFIDENCE

    assert get_status_logic(0.8) == ClassificationStatus.CONFIRMED
    assert get_status_logic(0.3) == ClassificationStatus.LOW_CONFIDENCE
