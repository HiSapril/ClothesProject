from app.services.ai_service import analyze_image
import os

def test_ai():
    print("Starting AI test...")
    file_path = "test_image.png"
    
    if not os.path.exists(file_path):
        print(f"File {file_path} not found.")
        return

    with open(file_path, "rb") as f:
        content = f.read()
    
    try:
        print("Calling analyze_image...")
        result = analyze_image(content)
        print("Success!")
        print("Category:", result.get("category_raw"))
        print("Color:", result.get("color_hex"))
    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ai()
