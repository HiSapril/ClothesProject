import io
import os
import certifi
import numpy as np
import logging
from PIL import Image
from rembg import remove, new_session
from sklearn.cluster import KMeans
from collections import Counter
import cv2
from app.core.config import settings
import requests
import json

# Initialize persistent session for rembg (avoids loading model on every call)
bg_session = new_session()

# Fix for model download SSL verification
os.environ['SSL_CERT_FILE'] = certifi.where()
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()

logger = logging.getLogger("app")

# --- 1. Background Removal ---
def remove_background(image_bytes: bytes) -> bytes:
    """
    Removes background using U-2-Net (via rembg).
    Returns PNG bytes with alpha channel.
    Optimized: Resizes large images to 800px max before processing.
    """
    logger.info("Running background removal")
    try:
        # Optimization: Resize for speed if image is too large
        img = Image.open(io.BytesIO(image_bytes))
        orig_size = img.size
        max_dim = 640 # Reduced from 800 for even more speed
        
        if max(orig_size) > max_dim:
            logger.info(f"Resizing image from {orig_size} for faster BG removal")
            img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
            buffered = io.BytesIO()
            img.save(buffered, format="PNG")
            image_bytes = buffered.getvalue()

        output_data = remove(image_bytes, session=bg_session)
        return output_data
    except Exception as e:
        logger.error(f"Background removal failed: {e}", exc_info=True)
        return image_bytes # Fallback to original

# --- 2. Feature Extraction ---

# A. Color Extraction (K-Means)
def get_dominant_color(image: Image.Image, k=3) -> str:
    """
    Extracts the most dominant color from the image (ignoring transparent background).
    Returns Hex code (e.g., #FFFFFF).
    """
    try:
        # Resize for speed
        image = image.resize((100, 100))
        img_np = np.array(image)
        
        # If RGBA, filter out transparent pixels
        if img_np.shape[2] == 4:
            mask = img_np[:, :, 3] > 0
            pixels = img_np[mask][:, :3] # Take only RGB of non-transparent
        else:
            pixels = img_np.reshape(-1, 3)

        if len(pixels) == 0:
            return "#000000"

        kmeans = KMeans(n_clusters=k, n_init=10)
        kmeans.fit(pixels)
        
        # Find most frequent cluster
        counts = Counter(kmeans.labels_)
        dominant_cluster = counts.most_common(1)[0][0]
        dominant_rgb = kmeans.cluster_centers_[dominant_cluster]
        
        # Convert to Hex
        return "#{:02x}{:02x}{:02x}".format(int(dominant_rgb[0]), int(dominant_rgb[1]), int(dominant_rgb[2]))
    except Exception as e:
        logger.error(f"Color extraction failed: {e}", exc_info=True)
        return "#000000"

# B. Classification (Gemini Vision API via OpenRouter)

import base64

def classify_apparel(image_bytes: bytes) -> dict:
    """
    Uses Google Gemini 2.5 Flash Vision via OpenRouter to predict class.
    Returns a dict with 'label' (e.g., TOP, BOTTOM, OUTERWEAR, FOOTWEAR) and 'confidence'.
    """
    logger.info("Running apparel classification via Gemini Vision API")
    
    if not settings.DEEPSEEK_API_KEY or "your_" in settings.DEEPSEEK_API_KEY:
        logger.warning("No API key found. Falling back to UNKNOWN.")
        return {"label": "UNKNOWN", "confidence": 0.0}

    try:
        # Resize image to save bandwidth and speed up API
        img = Image.open(io.BytesIO(image_bytes))
        img.thumbnail((512, 512), Image.Resampling.LANCZOS)
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        b64_img = base64.b64encode(buffered.getvalue()).decode("utf-8")
        
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}",
            "HTTP-Referer": "http://localhost:8000",
            "X-Title": "OutfitAI"
        }
        
        prompt = "Hãy nhìn bức ảnh món đồ thời trang này. Nó thuộc thể loại nào trong danh sách sau: TOP (Áo), BOTTOM (Quần, Chân váy), OUTERWEAR (Áo khoác ngoài), FOOTWEAR (Giày dép), FULL_BODY (Váy liền thân, Đầm), ACCESSORY (Phụ kiện). Chỉ in ra đúng duy nhất 1 từ tiếng Anh in hoa trong danh sách đó."
        
        payload = {
            "model": "google/gemini-2.5-flash",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64_img}"}}
                    ]
                }
            ],
            "temperature": 0.1,
            "max_tokens": 10
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=8.0)
        if response.status_code == 200:
            data = response.json()
            label = data["choices"][0]["message"]["content"].strip().upper()
            
            valid_labels = ["TOP", "BOTTOM", "OUTERWEAR", "FOOTWEAR", "FULL_BODY", "ACCESSORY"]
            for v in valid_labels:
                if v in label:
                    return {"label": v, "confidence": 0.99}
                    
            logger.warning(f"Unexpected vision output: {label}")
            return {"label": "UNKNOWN", "confidence": 0.5}
            
        else:
            logger.error(f"Vision API error: {response.text}")
            return {"label": "UNKNOWN", "confidence": 0.0}
            
    except Exception as e:
        logger.error(f"Classification failed: {e}", exc_info=True)
        return {"label": "UNKNOWN", "confidence": 0.0}

