from app.services.calendar_service import calendar_service
import os

def test_flow():
    print("Testing Google Flow construction...")
    try:
        redirect_uri = "http://localhost:8000/api/v1/calendar/callback"
        flow = calendar_service.get_calendar_flow(redirect_uri)
        if not flow:
            print("FAILED: Flow is None. Check credentials.json existence.")
            return
        
        print(f"Scopes being requested: {flow.scopes}")
        auth_url, _ = flow.authorization_url(prompt='consent')
        print(f"SUCCESS: Authorization URL generated: {auth_url[:50]}...")
    except Exception as e:
        print(f"FAILED with error: {e}")

if __name__ == "__main__":
    test_flow()
