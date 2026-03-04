import logging
from enum import Enum
from typing import Optional, Dict, Any
from app.domain.fashion_taxonomy import ClassificationStatus

logger = logging.getLogger("app")

class FailureCode(str, Enum):
    LOW_CONFIDENCE = "LOW_CONFIDENCE"
    CONFLICTING_CONTEXT = "CONFLICTING_CONTEXT"
    INSUFFICIENT_WARDROBE = "INSUFFICIENT_WARDROBE"
    SYSTEM_ERROR = "SYSTEM_ERROR"
    UNKNOWN_CATEGORY = "UNKNOWN_CATEGORY"

class DecisionEngine:
    """
    Intelligent layer that interprets raw AI model outputs 
    and turns them into business-safe decisions.
    """
    
    CONFIDENCE_THRESHOLD_STRICT = 0.85
    CONFIDENCE_THRESHOLD_MIN = 0.50

    @classmethod
    def classify_decision(cls, raw_label: str, confidence: float) -> Dict[str, Any]:
        """
        Determines the safety and status of a classification.
        """
        if confidence < cls.CONFIDENCE_THRESHOLD_MIN:
            return {
                "status": ClassificationStatus.UNKNOWN,
                "failure_code": FailureCode.LOW_CONFIDENCE,
                "suggested_action": "Hãy thử chụp ảnh lại với ánh sáng tốt hơn và phông nền đơn giản.",
                "reason": f"Độ tin cậy quá thấp ({confidence:.2f})"
            }
        
        if confidence < cls.CONFIDENCE_THRESHOLD_STRICT:
            return {
                "status": ClassificationStatus.LOW_CONFIDENCE,
                "failure_code": None,
                "suggested_action": "Vui lòng xác nhận lại loại quần áo này trong tủ đồ.",
                "reason": "Phân loại có độ tin cậy trung bình."
            }

        return {
            "status": ClassificationStatus.CONFIRMED,
            "failure_code": None,
            "suggested_action": None,
            "reason": "Phân loại chính xác cao."
        }

    @classmethod
    def get_recommendation_explanation(cls, items_count: int, weather: Dict, occasion: str) -> str:
        """
        Generates deterministic human-readable explanations (XAI-Lite).
        """
        temp = weather.get("temp", 25)
        condition = weather.get("condition", "Nắng")
        
        base = f"Dựa trên thời tiết {condition} ({temp}°C) và sự kiện {occasion}: "
        
        if temp < 18:
            action = "Chúng tôi đã chọn thêm một lớp áo khoác để giữ ấm cho bạn."
        elif temp > 28:
            action = "Chúng tôi ưu tiên các chất liệu thoáng mát và phối đồ đơn giản tránh nóng."
        else:
            action = "Đây là sự phối hợp lý tưởng cho tiết trời mát mẻ hôm nay."

        return f"{base}{action}"

    @classmethod
    def validate_outfit_safety(cls, items: List[Any], weather: Dict) -> Dict[str, Any]:
        """
        Academic Research: Detects illogical or unsafe outfit combinations.
        Returns a decision status and reasoning.
        """
        temp = weather.get("temp", 25)
        categories = [getattr(i, 'category', None) for i in items]
        
        # Scenario: Heavy outerwear in extreme heat
        if temp > 35:
            from app.domain.fashion_taxonomy import FashionCategory
            if FashionCategory.OUTERWEAR in categories:
                return {
                    "status": "REJECTED",
                    "reason": "Unsafe: Heavy outerwear suggested in extreme heat (>35°C)."
                }
        
        # Scenario: No shoes/pants (Incomplete outfit)
        # (This is more of a logic check than safety, but useful for evaluation)
        
        return {"status": "CONFIRMED", "reason": "Safe combination."}

    @classmethod
    def log_decision_metrics(cls, action_type: str, status: str, metadata: Dict = None):
        """
        Logs non-ML decision metrics for audit and improvement.
        """
        logger.info(
            f"[DECISION_METRIC] Type: {action_type} | Status: {status} | Details: {metadata or {}}"
        )

decision_engine = DecisionEngine()
