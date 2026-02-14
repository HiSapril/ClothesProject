"""
Test if the new API endpoints are accessible
"""
import requests

BASE_URL = "http://localhost:8000"

def test_api_docs():
    """Check if API is running and get OpenAPI schema"""
    try:
        response = requests.get(f"{BASE_URL}/openapi.json")
        if response.status_code == 200:
            data = response.json()
            paths = data.get('paths', {})
            
            print("=== Checking API Endpoints ===\n")
            
            # Check for our new endpoints
            endpoints_to_check = [
                "/api/v1/calendar/events/day",
                "/api/v1/recommend/with-event",
                "/api/v1/recommend"
            ]
            
            for endpoint in endpoints_to_check:
                if endpoint in paths:
                    methods = list(paths[endpoint].keys())
                    print(f"✓ {endpoint} - Methods: {methods}")
                else:
                    print(f"✗ {endpoint} - NOT FOUND")
            
            # Show all calendar-related endpoints
            print("\n=== All Calendar Endpoints ===")
            for path in sorted(paths.keys()):
                if 'calendar' in path or 'recommend' in path:
                    methods = list(paths[path].keys())
                    print(f"  {path} - {methods}")
                    
        else:
            print(f"Error accessing API docs: {response.status_code}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_api_docs()
