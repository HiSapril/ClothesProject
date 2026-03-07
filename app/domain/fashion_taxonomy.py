from enum import Enum
from typing import Dict, Optional

class FashionCategory(str, Enum):
    TOP = "TOP"
    BOTTOM = "BOTTOM"
    OUTERWEAR = "OUTERWEAR"
    FOOTWEAR = "FOOTWEAR"
    ACCESSORY = "ACCESSORY"
    FULL_BODY = "FULL_BODY" # Dress, Suit
    UNKNOWN = "UNKNOWN"

class ClassificationStatus(str, Enum):
    CONFIRMED = "CONFIRMED"
    LOW_CONFIDENCE = "LOW_CONFIDENCE"
    UNKNOWN = "UNKNOWN"

# Mapping from common ImageNet labels to FashionCategory
# This is a representative subset. In a real production app, 
# this would map all relevant 1000 ImageNet classes or use a fine-tuned model.
IMAGENET_TO_FASHION: Dict[str, FashionCategory] = {
    # Tops
    "t-shirt": FashionCategory.TOP,
    "jersey": FashionCategory.TOP,
    "sweatshirt": FashionCategory.TOP,
    "cardigan": FashionCategory.TOP,
    "sweater": FashionCategory.TOP,
    "polo shirt": FashionCategory.TOP,
    "shirt": FashionCategory.TOP,
    
    # Bottoms
    "jean": FashionCategory.BOTTOM,
    "drilling": FashionCategory.BOTTOM,
    "skirt": FashionCategory.BOTTOM,
    "short": FashionCategory.BOTTOM,
    "trouser": FashionCategory.BOTTOM,
    "pant": FashionCategory.BOTTOM,
    "miniskirt": FashionCategory.BOTTOM,
    "sweatpants": FashionCategory.BOTTOM,
    "pajama": FashionCategory.BOTTOM,
    "cargo": FashionCategory.BOTTOM,
    "legging": FashionCategory.BOTTOM,
    
    # Outerwear
    "jacket": FashionCategory.OUTERWEAR,
    "coat": FashionCategory.OUTERWEAR,
    "parka": FashionCategory.OUTERWEAR,
    "trench coat": FashionCategory.OUTERWEAR,
    "overcoat": FashionCategory.OUTERWEAR,
    "windbreaker": FashionCategory.OUTERWEAR,
    
    # Footwear
    "shoe": FashionCategory.FOOTWEAR,
    "sneaker": FashionCategory.FOOTWEAR,
    "boot": FashionCategory.FOOTWEAR,
    "sandal": FashionCategory.FOOTWEAR,
    "slipper": FashionCategory.FOOTWEAR,
    "flip-flop": FashionCategory.FOOTWEAR,
    "clog": FashionCategory.FOOTWEAR,
    "loafer": FashionCategory.FOOTWEAR,
    
    # Full Body
    "dress": FashionCategory.FULL_BODY,
    "gown": FashionCategory.FULL_BODY,
    "robe": FashionCategory.FULL_BODY,
    "kimono": FashionCategory.FULL_BODY,
    "suit": FashionCategory.FULL_BODY,
    
    # Accessories
    "watch": FashionCategory.ACCESSORY,
    "bracelet": FashionCategory.ACCESSORY,
    "necktie": FashionCategory.ACCESSORY,
    "sunglass": FashionCategory.ACCESSORY,
    "spectacle": FashionCategory.ACCESSORY,
    "hat": FashionCategory.ACCESSORY,
    "cap": FashionCategory.ACCESSORY,
    "belt": FashionCategory.ACCESSORY,
    "bag": FashionCategory.ACCESSORY,
    "wallet": FashionCategory.ACCESSORY,
    "purse": FashionCategory.ACCESSORY,
}

def map_imagenet_label(label: str) -> FashionCategory:
    """
    Deterministically maps an ImageNet label to a FashionCategory.
    Returns UNKNOWN if no mapping is found.
    """
    label_lower = label.lower()
    
    # Exact matches first
    if label_lower in IMAGENET_TO_FASHION:
        return IMAGENET_TO_FASHION[label_lower]
    
    # Substring matches for fallback (more deterministic than wild heuristics)
    for key, category in IMAGENET_TO_FASHION.items():
        if key in label_lower:
            return category
            
    return FashionCategory.UNKNOWN
