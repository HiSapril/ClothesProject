import certifi
import os
import requests

print(f"Certifi Path: {certifi.where()}")
print(f"Exists: {os.path.exists(certifi.where())}")

os.environ['SSL_CERT_FILE'] = certifi.where()
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()

try:
    resp = requests.get("https://www.google.com", timeout=5)
    print(f"HTTPS Request to Google: {resp.status_code} (Success)")
except Exception as e:
    print(f"HTTPS Request failed: {e}")
