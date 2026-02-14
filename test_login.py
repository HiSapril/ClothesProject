import requests

# Test the login endpoint
print("Testing /calendar/login endpoint...")
try:
    response = requests.get("http://localhost:8000/api/v1/calendar/login", allow_redirects=False)
    print(f"Status Code: {response.status_code}")
    print(f"Headers: {response.headers}")
    if 'location' in response.headers:
        print(f"Redirect URL: {response.headers['location'][:100]}...")
        print("\n✓ Login endpoint is working - redirects to Google OAuth")
    else:
        print("✗ No redirect found")
except Exception as e:
    print(f"✗ Error: {e}")

print("\n" + "="*50)
print("Note: Để test đầy đủ, bạn cần:")
print("1. Mở browser và truy cập: http://localhost:8000/api/v1/calendar/login")
print("2. Đăng nhập bằng tài khoản Google")
print("3. Kiểm tra xem có lỗi nào trong terminal uvicorn không")
