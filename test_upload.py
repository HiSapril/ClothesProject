import requests

def test_upload():
    url = "http://127.0.0.1:8000/api/v1/items/upload"
    files = {'file': open('test_image.png', 'rb')}
    data = {'user_id': 1}
    
    try:
        response = requests.post(url, files=files, data=data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_upload()
