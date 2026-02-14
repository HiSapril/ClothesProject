import sys
import os
import unittest
from unittest.mock import MagicMock
from datetime import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from app.services.recommendation_engine import RecommendationEngine
from app.db.models import ClothingItem, ClothingTypeEnum, OccasionEnum, User

class TestRecommendationEngine(unittest.TestCase):
    def setUp(self):
        self.engine = RecommendationEngine()
        self.db = MagicMock()
        self.user_id = 1
        self.user = User(id=1, gender="Nam", age=30, height=175, weight=70)
        self.db.query().filter().first.return_value = self.user
        
        # Default weather
        self.weather = {"temp": 25, "condition": "clear"}

    def test_recommend_with_no_suitable_formal_items(self):
        """Test that casual items are used when no formal items are available for a formal occasion"""
        # Inventory: 1 Casual Top, 1 Casual Bottom, 1 Casual Shoes
        items = [
            ClothingItem(id=1, type=ClothingTypeEnum.TOP, occasion=OccasionEnum.CASUAL, user_id=1, category_label="Áo phông"),
            ClothingItem(id=2, type=ClothingTypeEnum.BOTTOM, occasion=OccasionEnum.CASUAL, user_id=1, category_label="Quần short"),
            ClothingItem(id=3, type=ClothingTypeEnum.SHOES, occasion=OccasionEnum.CASUAL, user_id=1, category_label="Giày thể thao")
        ]
        self.db.query().filter().all.return_value = items
        
        recommendations = self.engine.recommend(self.db, self.user_id, self.weather, OccasionEnum.FORMAL)
        
        self.assertGreaterEqual(len(recommendations), 1)
        # Should have picked the casual items since no formal ones exist
        self.assertEqual(len(recommendations[0]["items"]), 3)
        print(f"Test 1 (Relaxation) Passed: Found {len(recommendations)} outfits.")

    def test_recommend_returns_up_to_3_outfits(self):
        """Test that the engine returns 3 variations when plenty of items exist"""
        # Inventory: 5 pairs of everything (Casual)
        items = []
        for i in range(5):
            items.append(ClothingItem(id=10+i, type=ClothingTypeEnum.TOP, occasion=OccasionEnum.CASUAL, user_id=1))
            items.append(ClothingItem(id=20+i, type=ClothingTypeEnum.BOTTOM, occasion=OccasionEnum.CASUAL, user_id=1))
            items.append(ClothingItem(id=30+i, type=ClothingTypeEnum.SHOES, occasion=OccasionEnum.CASUAL, user_id=1))
        
        self.db.query().filter().all.return_value = items
        
        recommendations = self.engine.recommend(self.db, self.user_id, self.weather, OccasionEnum.CASUAL)
        
        self.assertEqual(len(recommendations), 3)
        print(f"Test 2 (Multi-outfit) Passed: Found {len(recommendations)} outfits.")

    def test_recommend_with_minimal_inventory(self):
        """Test fallback when items are limited"""
        # Only 1 top and 1 bottom
        items = [
            ClothingItem(id=1, type=ClothingTypeEnum.TOP, occasion=OccasionEnum.CASUAL, user_id=1),
            ClothingItem(id=2, type=ClothingTypeEnum.BOTTOM, occasion=OccasionEnum.CASUAL, user_id=1)
        ]
        self.db.query().filter().all.return_value = items
        
        recommendations = self.engine.recommend(self.db, self.user_id, self.weather, OccasionEnum.CASUAL)
        
        self.assertGreaterEqual(len(recommendations), 1)
        print(f"Test 3 (Fallback) Passed: Found {len(recommendations)} outfits with minimal inventory.")

if __name__ == "__main__":
    unittest.main()
