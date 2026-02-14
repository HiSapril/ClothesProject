import requests
import os

token = "PASTE_TOKEN_HERE_LATER_IF_NEEDED"
# But I can't easily get the JWT token. 
# I'll just check if the endpoint is accessible and if it sees the token.

# Actually, I'll create a script that runs INSIDE the app context to debug.
import sys
sys.path.append(os.getcwd())
from app.services.calendar_service import calendar_service

print(f"TOKEN_FILE path: {calendar_service.TOKEN_FILE}")
print(f"Exists: {os.path.exists(calendar_service.TOKEN_FILE)}")

try:
    events = calendar_service.get_upcoming_events_summary()
    print(f"Events found: {len(events)}")
    for e in events:
        print(f"- {e['title']} at {e['time']}")
except Exception as e:
    print(f"Error fetching events: {e}")
