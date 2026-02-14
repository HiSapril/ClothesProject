import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

print("=== Testing Event Selection Endpoints ===\n")

# Note: You'll need a valid auth token
print("1. Test GET /calendar/events/day endpoint")
print("   Example: GET /calendar/events/day?year=2026&month=1&day=15")
print("   Expected: Returns list of events for that day\n")

print("2. Test POST /recommend/with-event endpoint")
print("   Example body: {lat, lon, user_id, event_id}")
print("   Expected: Returns outfit recommendations\n")

print("3. Test POST /recommend with selected_event_id")
print("   Example body: {lat, lon, user_id, selected_event_id}")
print("   Expected: Returns outfit recommendations\n")

print("=" * 50)
print("\nTo properly test, you need:")
print("- Valid authentication token")
print("- Google Calendar connected")
print("- Some events in your calendar")
print("\nPlease describe what error you're seeing:")
print("- Is it a 401 (unauthorized)?")
print("- Is it a 404 (endpoint not found)?")
print("- Is it a 500 (server error)?")
print("- Is the data not showing up correctly?")
print("- Is there a JavaScript error in browser console?")
