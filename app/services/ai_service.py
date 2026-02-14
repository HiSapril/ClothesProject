import io
import os
import certifi

# Fix for model download SSL verification
os.environ['SSL_CERT_FILE'] = certifi.where()
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()

import numpy as np
from PIL import Image
from rembg import remove
from sklearn.cluster import KMeans
from collections import Counter
import torch
from torchvision import models, transforms
import cv2

# --- 1. Background Removal ---
def remove_background(image_bytes: bytes) -> bytes:
    """
    Removes background using U-2-Net (via rembg).
    Returns PNG bytes with alpha channel.
    """
    output_data = remove(image_bytes)
    return output_data

# --- 2. Feature Extraction ---

# A. Color Extraction (K-Means)
def get_dominant_color(image: Image.Image, k=3) -> str:
    """
    Extracts the most dominant color from the image (ignoring transparent background).
    Returns Hex code (e.g., #FFFFFF).
    """
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

# B. Classification (ResNet-50)
# Load model once at startup (Global)
# Note: In production, consider loading lazily or serving via TFServing/TorchServe
# For this demo, we use a pretrained ResNet and map ImageNet classes to our categories roughly
# Or ideally, finetuned on DeepFashion. Here we simulate "Concept" code with standard ResNet.

weights = models.ResNet50_Weights.DEFAULT
model = models.resnet50(weights=weights)
model.eval()

preprocess = weights.transforms()

# Simulating mapping for demo purposes (ImageNet labels are distinct from "Jeans", "T-shirt")
# In a real scenario, use a specific model trained on FashionMNIST or DeepFashion.
# For now, we will assume the User inputs the category OR we implement a mock classifier 
# if we don't have the specific weights ready to download.
# Let's write the code structure for inference.

def classify_apparel(image: Image.Image) -> str:
    """
    Uses ResNet50 to predict class.
    Note: Standard ImageNet classes (1000) contain some apparel like 'jersey', 'jean', 'clog'.
    Returns the raw label from ImageNet.
    """
    # Convert to RGB if RGBA
    if image.mode != "RGB":
        image = image.convert("RGB")
        
    input_tensor = preprocess(image)
    input_batch = input_tensor.unsqueeze(0) 

    with torch.no_grad():
        output = model(input_batch)
    
    probabilities = torch.nn.functional.softmax(output[0], dim=0)
    
    # Get top class
    top_prob, top_catid = torch.topk(probabilities, 1)
    category_name = weights.meta["categories"][top_catid[0].item()]
    
    return category_name

def analyze_image(image_bytes: bytes):
    """
    Pipeline: BG Removal -> Color -> Classification
    """
    # 1. BG Removal
    clean_bytes = remove_background(image_bytes)
    clean_image = Image.open(io.BytesIO(clean_bytes))
    
    # 2. Color
    hex_color = get_dominant_color(clean_image)
    
    # 3. Classify (using original logic or clean image)
    # Using clean image might miss context, but reduces background noise.
    # Let's use clean image for shape focus.
    category = classify_apparel(clean_image)
    
    return {
        "processed_image": clean_bytes,
        "color_hex": hex_color,
        "category_raw": category
    }
