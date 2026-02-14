import requests
from app.core.config import settings

class WeatherService:
    BASE_URL = "https://api.openweathermap.org/data/2.5/weather"
    
    def __init__(self, api_key: str):
        self.api_key = api_key

    def get_current_weather(self, lat: float, lon: float):
        """
        Fetches current weather data and 3-day forecast from Open-Meteo.
        """
        location_name = "Vị trí của bạn"
        try:
            # Reverse geocoding using Nominatim
            geo_url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}&zoom=10&addressdetails=1"
            geo_resp = requests.get(geo_url, headers={'User-Agent': 'OutfitAI/1.0'}, timeout=3)
            if geo_resp.ok:
                geo_data = geo_resp.json()
                address = geo_data.get("address", {})
                location_name = address.get("city") or address.get("town") or address.get("village") or address.get("province") or address.get("state") or "Vị trí của bạn"
        except:
            pass

        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "current_weather": "true",
            "daily": "weathercode,temperature_2m_max,temperature_2m_min",
            "timezone": "auto"
        }

        try:
            response = requests.get(url, params=params, timeout=5, verify=False)
            response.raise_for_status()
            data = response.json()
            
            # Extract current info
            current = data["current_weather"]
            curr_temp = current["temperature"]
            curr_code = current["weathercode"]
            curr_condition = self._map_weather_code(curr_code)
            
            # Extract forecast (next 3 days, starting from tomorrow)
            daily = data["daily"]
            forecast = []
            for i in range(1, 4): # Start from tomorrow (index 1)
                forecast.append({
                    "day": i,
                    "max_temp": daily["temperature_2m_max"][i],
                    "min_temp": daily["temperature_2m_min"][i],
                    "condition": self._map_weather_code(daily["weathercode"][i])
                })
            
            return {
                "temp": curr_temp,
                "condition": curr_condition,
                "location": location_name,
                "description": f"Hiện tại {curr_condition.lower()}",
                "forecast": forecast
            }
        except Exception as e:
            print(f"Weather API Error: {e}")
            # Fallback
            return {
                "temp": 25.0, 
                "condition": "Trời quang", 
                "location": location_name, 
                "description": "Dữ liệu mẫu (mất kết nối)",
                "forecast": []
            }

    def _map_weather_code(self, code: int) -> str:
        if code <= 3: return "Trời quang"
        if code <= 48: return "Có mây" 
        if code <= 55: return "Mưa nhỏ"
        if code <= 67: return "Mưa lớn"
        if code <= 77: return "Tuyết"
        if code <= 82: return "Mưa rào"
        if code <= 99: return "Giông bão"
        return "Trời quang"

# Singleton instance
weather_service = WeatherService(settings.OPENWEATHER_API_KEY)
