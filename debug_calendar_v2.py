import os
import datetime
import json
import traceback
import sys

# Ensure we can import from app
sys.path.append(os.getcwd())

from app.services.calendar_service import calendar_service

print(f"--- DIAGNOSTIC START ---")
print(f"Working Dir: {os.getcwd()}")
print(f"TOKEN_FILE path: {calendar_service.TOKEN_FILE}")
print(f"TOKEN_FILE exists: {os.path.exists(calendar_service.TOKEN_FILE)}")

if os.path.exists(calendar_service.TOKEN_FILE):
    try:
        print("Attempting to fetch events...")
        events = calendar_service.get_upcoming_events_summary()
        print(f"Success! Events found: {len(events)}")
        for e in events:
            print(f"- {e['title']} at {e['time']} ({e['occasion']})")
    except Exception as e:
        print(f"FAILED to fetch events.")
        traceback.print_exc()
else:
    print("TOKEN_FILE does not exist. Cannot fetch events.")

print(f"--- DIAGNOSTIC END ---")
