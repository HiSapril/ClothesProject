import os
import io
import certifi
from PIL import Image
import logging

# Force correct SSL certificate path to avoid system-level conflicts (e.g. PostgreSQL)
os.environ['SSL_CERT_FILE'] = certifi.where()
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()

from celery import shared_task
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.db import models
from app.services.ai_service import analyze_image, enhance_classification_with_llm
from app.domain.fashion_taxonomy import map_imagenet_label, ClassificationStatus
from celery.exceptions import SoftTimeLimitExceeded

logger = logging.getLogger("app")

def process_clothing_ai(item_id: int, image_hex: str, request_id: str = None, db: Session = None):
    # Use provided session or create a new one
    local_session = False
    if db is None:
        db = SessionLocal()
        local_session = True
        
    item = None
    try:
        logger.info(f"Processing AI for item {item_id}")
        item = db.query(models.ClothingItem).filter(models.ClothingItem.id == item_id).first()
        
        if not item:
            logger.error(f"Item {item_id} not found in database")
            return {"status": "FAILED", "message": "Item not found"}
        
        item.status = "PROCESSING"
        db.commit()

        # 1. Deduplication Check
        if item.image_hash:
            existing = db.query(models.ClothingItem).filter(
                models.ClothingItem.image_hash == item.image_hash,
                models.ClothingItem.status == "completed",
                models.ClothingItem.id != item_id
            ).first()
            
            if existing:
                logger.info(f"AI Deduplication HIT for item {item_id}")
                item.category = existing.category
                item.category_label = existing.category_label
                item.category_raw = existing.category_raw
                item.confidence_score = existing.confidence_score
                item.classification_status = existing.classification_status
                item.raw_model_output = existing.raw_model_output
                item.processed_image_path = existing.processed_image_path
                item.main_color_hex = existing.main_color_hex
                item.type = existing.type
                item.occasion = existing.occasion
                item.status = "COMPLETED"
                db.commit()
                return {"status": "COMPLETED", "item_id": item_id, "deduplicated": True}

        logger.info(f"AI Deduplication MISS for item {item_id}")
        # 2. Process with AI
        image_bytes = bytes.fromhex(image_hex)
        ai_results = analyze_image(image_bytes)
        
        raw_label = ai_results['category_raw']
        confidence = ai_results['confidence']
        
        # Parse Gemini direct enum output if applicable
        from app.domain.fashion_taxonomy import FashionCategory
        try:
            category = FashionCategory(raw_label.upper())
        except ValueError:
            category = map_imagenet_label(raw_label)
        
        # 3. Decision Layer
        from app.services.decision_engine import DecisionEngine
        decision = DecisionEngine.classify_decision(raw_label, confidence)
        
        # Log decision metrics for performance audit
        DecisionEngine.log_decision_metrics(
            action_type="classification",
            status=decision["status"],
            metadata={
                "item_id": item_id,
                "confidence": confidence,
                "raw_label": raw_label,
                "mapped_category": category.name
            }
        )

        # 4. Enhance with DeepSeek LLM
        deepseek_enhancement = enhance_classification_with_llm(raw_label, ai_results['color_hex'])
        
        # 5. Update Database
        item.category = category
        item.category_label = deepseek_enhancement.get('style_tag', raw_label)
        item.confidence_score = confidence
        item.classification_status = decision["status"]
        item.failure_code = decision["failure_code"]
        item.suggested_action = decision["suggested_action"]
        item.raw_model_output = ai_results['raw_output']
        item.processed_image_path = ai_results['processed_image_path']
        item.main_color_hex = ai_results['color_hex']
        
        # Map occasion string to Enum safely
        from app.db.models import OccasionEnum
        occ_str = deepseek_enhancement.get('occasion', 'casual').lower()
        try:
            item.occasion = OccasionEnum(occ_str)
        except ValueError:
            item.occasion = OccasionEnum.CASUAL
            
        item.status = "COMPLETED"
        
        from app.db.models import ClothingTypeEnum
        type_map = {
            "TOP": ClothingTypeEnum.TOP,
            "BOTTOM": ClothingTypeEnum.BOTTOM,
            "FOOTWEAR": ClothingTypeEnum.SHOES,
            "OUTERWEAR": ClothingTypeEnum.OUTERWEAR,
            "FULL_BODY": ClothingTypeEnum.FULL
        }
        item.type = type_map.get(category.name)
        db.commit()
        return {"status": "COMPLETED", "item_id": item_id}

    except SoftTimeLimitExceeded:
        logger.error(f"Task timeout (soft) for item {item_id}")
        if item:
            item.status = "FAILED"
            item.failure_reason = "AI timeout exceeded"
            db.commit()
        return {"status": "FAILED", "message": "Timeout"}
    except Exception as e:
        logger.error(f"AI error: {str(e)}", exc_info=True)
        if item:
            item.status = "FAILED"
            item.failure_reason = str(e)
            db.commit()
        return {"status": "FAILED", "message": str(e)}
    finally:
        if local_session and db:
            db.close()
