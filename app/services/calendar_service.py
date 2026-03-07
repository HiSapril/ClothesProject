import os
import datetime
import json
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from app.db.models import OccasionEnum

# Use absolute paths for production-like reliability
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CLIENT_SECRETS_FILE = os.path.join(BASE_DIR, "credentials.json")
TOKEN_FILE = os.path.join(BASE_DIR, "token.json")

SCOPES = [
    'https://www.googleapis.com/auth/calendar.events',
    'https://www.googleapis.com/auth/calendar.events.readonly',
    'openid',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile'
]

class CalendarService:
    def __init__(self):
        self.SCOPES = SCOPES
        self.CLIENT_SECRETS_FILE = CLIENT_SECRETS_FILE
        self.TOKEN_FILE = TOKEN_FILE

    def get_calendar_flow(self, redirect_uri: str):
        if not os.path.exists(self.CLIENT_SECRETS_FILE):
            print(f"DEBUG: Missing {self.CLIENT_SECRETS_FILE}")
            return None
        return Flow.from_client_secrets_file(
            self.CLIENT_SECRETS_FILE,
            scopes=self.SCOPES,
            redirect_uri=redirect_uri
        )

    def get_user_info(self, creds):
        """Fetch user profile from Google"""
        service = build('oauth2', 'v2', credentials=creds)
        return service.userinfo().get().execute()

    def get_calendar_service(self, token_json: str = None):
        """Build service from token JSON string"""
        if not token_json:
            return None
            
        try:
            creds = Credentials.from_authorized_user_info(json.loads(token_json), self.SCOPES)
            
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    try:
                        creds.refresh(Request())
                        # Note: The caller must save the refreshed token back to DB
                        return build('calendar', 'v3', credentials=creds), creds.to_json()
                    except Exception as e:
                        print(f"DEBUG: Refresh failed: {e}")
                        return None, None
                else:
                    return None, None
            
            return build('calendar', 'v3', credentials=creds), None
        except Exception as e:
            print(f"DEBUG: Error building service: {e}")
            return None, None

    def get_upcoming_events(self, token_json: str, max_results=10):
        service, new_token = self.get_calendar_service(token_json)
        if not service:
            return [], None
        
        # Use start of TODAY (UTC) so events created for today are always included
        today_start = datetime.datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        time_min = today_start.isoformat() + 'Z'
        events_result = service.events().list(
            calendarId='primary', timeMin=time_min,
            maxResults=max_results, singleEvents=True,
            orderBy='startTime'
        ).execute()
        return events_result.get('items', []), new_token

    def get_upcoming_events_summary(self, token_json: str, max_results=10):
        """Fetch formatted summary of upcoming events"""
        try:
            events, new_token = self.get_upcoming_events(token_json, max_results=max_results)
            summary_list = []
            
            for event in events:
                start_full = event['start'].get('dateTime', event['start'].get('date'))
                # Extract date (YYYY-MM-DD -> DD/MM)
                date_part = start_full.split('T')[0]
                try:
                    dt_obj = datetime.date.fromisoformat(date_part)
                    formatted_date = dt_obj.strftime("%d/%m")
                except:
                    formatted_date = ""

                time_part = "Cả ngày"
                if 'T' in start_full:
                    # Handle timezone offset if present (+07:00)
                    time_part = start_full.split('T')[1][:5]
                    
                summary_list.append({
                    "id": event.get('id'),
                    "title": event.get('summary', 'Sự kiện không tên'),
                    "date": formatted_date,
                    "time": time_part,
                    "occasion": self.map_event_to_occasion(event.get('summary', ''))
                })
            # Deduplicate by event ID before returning
            seen_ids = set()
            unique_list = []
            for ev in summary_list:
                if ev['id'] not in seen_ids:
                    seen_ids.add(ev['id'])
                    unique_list.append(ev)
            return unique_list, new_token
        except Exception as e:
            print(f"DEBUG: Error in events summary: {e}")
            return [], None

    def map_event_to_occasion(self, summary: str) -> OccasionEnum:
        summary = (summary or "").lower()
        if any(kw in summary for kw in ['gym', 'sport', 'chạy', 'đá bóng', 'yoga', 'tập']):
            return OccasionEnum.SPORT
        if any(kw in summary for kw in ['meeting', 'họp', 'office', 'công ty', 'làm việc', 'phỏng vấn', 'đối tác']):
            return OccasionEnum.FORMAL
        if any(kw in summary for kw in ['party', 'tiệc', 'wedding', 'cưới', 'đi chơi', 'date', 'hẹn hò']):
            return OccasionEnum.CASUAL
        return OccasionEnum.CASUAL

    def get_events_for_range(self, token_json: str, start_time: datetime.datetime, end_time: datetime.datetime):
        """Fetch all events for a specific time range"""
        service, new_token = self.get_calendar_service(token_json)
        if not service:
            return [], None
            
        # Ensure times have Z suffix for Google API if they don't have offset
        t_min = start_time.isoformat()
        if 'Z' not in t_min and '+' not in t_min: t_min += 'Z'
        t_max = end_time.isoformat()
        if 'Z' not in t_max and '+' not in t_max: t_max += 'Z'

        events_result = service.events().list(
            calendarId='primary', 
            timeMin=t_min,
            timeMax=t_max,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        return events_result.get('items', []), new_token

    def get_events_for_month(self, token_json: str, year: int, month: int):
        """Fetch all events for a specific month"""
        # Start of month
        import calendar
        start_time = datetime.datetime(year, month, 1, 0, 0, 0)
        # End of month
        last_day = calendar.monthrange(year, month)[1]
        end_time = datetime.datetime(year, month, last_day, 23, 59, 59)
        
        events, new_token = self.get_events_for_range(token_json, start_time, end_time)
        
        formatted_events = []
        for event in events:
            start_str = event['start'].get('dateTime', event['start'].get('date'))
            date_only = start_str.split('T')[0]
            
            formatted_events.append({
                'id': event['id'],
                'summary': event.get('summary', 'Sự kiện không tên'),
                'date': date_only,
                'time': start_str.split('T')[1][:5] if 'T' in start_str else "Cả ngày",
                'occasion': self.map_event_to_occasion(event.get('summary', ''))
            })
        return formatted_events, new_token

    def get_events_for_day(self, token_json: str, target_date: datetime.date):
        """
        Fetch all events for a specific day
        Returns formatted events with id, summary, times, and occasion
        """
        # Create start and end times for the target day in Vietnam timezone
        start_time = datetime.datetime.combine(target_date, datetime.time.min)
        end_time = datetime.datetime.combine(target_date, datetime.time.max)
        
        # Get events for the day
        events, new_token = self.get_events_for_range(token_json, start_time, end_time)
        
        # Format events with occasion mapping
        formatted_events = []
        for event in events:
            start_str = event['start'].get('dateTime', event['start'].get('date'))
            end_str = event['end'].get('dateTime', event['end'].get('date'))
            
            formatted_events.append({
                'id': event['id'],
                'summary': event.get('summary', 'Sự kiện không tên'),
                'start_time': start_str,
                'end_time': end_str,
                'occasion': self.map_event_to_occasion(event.get('summary', '')),
                'description': event.get('description', '')
            })
        
        return formatted_events, new_token
    
    def get_event_by_id(self, token_json: str, event_id: str):
        """Fetch a specific event by its ID"""
        service, new_token = self.get_calendar_service(token_json)
        if not service:
            return None, None
            
        try:
            event = service.events().get(calendarId='primary', eventId=event_id).execute()
            return {
                'id': event['id'],
                'summary': event.get('summary', 'Sự kiện không tên'),
                'start_time': event['start'].get('dateTime', event['start'].get('date')),
                'end_time': event['end'].get('dateTime', event['end'].get('date')),
                'occasion': self.map_event_to_occasion(event.get('summary', '')),
                'description': event.get('description', '')
            }, new_token
        except Exception as e:
            print(f"Error fetching event {event_id}: {e}")
            return None, new_token


    def create_event(self, token_json: str, event_data: dict):
        """
        Create a new event
        event_data: {summary, location, description, start_time, end_time}
        """
        service, new_token = self.get_calendar_service(token_json)
        if not service:
            return None, None
            
        event = {
            'summary': event_data['summary'],
            'location': event_data.get('location', ''),
            'description': event_data.get('description', ''),
            'start': {
                'dateTime': event_data['start_time'], # ISO format
                'timeZone': 'Asia/Ho_Chi_Minh',
            },
            'end': {
                'dateTime': event_data['end_time'],
                'timeZone': 'Asia/Ho_Chi_Minh',
            },
        }
        
        created_event = service.events().insert(calendarId='primary', body=event).execute()
        return created_event, new_token

    def update_event(self, token_json: str, event_id: str, event_data: dict):
        """Edit an existing event"""
        service, new_token = self.get_calendar_service(token_json)
        if not service:
            return None, None
            
        event = service.events().get(calendarId='primary', eventId=event_id).execute()
        
        if 'summary' in event_data: event['summary'] = event_data['summary']
        if 'location' in event_data: event['location'] = event_data['location']
        if 'description' in event_data: event['description'] = event_data['description']
        if 'start_time' in event_data: event['start']['dateTime'] = event_data['start_time']
        if 'end_time' in event_data: event['end']['dateTime'] = event_data['end_time']
        
        updated_event = service.events().update(calendarId='primary', eventId=event_id, body=event).execute()
        return updated_event, new_token

    def delete_event(self, token_json: str, event_id: str):
        """Delete an event"""
        service, new_token = self.get_calendar_service(token_json)
        if not service:
            return False, None
            
        service.events().delete(calendarId='primary', eventId=event_id).execute()
        return True, new_token

    def get_current_occasion_from_calendar(self, token_json: str):
        events, new_token = self.get_upcoming_events(token_json, max_results=1)
        if not events:
            return None, new_token
            
        event = events[0]
        start_str = event['start'].get('dateTime', event['start'].get('date'))
        try:
            # Handle both Z and +HH:MM formats
            dt_str = start_str.replace('Z', '+00:00')
            start_time = datetime.datetime.fromisoformat(dt_str)
        except:
            return None, new_token
            
        now = datetime.datetime.now(datetime.timezone.utc)
        
        diff = start_time - now
        if -datetime.timedelta(hours=1) < diff < datetime.timedelta(hours=2):
            return {
                "occasion": self.map_event_to_occasion(event.get('summary', '')),
                "summary": event.get('summary', 'Sự kiện sắp tới')
            }, new_token
        return None, new_token

# Singleton instance
calendar_service = CalendarService()
