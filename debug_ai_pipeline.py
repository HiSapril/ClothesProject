import io
from PIL import Image
from app.services.ai_service import analyze_image
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_ai")

def test_ai():
    # Create a dummy image
    img = Image.new('RGB', (100, 100), color = (73, 109, 137))
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_bytes = img_byte_arr.getvalue()

    print("Starting AI test...")
    try:
        print("Calling analyze_image...")
        results = analyze_image(img_bytes)
        print("SUCCESS:", results)
    except Exception as e:
        print("FAILED:", str(e))
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ai()
