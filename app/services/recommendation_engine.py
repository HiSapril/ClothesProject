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
    WEATHER_MATCH_BONUS = 20
    OCCASION_MATCH_BONUS = 20
    COLOR_HARMONY_BONUS = 15
    LOW_CONFIDENCE_PENALTY = -30
    UNKNOWN_CATEGORY_PENALTY = -50

    def recommend(self, db: Session, user_id: int, weather: Dict, occasion: OccasionEnum, 
                  strategy: str = "CONTEXT_AWARE", decision_layer_enabled: bool = True,
                  context_override: Dict = None, event_name: str = None) -> List[Dict]:
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
            tops = inventory[FashionCategory.TOP]
            bottoms = inventory[FashionCategory.BOTTOM]
            shoes = inventory[FashionCategory.FOOTWEAR]
            
            if tops and bottoms and shoes:
                potential_outerwear = inventory[FashionCategory.OUTERWEAR]
                for top in tops:
                    for bottom in bottoms:
                        for shoe in shoes:
                            base_items = [top, bottom, shoe]
                            # 1. Add base 3-item outfit
                            candidates.append(self._evaluate_outfit(base_items, weather, occasion, user))
                            
                            # 2. Add optional 4-item outfits with each available outerwear
                            if potential_outerwear:
                                for outer in potential_outerwear:
                                    candidates.append(self._evaluate_outfit(base_items + [outer], weather, occasion, user))
            else:
                # RELAXED: If full outfit not possible, suggest pairs or individuals
                # Research: Academic users prefer knowing WHY they have few options
                logger.warning(f"Full outfit not possible for user {user_id}. Falling back to partials.")
                all_possible = tops + bottoms + shoes + inventory[FashionCategory.OUTERWEAR] + inventory[FashionCategory.FULL_BODY]
                for item in all_possible[:10]:
                    candidates.append({
                        "items": [item],
                        "score": 10,
                        "reason": f"Món đồ lẻ gợi ý vì bạn chưa có đủ bộ phối đầy đủ (thiếu {'Giày' if not shoes else 'Quần' if not bottoms else 'Áo'})."
                    })

        # 2. Ranking
        candidates.sort(key=lambda x: (-x["score"], tuple(sorted([i.id for i in x["items"]]))))

        # 3. Decision Layer Application (if enabled)
        from app.services.decision_engine import DecisionEngine
        final_recs = []
        used_item_ids = set() # Track INDIVIDUAL items to prevent reuse

        # Sort again by score primarily
        candidates.sort(key=lambda x: -x["score"])

        for c in candidates:
            # Check if ANY item in this outfit has already been used in a higher-ranked outfit
            current_item_ids = set(i.id for i in c["items"])
            if not current_item_ids.isdisjoint(used_item_ids):
                continue
            
            decision_status = "CONFIRMED"
            if decision_layer_enabled:
                validation = DecisionEngine.validate_outfit_safety(c["items"], weather)
                decision_status = validation["status"]
                if decision_status == "REJECTED":
                    continue # Skip rejected for research clarity
                
                # Check for low-confidence items
                for item in c["items"]:
                    if item.classification_status == ClassificationStatus.LOW_CONFIDENCE:
                        decision_status = "LOW_CONFIDENCE"
                        break

            c["decision_status"] = decision_status
            final_recs.append(c)
            used_item_ids.update(current_item_ids) # Mark these items as consumed
            
            # Change: Pick 3 top, then stop to pick 2 wildcards later
            if len(final_recs) >= 3: break

        # 4. Wildcard Selection: Find the 2 LOWEST scoring unique-item outfits for baseline comparison
        if len(final_recs) < 5:
            # Sort candidates by score ASCENDING this time
            candidates_asc = sorted(candidates, key=lambda x: x["score"])
            for c in candidates_asc:
                current_item_ids = set(i.id for i in c["items"])
                if current_item_ids.isdisjoint(used_item_ids):
                    # Found a unique low-scoring outfit
                    decision_status = "CONFIRMED"
                    if decision_layer_enabled:
                        validation = DecisionEngine.validate_outfit_safety(c["items"], weather)
                        if validation["status"] == "REJECTED": continue
                    
                    c["decision_status"] = "CONFIRMED"
                    final_recs.append(c)
                    used_item_ids.update(current_item_ids)
                    
                    if len(final_recs) >= 5: break


        # Only generate LLM explanations for the top selected outfits (massive speedup)
        for c in final_recs:
            if "explanations" in c and "reason" not in c:
                c["reason"] = DecisionEngine.get_recommendation_explanation(
                    c["items"], weather, occasion.value, c["score"], c["explanations"],
                    event_name=event_name
                )

        # 4. Cache (only for valid CONTEXT_AWARE results)
        if strategy == "CONTEXT_AWARE" and not context_override:
            serializable_results = [{
                "items": [i.id for i in r["items"]],
                "score": r["score"],
                "reason": r["reason"],
                "decision_status": r["decision_status"]
            } for r in final_recs[:5]]
            cache.set(cache_key, serializable_results, ttl=300)

        return final_recs[:5]

    def _get_color_brightness(self, hex_color: str) -> float:
        """Returns 0 (very dark) to 1 (very bright) from a hex color string."""
        try:
            hx = hex_color.lstrip('#')
            if len(hx) != 6: return 0.5
            r, g, b = int(hx[0:2], 16), int(hx[2:4], 16), int(hx[4:6], 16)
            return (0.299 * r + 0.587 * g + 0.114 * b) / 255.0
        except:
            return 0.5

    def _evaluate_outfit(self, items: List[ClothingItem], weather: Dict, occasion: OccasionEnum, user=None) -> Dict:
        score = self.MATCH_BASE_SCORE
        explanations = [f"Base score: +{self.MATCH_BASE_SCORE}"]
        temp = weather.get("temp", 25)

        # --- 1. Occasion Match (Max +30) ---
        match_count = sum(1 for item in items if item.occasion == occasion)
        if match_count > 0:
            # Distributed match score (Total +20)
            distributed_score = (match_count / len(items)) * self.OCCASION_MATCH_BONUS
            score += distributed_score
            explanations.append(f"Occasion match ({match_count}/{len(items)}): +{round(distributed_score)}")

            # Full match bonus (Max +10)
            if match_count == len(items):
                score += 10
                explanations.append("Full occasion match bonus: +10")
        else:
            score -= 10
            explanations.append("Occasion mismatch: -10")

        # --- 2. Weather Suitability (Max +20) ---
        if temp < 18:
            has_outerwear = any(i.category == FashionCategory.OUTERWEAR for i in items)
            if has_outerwear:
                score += self.WEATHER_MATCH_BONUS
                explanations.append(f"Cold weather + outerwear: +{self.WEATHER_MATCH_BONUS}")
            else:
                score -= 20
                explanations.append("No outerwear in cold weather: -20")
        elif temp > 28:
            has_heavy = any("coat" in (i.category_label or "").lower() or "jacket" in (i.category_label or "").lower() for i in items)
            if has_heavy:
                score -= 15
                explanations.append("Too many layers for hot weather: -15")
            else:
                # Add weather bonus for appropriate layering in heat
                score += self.WEATHER_MATCH_BONUS
                explanations.append(f"Ideal layers for hot weather: +{self.WEATHER_MATCH_BONUS}")

        # --- 3. Color harmony (Max +15) ---
        color_bonus = 0
        items_with_color = [i for i in items if i.main_color_hex]
        if items_with_color:
            if temp > 25:
                # Light colors
                light_colors_count = sum(1 for i in items_with_color if self._get_color_brightness(i.main_color_hex) > 0.6)
                color_bonus = (light_colors_count / len(items_with_color)) * 15
                explanations.append(f"Cool light colors: +{color_bonus:.1f}")
            else:
                # Deep/warm colors
                dark_colors_count = sum(1 for i in items_with_color if self._get_color_brightness(i.main_color_hex) < 0.4)
                color_bonus = (dark_colors_count / len(items_with_color)) * 15
                explanations.append(f"Deep tones for warmth: +{color_bonus:.1f}")
        score += color_bonus

        # --- 4. AI Confidence Quality (Max +15) ---
        confirmed_count = sum(1 for i in items if i.classification_status == ClassificationStatus.CONFIRMED)
        if confirmed_count > 0:
            # Base bonus for confirmation (max +10)
            base_conf_bonus = (confirmed_count / len(items)) * 10
            
            # Granular bonus: use the actual 0-1.0 confidence score from Gemini (max +5)
            extra_granular = sum((i.confidence_score or 0.0) for i in items if i.classification_status == ClassificationStatus.CONFIRMED)
            conf_bonus = base_conf_bonus + (extra_granular * (5 / len(items))) 
            
            score += conf_bonus
            explanations.append(f"AI classification quality: +{conf_bonus:.2f}")

        # --- 5. Tie-breaker (Internal Ranking Only) ---
        # Tiny offset to break ties in ranking without affecting the visible integer score
        score += sum(i.id for i in items) / 1000000.0

        
        # Log decision metrics... (existing logic)

        for item in items:
            if item.classification_status == ClassificationStatus.LOW_CONFIDENCE:
                score += self.LOW_CONFIDENCE_PENALTY
                explanations.append(f"Low confidence penalty ({item.category_label}): {self.LOW_CONFIDENCE_PENALTY}")
            elif item.classification_status == ClassificationStatus.UNKNOWN:
                score += self.UNKNOWN_CATEGORY_PENALTY
                explanations.append(f"Unknown item penalty: {self.UNKNOWN_CATEGORY_PENALTY}")
        
        from app.services.decision_engine import DecisionEngine
        DecisionEngine.log_decision_metrics(
            action_type="recommendation",
            status="SUCCESS",
            metadata={
                "items_count": len(items),
                "weather": weather,
                "score": int(score),
                "breakdown": explanations
            }
        )

        return {
            "items": items,
            "score": int(score),
            "explanations": explanations  # Reason will be generated later for top K
        }

recommendation_engine = RecommendationEngine()
