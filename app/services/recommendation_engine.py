from typing import List, Dict
from sqlalchemy.orm import Session
from app.db.models import ClothingItem, ClothingTypeEnum, OccasionEnum
import random

class RecommendationEngine:
    
    def recommend(self, db: Session, user_id: int, weather: Dict, occasion: OccasionEnum) -> List[Dict]:
        """
        Main logic flow:
        1. Fetch User Inventory
        2. Filter by Weather (Temperature, Rain)
        3. Filter by Occasion
        4. Color Matching (Simple Complementary)
        5. Return Top 3 Combinations
        """
        
    def _get_color_analysis(self, items: List[ClothingItem]):
        # Simple color theory logic
        colors = [i.main_color_hex for i in items if i.main_color_hex]
        if not colors: return "Sự phối hợp màu sắc hài hòa."
        
        # In a real app, this would use a color library. For now, we simulate knowledge.
        return "Sự phối hợp giữa các tông màu này tạo nên một tổng thể cân đối, không quá chói mắt nhưng vẫn đủ ấn tượng."

    def _generate_deep_reasoning(self, items: List[ClothingItem], weather: Dict, occasion: OccasionEnum, user=None):
        temp = weather.get("temp", 25)
        condition = weather.get("condition", "clear").lower()
        
        steps = []
        
        # --- Bước 1: Phân tích người mặc ---
        gender_type = "Quý ông" if user and user.gender == "Nam" else "Quý cô" if user and user.gender == "Nữ" else "Người dùng"
        body_type = "cân đối"
        if user and user.height and user.weight:
            bmi = user.weight / ((user.height / 100) ** 2)
            if bmi < 18.5: body_type = "mảnh khảnh"
            elif bmi > 25: body_type = "đầy đặn"
        steps.append(f"- Người mặc: {gender_type} vóc dáng {body_type}, phong cách tối giản thanh lịch.")

        # --- Bước 2: Phân tích hoàn cảnh sử dụng ---
        occ_str = "trang trọng" if occasion == OccasionEnum.FORMAL else "năng động" if occasion == OccasionEnum.SPORT else "thường ngày"
        steps.append(f"- Hoàn cảnh: Phù hợp bối cảnh {occ_str} trong tiết trời {temp}°C ({condition}).")

        # --- Bước 3: Phân tích mục tiêu mặc ---
        goal = "tôn dáng và chuyên nghiệp"
        if occasion == OccasionEnum.SPORT: goal = "linh hoạt vận động"
        elif occasion == OccasionEnum.CASUAL: goal = "thoải mái, thanh lịch tự nhiên"
        steps.append(f"- Mục tiêu: Giúp bạn {goal}, tự tin trong mọi tương tác.")

        # --- Bước 4: Đưa ra nguyên tắc lựa chọn ---
        principle = "Gam màu trung tính, chất liệu bền vững."
        if "mưa" in condition or "rain" in condition: principle = "Chất liệu nhanh khô, màu tối phần dưới tránh bẩn."
        elif temp > 28: principle = "Vải mỏng nhẹ, phom suông thoáng mát."
        steps.append(f"- Nguyên tắc: {principle} Phối màu tương đồng tạo tổng thể mượt mà.")

        # --- Bước 5: Đề xuất outfit cụ thể ---
        items_str = ", ".join([f"{i.category_label}" for i in items])
        steps.append(f"- Đề xuất: Phối hợp giữa {items_str} với sắc độ hài hòa.")

        # --- Bước 6: Lý do + mẹo bổ sung ---
        tip = "Sơ vin nhẹ và thêm đồng hồ để tạo điểm nhấn."
        if occasion == OccasionEnum.FORMAL: tip = "Giày và thắt lưng nên đồng nhất màu sắc/chất liệu."
        steps.append(f"- Mẹo từ chuyên gia: {tip} Giúp tôn ưu điểm tự nhiên của bạn.")

        return "\n".join(steps)

    def recommend(self, db: Session, user_id: int, weather: Dict, occasion: OccasionEnum) -> List[Dict]:
        """
        Main logic flow:
        1. Fetch User Inventory
        2. Filter by Weather (Temperature, Rain)
        3. Filter by Occasion (with progressive relaxation)
        4. Strategy Generation (Tops+Bottoms, Full Body, Fallbacks)
        5. Variation Scaling (Ensure 3 outfits if possible)
        """
        
        # 1. Fetch Inventory & User Context
        print(f"DEBUG: Recommend called for user {user_id} with occasion {occasion}")
        from app.db import models
        user = db.query(models.User).filter(models.User.id == user_id).first()
        all_items = db.query(ClothingItem).filter(ClothingItem.user_id == user_id).all()
        
        if not all_items:
            return []

        temp = weather.get("temp", 25)
        condition = weather.get("condition", "clear")
        
        # Filter items by type
        tops = [i for i in all_items if i.type == ClothingTypeEnum.TOP]
        bottoms = [i for i in all_items if i.type == ClothingTypeEnum.BOTTOM]
        shoes = [i for i in all_items if i.type == ClothingTypeEnum.SHOES]
        outerwear = [i for i in all_items if i.type == ClothingTypeEnum.OUTERWEAR]
        full_body = [i for i in all_items if i.type == ClothingTypeEnum.FULL]

        # --- Dynamic Rules based on User Info (Height/Weight/Gender) ---
        if user and user.gender == "Nam":
            bottoms = [b for b in bottoms if "váy" not in (b.category_label or "").lower()]
            full_body = [] 
        
        # --- Filter 1: Weather ---
        needs_outerwear = temp < 18
        
        valid_shoes = shoes
        if "rain" in condition.lower() or "mưa" in condition.lower():
            valid_shoes = [s for s in shoes if "white" not in (s.main_color_hex or "").lower()]
            if not valid_shoes: valid_shoes = shoes

        # --- Filter 2: Occasion (Progressive Relaxation) ---
        v_tops = self._filter_by_occasion(tops, occasion)
        v_bottoms = self._filter_by_occasion(bottoms, occasion)
        v_shoes = self._filter_by_occasion(valid_shoes, occasion)
        v_outer = self._filter_by_occasion(outerwear, occasion)
        v_full = self._filter_by_occasion(full_body, occasion)

        outfits = []
        
        # Strategy A: Top + Bottom
        for top in v_tops:
            for bottom in v_bottoms:
                current_shoes = v_shoes if v_shoes else valid_shoes
                for shoe in current_shoes:
                    outfit_items = [top, bottom, shoe]
                    score = 10
                    if needs_outerwear:
                        outer = random.choice(v_outer) if v_outer else (random.choice(outerwear) if outerwear else None)
                        if outer: outfit_items.append(outer)
                    outfits.append({"items": outfit_items, "score": score})

        # Strategy B: Full Body 
        for fb in v_full:
            current_shoes = v_shoes if v_shoes else valid_shoes
            for shoe in current_shoes:
                 outfit_items = [fb, shoe]
                 score = 10
                 if needs_outerwear:
                     outer = random.choice(v_outer) if v_outer else (random.choice(outerwear) if outerwear else None)
                     if outer: outfit_items.append(outer)
                 outfits.append({"items": outfit_items, "score": score})

        # --- Relaxation Round 1: Mix Casual into Formal/Sport if needed ---
        if len(outfits) < 3:
            # If for formal/sport we don't have enough, try including regular items
            if occasion != OccasionEnum.CASUAL:
                relaxed_tops = [t for t in tops if t not in v_tops]
                relaxed_bottoms = [b for b in bottoms if b not in v_bottoms]
                
                # Combine relaxed items with valid or other items
                for t in (v_tops + relaxed_tops[:3]):
                    for b in (v_bottoms + relaxed_bottoms[:3]):
                        if t in v_tops and b in v_bottoms: continue # Skip already added
                        
                        current_shoes = v_shoes if v_shoes else valid_shoes
                        for shoe in current_shoes[:2]:
                            items = [t, b, shoe]
                            if needs_outerwear:
                                outer = random.choice(outerwear) if outerwear else None
                                if outer: items.append(outer)
                            outfits.append({"items": items, "score": 7})

        # --- Fallback: Forced Generation ---
        if not outfits:
            # Last resort: just pick everything available regardless of occasion
            for _ in range(5): # Generate a few random combos
                f_top = random.choice(tops) if tops else None
                f_bottom = random.choice(bottoms) if bottoms else None
                f_shoe = random.choice(shoes) if shoes else None
                f_full = random.choice(full_body) if full_body else None
                
                if f_top and f_bottom and f_shoe:
                    outfits.append({"items": [f_top, f_bottom, f_shoe], "score": 5})
                elif f_full and f_shoe:
                    outfits.append({"items": [f_full, f_shoe], "score": 5})

        # Final check if still empty, push ANY items
        if not outfits and all_items:
            outfits.append({"items": all_items[:3], "score": 1})

        # Shuffle and pick top 3
        random.shuffle(outfits)
        
        # Deduplicate by item set to avoid identical recommendations
        unique_outfits = []
        seen_sets = set()
        for o in outfits:
            item_ids = tuple(sorted([i.id for i in o["items"]]))
            if item_ids not in seen_sets:
                unique_outfits.append(o)
                seen_sets.add(item_ids)
        
        final_outfits = unique_outfits[:3]

        # --- 3. Add Advanced AI reasoning ---
        for outfit in final_outfits:
            outfit["reason"] = self._generate_deep_reasoning(outfit["items"], weather, occasion, user)

        return final_outfits

    def _filter_by_occasion(self, items: List[ClothingItem], occasion: OccasionEnum):
        if occasion == OccasionEnum.FORMAL:
            return [i for i in items if i.occasion == OccasionEnum.FORMAL]
        elif occasion == OccasionEnum.SPORT:
            return [i for i in items if i.occasion == OccasionEnum.SPORT or i.occasion == OccasionEnum.CASUAL]
        else:
            return [i for i in items if i.occasion != OccasionEnum.FORMAL]

    def _is_color_match(self, hex1, hex2):
        return True

recommendation_engine = RecommendationEngine()
