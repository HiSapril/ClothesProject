from app.db.database import SessionLocal
from app.db.models import ClothingItem, ClothingTypeEnum
from app.services.ai_service import analyze_image
from PIL import Image
import os
import io

def correct_tags():
    db = SessionLocal()
    # Find items tagged as Mat Kinh
    items = db.query(ClothingItem).filter(ClothingItem.category_label == "Mắt kính").all()
    
    corrections = 0
    for item in items:
        # Since we don't have category_raw for old items, let's re-classify using the image!
        if not os.path.exists(item.processed_image_path):
            print(f"File not found: {item.processed_image_path}")
            continue
            
        with open(item.processed_image_path, "rb") as f:
            img_bytes = f.read()
            
        # We only need classification, but let's just use classify_apparel if accessible
        # or analyze_image for simplicity
        try:
            from app.services.ai_service import classify_apparel
            img = Image.open(io.BytesIO(img_bytes))
            cat_raw = classify_apparel(img).lower()
        except Exception as e:
            print(f"AI classification failed for {item.id}: {e}")
            continue
            
        # Store the raw category now anyway
        item.category_raw = cat_raw
        
        new_label = None
        new_type = None
        
        if any(kw in cat_raw for kw in ["watch", "stopwatch", "clock", "chronometer", "timer"]):
            new_label = "Đồng hồ"
            new_type = ClothingTypeEnum.WATCH
        elif any(kw in cat_raw for kw in ["bracelet", "bangle", "wrist", "armlet", "bead", "jewelry"]):
            new_label = "Vòng tay"
            new_type = ClothingTypeEnum.BRACELET
        elif any(kw in cat_raw for kw in ["necklace", "pendant", "locket", "chain", "choker"]):
            new_label = "Dây chuyền"
            new_type = ClothingTypeEnum.NECKLACE
            
        if new_label and new_label != item.category_label:
            print(f"Correcting {item.id} ({cat_raw}): {item.category_label} -> {new_label}")
            item.category_label = new_label
            item.type = new_type # Correct attribute name is 'type'
            corrections += 1
            
    if corrections > 0 or items:
        db.commit()
    print(f"Total corrections: {corrections}")
    db.close()

if __name__ == "__main__":
    correct_tags()
