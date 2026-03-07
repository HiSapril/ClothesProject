import logging
from enum import Enum
from typing import Optional, Dict, Any, List
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
    def get_recommendation_explanation(cls, items: List[Any], weather: Dict, occasion: str, score: int, breakdown: List[str], event_name: str = None) -> str:
        """
        Generates dynamic, item-aware explanations (XAI-Lite) using DeepSeek LLM if available,
        falling back to deterministic reasoning if the API fails or is disabled.
        """
        temp = weather.get("temp", 25)
        condition = weather.get("condition", "Nắng")
        item_names = [getattr(i, 'category_label', 'đồ') for i in items]
        
        # Score from algorithm: max possible score is exactly 100 points.
        suitability_pct = min(100, max(0, round(score)))
        
        # Base deterministic explanation (Fallback)
        event_ctx = f" sự kiện '{event_name}'" if event_name else ""
        base = f"🎯 Độ phù hợp: {suitability_pct}/100 | ✨ Phân tích: "
        
        condition_map = {
            "Nắng": "trời nắng ráo",
            "Mưa": "trời có mưa",
            "Mây": "trời nhiều mây",
            "Tuyết": "trời có tuyết"
        }
        weather_desc = condition_map.get(condition, f"tiết trời {condition}")
        
        if suitability_pct >= 80:
            status_desc = "rất lý tưởng"
        elif suitability_pct >= 60:
            status_desc = "khá ổn"
        else:
            status_desc = "chưa thực sự tối ưu"

        action = f"Sự kết hợp giữa {', '.join(item_names)} {status_desc} cho {weather_desc} ({temp}°C) và bối cảnh {occasion}{event_ctx}."
        fallback_text = f"{base}{action}"

        # Attempt to use DeepSeek LLM
        from app.core.config import settings
        import requests
        
        # Verify the key is not default/missing
        if not settings.DEEPSEEK_API_KEY or "your_" in settings.DEEPSEEK_API_KEY:
            return fallback_text

        try:
            url = "https://openrouter.ai/api/v1/chat/completions"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}",
                "HTTP-Referer": "http://localhost:8000",
                "X-Title": "OutfitAI"
            }
            
            event_line = f"Sự kiện: '{event_name}'.\n" if event_name else ""
            prompt = f"Bối cảnh: {occasion}. Thời tiết: {condition}, {temp}°C.\n" \
                     f"{event_line}" \
                     f"Trang phục: {', '.join(item_names)}.\n" \
                     f"Điểm phù hợp: {suitability_pct}/100.\n" \
                     f"Hãy đóng vai Stylist AI giàu kinh nghiệm. Hãy viết 2-3 câu tiếng Việt để:\n" \
                     f"1. Giải thích lý do tại sao bộ đồ đạt số điểm {suitability_pct}/100 (Phân tích ưu/nhược điểm cụ thể về màu sắc, thời tiết hoặc bối cảnh).\n" \
                     f"2. Nêu lý do hệ thống chọn sự kết hợp này.\n" \
                     f"3. Nếu điểm thấp, hãy chỉ rõ điểm chưa ổn để người dùng rút kinh nghiệm.\n" \
                     f"Lưu ý: Không dùng ngoặc kép, trả lời trực diện, súc tích."
            
            payload = {
                "model": "deepseek/deepseek-chat",
                "messages": [
                    {"role": "system", "content": "You are an expert personal stylist AI. Provide a deep, analytical explanation for an outfit's suitability score (0-100). Focus on pros/cons, weather logic, and occasion alignment. Use friendly but professional Vietnamese."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.5,
                "max_tokens": 400
            }
            
            # Use a slightly longer timeout (max 5 seconds) to ensure response
            response = requests.post(url, headers=headers, json=payload, timeout=5.0)
            
            if response.status_code == 200:
                data = response.json()
                if "choices" in data and len(data["choices"]) > 0:
                    ai_text = data["choices"][0]["message"]["content"].strip()
                    ai_text = ai_text.replace('"', '').replace("'", "")
                    # Ensure the response includes the required prefix for UI consistency
                    return f"🎯 Độ phù hợp: {suitability_pct}/100 | ✨ Stylist AI: {ai_text}"
            else:
                logger.warning(f"DeepSeek API returned {response.status_code}: {response.text}")
                
        except (requests.exceptions.RequestException, Exception) as e:
            logger.warning(f"DeepSeek API Call failed: {e}. Using deterministic fallback.")
            
        return fallback_text

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
