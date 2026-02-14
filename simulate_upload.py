import requests
import os

def test_upload_accessory():
    url = "http://localhost:8000/api/v1/items/upload"
    # Create a dummy image if not exists or use an existing one
    image_path = "test_image.png"
    if not os.path.exists(image_path):
        from PIL import Image
        img = Image.new('RGB', (100, 100), color = (73, 109, 137))
        img.save(image_path)
    
    files = {'file': open(image_path, 'rb')}
    data = {'user_id': 1}
    
    try:
        response = requests.post(url, files=files, data=data)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_upload_accessory()
