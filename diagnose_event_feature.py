"""
Quick diagnostic script to check if the event selection endpoints work
"""
import sys
sys.path.append('.')

try:
    print("=== Checking Imports ===")
    from app.schemas import schemas
    print("✓ Schemas imported")
    
    # Check if new schemas exist
    if hasattr(schemas, 'DayEventItem'):
        print("✓ DayEventItem found")
    else:
        print("✗ DayEventItem NOT found")
    
    if hasattr(schemas, 'DayEventsResponse'):
        print("✓ DayEventsResponse found")
    else:
        print("✗ DayEventsResponse NOT found")
        
    if hasattr(schemas, 'EventRecommendationRequest'):
        print("✓ EventRecommendationRequest found")
    else:
        print("✗ EventRecommendationRequest NOT found")
    
    print("\n=== Checking Calendar Service ===")
    from app.services.calendar_service import calendar_service
    print("✓ Calendar service imported")
    
    # Check if new methods exist
    if hasattr(calendar_service, 'get_events_for_day'):
        print("✓ get_events_for_day method found")
    else:
        print("✗ get_events_for_day method NOT found")
        
    if hasattr(calendar_service, 'get_event_by_id'):
        print("✓ get_event_by_id method found")
    else:
        print("✗ get_event_by_id method NOT found")
    
    print("\n=== Checking RecommendationRequest Schema ===")
    # Create a test instance
    test_req = schemas.RecommendationRequest(
        lat=10.0,
        lon=106.0,
        user_id=1
    )
    print(f"✓ RecommendationRequest created: {test_req}")
    
    # Check if selected_event_id field exists
    if hasattr(test_req, 'selected_event_id'):
        print(f"✓ selected_event_id field exists (value: {test_req.selected_event_id})")
    else:
        print("✗ selected_event_id field NOT found")
    
    print("\n=== All checks completed ===")
    
except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()
