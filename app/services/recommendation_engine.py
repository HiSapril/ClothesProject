from typing import List, Dict, Tuple
from sqlalchemy.orm import Session
from app.db.models import ClothingItem, OccasionEnum
from app.domain.fashion_taxonomy import FashionCategory, ClassificationStatus
import os
import logging

logger = logging.getLogger("app")

class RecommendationEngine:
    # --- Scoring Constants ---
    MATCH_BASE_SCORE = 20
    WEATHER_MATCH_BONUS = 15
    OCCASION_MATCH_BONUS = 15
    COLOR_HARMONY_BONUS = 10
    LOW_CONFIDENCE_PENALTY = -30
    UNKNOWN_CATEGORY_PENALTY = -50

    def recommend(self, db: Session, user_id: int, weather: Dict, occasion: OccasionEnum, 
                  strategy: str = "CONTEXT_AWARE", decision_layer_enabled: bool = True,
                  context_override: Dict = None) -> List[Dict]:
        """
        Deterministic Recommendation Engine with Research Support.
        """
        if context_override:
            if "temp" in context_override: weather["temp"] = context_override["temp"]
            if "condition" in context_override: weather["condition"] = context_override["condition"]

        from app.core.cache import cache
        
        # 0. Cache (Only for CONTEXT_AWARE without overrides)
        if strategy == "CONTEXT_AWARE" and not context_override:
            temp_sig = int(round(weather.get("temp", 25)))
            cond_sig = weather.get("condition", "Clear")
            weather_sig = f"{temp_sig}_{cond_sig}"
            cache_key = f"rec:{user_id}:{occasion.value}:{weather_sig}"
            cached_recs = cache.get(cache_key)
            if cached_recs:
                logger.info(f"Recommendation cache HIT for user {user_id}")
                final_recs = []
                for entry in cached_recs:
                    db_items = db.query(ClothingItem).filter(ClothingItem.id.in_(entry["items"])).all()
                    item_map = {item.id: item for item in db_items}
                    final_recs.append({
                        "items": [item_map[iid] for iid in entry["items"] if iid in item_map],
                        "score": entry["score"],
                        "reason": entry["reason"],
                        "decision_status": entry.get("decision_status", "CONFIRMED")
                    })
                return final_recs

        logger.info(f"Rec Request: User={user_id}, Strategy={strategy}, DecisionLayer={decision_layer_enabled}")
        
        from app.db import models
        user = db.query(models.User).filter(models.User.id == user_id).first()
        all_items = db.query(ClothingItem).filter(ClothingItem.user_id == user_id).all()
        
        if not all_items: return []

        # 1. Group items by taxonomy
        inventory = {cat: [i for i in all_items if i.category == cat] for cat in FashionCategory}
        
        temp = weather.get("temp", 25)
        candidates = []

        # Strategy Switch
        if strategy == "BASELINE":
            # Simple category-only logic: Just pick one of each available
            tops = inventory[FashionCategory.TOP]
            bottoms = inventory[FashionCategory.BOTTOM]
            shoes = inventory[FashionCategory.FOOTWEAR]
            if tops and bottoms and shoes:
                for t in tops[:2]:
                    for b in bottoms[:2]:
                        for s in shoes[:2]:
                            candidates.append({
                                "items": [t, b, s],
                                "score": 20,
                                "reason": "Baseline Rule: One of each category."
                            })
        else:
            # CONTEXT_AWARE Logic
            for top in inventory[FashionCategory.TOP]:
                for bottom in inventory[FashionCategory.BOTTOM]:
                    for shoe in inventory[FashionCategory.FOOTWEAR]:
                        items = [top, bottom, shoe]
                        potential_outerwear = inventory[FashionCategory.OUTERWEAR]
                        if temp < 18 and potential_outerwear:
                            for outer in potential_outerwear:
                                candidates.append(self._evaluate_outfit(items + [outer], weather, occasion, user))
                        else:
                            candidates.append(self._evaluate_outfit(items, weather, occasion, user))

        # 2. Ranking
        candidates.sort(key=lambda x: (-x["score"], tuple(sorted([i.id for i in x["items"]]))))

        # 3. Decision Layer Application (if enabled)
        from app.services.decision_engine import DecisionEngine
        final_recs = []
        seen_items = set()

        for c in candidates:
            item_tuple = tuple(sorted([i.id for i in c["items"]]))
            if item_tuple in seen_items: continue
            
            decision_status = "CONFIRMED"
            if decision_layer_enabled:
                validation = DecisionEngine.validate_outfit_safety(c["items"], weather)
                decision_status = validation["status"]
                if decision_status == "REJECTED":
                    c["reason"] = f"REJECTED by Decision Layer: {validation['reason']}"
                    c["score"] = -999 # Sink rejected outfits
                
                # Check for low-confidence items
                for item in c["items"]:
                    if item.classification_status == ClassificationStatus.LOW_CONFIDENCE:
                        decision_status = "LOW_CONFIDENCE"
                        break

            c["decision_status"] = decision_status
            final_recs.append(c)
            seen_items.add(item_tuple)
            if len(final_recs) >= 5: break

        # 4. Cache (only for valid CONTEXT_AWARE results)
        if strategy == "CONTEXT_AWARE" and not context_override:
            serializable_results = [{
                "items": [i.id for i in r["items"]],
                "score": r["score"],
                "reason": r["reason"],
                "decision_status": r["decision_status"]
            } for r in final_recs[:3]]
            cache.set(cache_key, serializable_results, ttl=300)

        return final_recs[:3]

    def _evaluate_outfit(self, items: List[ClothingItem], weather: Dict, occasion: OccasionEnum, user=None) -> Dict:
        score = self.MATCH_BASE_SCORE
        explanations = [f"Base score: +{self.MATCH_BASE_SCORE}"]
        temp = weather.get("temp", 25)

        occ_matches = sum(1 for item in items if item.occasion == occasion)
        if occ_matches > 0:
            bonus = self.OCCASION_MATCH_BONUS * (occ_matches / len(items))
            score += bonus
            explanations.append(f"Occasion match bonus: +{bonus:.1f}")
        else:
            score -= 10
            explanations.append("Occasion mismatch penalty: -10")

        if temp < 18:
            has_outerwear = any(i.category == FashionCategory.OUTERWEAR for i in items)
            if has_outerwear:
                score += self.WEATHER_MATCH_BONUS
                explanations.append(f"Cold weather protection: +{self.WEATHER_MATCH_BONUS}")
            else:
                score -= 20
                explanations.append("Lack of outerwear in cold weather: -20")
        elif temp > 28:
            has_heavy = any("coat" in (i.category_label or "").lower() or "jacket" in (i.category_label or "").lower() for i in items)
            if has_heavy:
                score -= 15
                explanations.append("Too many layers for hot weather: -15")
        
        for item in items:
            if item.classification_status == ClassificationStatus.LOW_CONFIDENCE:
                score += self.LOW_CONFIDENCE_PENALTY
                explanations.append(f"Low confidence penalty ({item.category_label}): {self.LOW_CONFIDENCE_PENALTY}")
            elif item.classification_status == ClassificationStatus.UNKNOWN:
                score += self.UNKNOWN_CATEGORY_PENALTY
                explanations.append(f"Unknown item penalty: {self.UNKNOWN_CATEGORY_PENALTY}")
        
        from app.services.decision_engine import DecisionEngine
        summary = DecisionEngine.get_recommendation_explanation(len(items), weather, occasion.value)
        
        DecisionEngine.log_decision_metrics(
            action_type="recommendation",
            status="SUCCESS",
            metadata={
                "items_count": len(items),
                "weather": weather,
                "score": int(score)
            }
        )

        return {
            "items": items,
            "score": int(score),
            "reason": summary # Replace raw explanation trail with refined XAI summary
        }

recommendation_engine = RecommendationEngine()
