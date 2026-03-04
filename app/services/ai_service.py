import io
import os
import certifi
import numpy as np
import logging
from PIL import Image
from rembg import remove
from sklearn.cluster import KMeans
from collections import Counter
import torch
from torchvision import models, transforms
import cv2
from app.core.config import settings

# Fix for model download SSL verification
os.environ['SSL_CERT_FILE'] = certifi.where()
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()

logger = logging.getLogger("app")

# --- 1. Background Removal ---
def remove_background(image_bytes: bytes) -> bytes:
    """
    Removes background using U-2-Net (via rembg).
    Returns PNG bytes with alpha channel.
    """
    logger.info("Running background removal")
    try:
        output_data = remove(image_bytes)
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

# B. Classification (ResNet-50)
# Use IMAGENET1K_V1 for consistency with taxonomy mapping
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
weights = models.ResNet50_Weights.IMAGENET1K_V1
model = models.resnet50(weights=weights)
model.eval()
model.to(device)

preprocess = weights.transforms()

def classify_apparel(image: Image.Image) -> dict:
    """
    Uses ResNet50 to predict class.
    Returns a dict with 'label' (raw name) and 'confidence' (probability).
    """
    logger.info("Running apparel classification")
    try:
        # Convert to RGB if RGBA
        if image.mode != "RGB":
            image = image.convert("RGB")
            
        input_tensor = preprocess(image)
        input_batch = input_tensor.unsqueeze(0).to(device)

        with torch.no_grad():
            output = model(input_batch)
        
        probabilities = torch.nn.functional.softmax(output[0], dim=0)
        
        # Get top class
        top_prob, top_catid = torch.topk(probabilities, 1)
        category_name = weights.meta["categories"][top_catid[0].item()]
        confidence = float(top_prob[0].item())
        
        logger.info(f"Classification result: {category_name} ({confidence:.2f})")
        
        return {
            "label": category_name,
            "confidence": confidence
        }
    except Exception as e:
        logger.error(f"Classification failed: {e}", exc_info=True)
        return {"label": "unknown", "confidence": 0.0}

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
    
    # 3. Classify
    classification = classify_apparel(clean_image)
    
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