def enhance_classification_with_llm(raw_label: str, color_hex: str) -> dict:
    """
    Uses DeepSeek to enhance the deterministic label with an Occasion and a Style Tag.
    """
    if not settings.DEEPSEEK_API_KEY or "your_" in settings.DEEPSEEK_API_KEY:
        return {"occasion": "casual", "style_tag": raw_label}

    try:
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}",
            "HTTP-Referer": "http://localhost:8000",
            "X-Title": "OutfitAI"
        }
        
        category_vi_map = {
            "TOP": "Áo",
            "BOTTOM": "Quần hoặc Chân váy",
            "OUTERWEAR": "Áo khoác",
            "FOOTWEAR": "Giày dép",
            "FULL_BODY": "Váy liền thân",
            "ACCESSORY": "Phụ kiện"
        }
        vi_label = category_vi_map.get(raw_label.upper(), raw_label)
        
        prompt = f"Tôi có một món quần áo là '{vi_label}' màu {color_hex}.\n" \
                 f"1. Phân loại nó vào 1 trong 3 dịp sau: 'casual', 'formal', hoặc 'sport'.\n" \
                 f"2. Đặt một tên tiếng Việt hay, ngắn gọn kèm phong cách (Ví dụ: 'Áo khoác Thanh lịch', 'Giày Thể thao Năng động').\n" \
                 f"Chỉ trả về JSON hợp lệ với 2 key 'occasion' và 'style_tag'. Không giải thích gì thêm."
                 
        payload = {
            "model": "deepseek/deepseek-chat",
            "messages": [
                {"role": "system", "content": "You are a JSON-only fashion categorizer bot. Always output strictly valid JSON."},
                {"role": "user", "content": prompt}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.1,
            "max_tokens": 100
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=4.0)
        if response.status_code == 200:
            data = response.json()
            content = data["choices"][0]["message"]["content"].strip()
            # In case OpenRouter wrapper ignores response_format and adds markdown ticks
            if content.startswith("```json"):
                content = content[7:-3].strip()
            elif content.startswith("```"):
                content = content[3:-3].strip()
                
            parsed = json.loads(content)
            # Validate output
            occ = parsed.get("occasion", "casual").lower()
            if occ not in ["casual", "formal", "sport"]:
                occ = "casual"
            return {"occasion": occ, "style_tag": parsed.get("style_tag", raw_label)}
    except Exception as e:
        logger.warning(f"DeepSeek enhancement failed: {e}")
        
    return {"occasion": "casual", "style_tag": raw_label}

def analyze_image(image_bytes: bytes):
    """
    Pipeline: BG Removal -> Color -> Classification
    """
    logger.info("Starting image analysis pipeline")
    
    # 1. BG Removal
    clean_bytes = remove_background(image_bytes)
    clean_image = Image.open(io.BytesIO(clean_bytes))
    
    # 2. Color
    hex_color = get_dominant_color(clean_image)
    
    # 3. Classify (Now takes bytes of cleaned image)
    classification = classify_apparel(clean_bytes)
    
    import uuid
    filename = f"proc_{uuid.uuid4()}.png"
    processed_path = os.path.join(settings.PROCESSED_DIR, filename)
    with open(processed_path, "wb") as f:
        f.write(clean_bytes)

    return {
        "processed_image_path": processed_path,
        "color_hex": hex_color,
        "category_raw": classification["label"],
        "confidence": classification["confidence"],
        "raw_output": classification
    }
