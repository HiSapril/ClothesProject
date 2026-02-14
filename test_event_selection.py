"""
Test Script for Event Selection Feature
Tests the new calendar event selection endpoints
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000/api/v1"

# You need to have a valid token from logging in
# Replace this with your actual token
TOKEN = "your_token_here"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

def test_get_events_for_day():
    """Test getting events for a specific day"""
    print("\n=== Testing Get Events for Day ===")
    
    # Test with a future date
    today = datetime.now()
    url = f"{BASE_URL}/calendar/events/day"
    params = {
        "year": today.year,
        "month": today.month,
        "day": today.day
    }
    
    try:
        response = requests.get(url, params=params, headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Date: {data['date']}")
            print(f"Number of events: {len(data['events'])}")
            
            for i, event in enumerate(data['events'], 1):
                print(f"\nEvent {i}:")
                print(f"  ID: {event['id']}")
                print(f"  Summary: {event['summary']}")
                print(f"  Start: {event['start_time']}")
                print(f"  Occasion: {event['occasion']}")
                
            return data['events']
        else:
            print(f"Error: {response.text}")
            return []
    except Exception as e:
        print(f"Exception: {e}")
        return []

def test_event_recommendation(event_id):
    """Test getting recommendations for a specific event"""
    print("\n=== Testing Event-based Recommendation ===")
    
    url = f"{BASE_URL}/recommend/with-event"
    payload = {
        "lat": 10.762622,  # Ho Chi Minh City coordinates
        "lon": 106.660172,
        "user_id": 1,  # Replace with actual user ID
        "event_id": event_id
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Weather: {data['weather_summary']}")
            print(f"Occasion Context: {data['occasion_context']}")
            print(f"Number of outfit suggestions: {len(data['outfits'])}")
            
            for i, outfit in enumerate(data['outfits'], 1):
                print(f"\nOutfit {i}:")
                print(f"  Score: {outfit['score']}")
                print(f"  Items: {len(outfit['items'])}")
                if outfit.get('reason'):
                    print(f"  Reason: {outfit['reason']}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")

def test_regular_recommendation_with_event():
    """Test using selected_event_id in regular recommendation endpoint"""
    print("\n=== Testing Regular Recommendation with selected_event_id ===")
    
    # First get events
    events = test_get_events_for_day()
    
    if not events:
        print("No events found to test with")
        return
    
    url = f"{BASE_URL}/recommend"
    payload = {
        "lat": 10.762622,
        "lon": 106.660172,
        "user_id": 1,  # Replace with actual user ID
        "selected_event_id": events[0]['id']
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Weather: {data['weather_summary']}")
            print(f"Occasion Context: {data['occasion_context']}")
            print(f"Number of outfits: {len(data['outfits'])}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    print("Event Selection Feature Test")
    print("=" * 50)
    print("\nNote: Make sure to:")
    print("1. Update TOKEN variable with your actual auth token")
    print("2. Update user_id if needed")
    print("3. Have Google Calendar connected")
    print("4. Have some events in your calendar")
    
    # Run tests
    events = test_get_events_for_day()
    
    if events:
        # Test with first event
        print(f"\nUsing first event for recommendation test...")
        test_event_recommendation(events[0]['id'])
        
        # Test regular endpoint with event selection
        test_regular_recommendation_with_event()
    else:
        print("\nNo events found. Please add events to your calendar first.")
