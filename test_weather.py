from app.services.weather_service import weather_service

def test():
    print("Testing Weather Service...")
    w = weather_service.get_current_weather(21.0285, 105.8542)
    print("Result:", w)

if __name__ == "__main__":
    test()
