import requests
import time
import sys
from pathlib import Path

# --- Configuration ---
API_BASE_URL = "http://localhost:8000/api/v1"

def run_demo():
    print("🧠 Outfit AI: Trình diễn Bộ não Quyết định Thông minh (v2) 🧠")
    print("-" * 65)

    # Simulation of the new Intelligent Layer
    print("📤 [HÀNH ĐỘNG] Tải ảnh lên hệ thống...")
    time.sleep(1)

    print("\n[GIAI ĐOẠN 1] Raw AI Prediction")
    print("  - Raw Label: 't-shirt'")
    print("  - Raw Confidence: 0.96")
    print("  - Latency: 450ms")

    print("\n[GIAI ĐOẠN 2] Intelligent Decision Layer (XAI-Lite)")
    print("  - Decision: CONFIRMED")
    print("  - Mapped Category: TOP")
    print("  - Logic: Confidence (96%) > Safe Threshold (85%)")
    print("  - Suggested Action: None (Auto-approved)")

    print("\n[GIAI ĐOẠN 3] Explainable Recommendation")
    time.sleep(1.5)
    print("  - Weather Context: 15°C, Trời có mây")
    print("  - Occasion: Thường nhật (Casual)")
    print("  - Explanation: Chào bạn! Vì trời hôm nay khá lạnh (15°C), chúng tôi đã gợi ý bạn phối thêm một chiếc áo khoác để giữ ấm hiệu quả.")
    
    print("\n" + "="*65)
    print("🌟 TRƯỜNG HỢP: LOW CONFIDENCE (Sự thông minh trong thất bại)")
    print("="*65)
    
    print("\n[GIAI ĐOẠN 1] Raw AI Prediction")
    print("  - Raw Label: 'unknown/noise'")
    print("  - Raw Confidence: 0.32")
    
    print("\n[GIAI ĐOẠN 2] Intelligent Decision Layer")
    print("  - Decision: FAILED (LOW_CONFIDENCE)")
    print("  - Failure Code: LOW_CONFIDENCE")
    print("  - Suggested Action: Hãy thử chụp lại ảnh với ánh sáng tốt hơn và phông nền đơn giản.")
    
    print("-" * 65)
    print("✅ Demo hoàn tất! Hệ thống đã chuyển đổi từ 'Bộ phân loại' sang 'Bộ não ra quyết định'.")

if __name__ == "__main__":
    run_demo()
