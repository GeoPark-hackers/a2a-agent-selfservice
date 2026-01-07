"""Weather tools for getting weather information."""

from .registry import register_tool


# Mock weather data - in production, replace with actual API calls
MOCK_WEATHER_DATA = {
    "new york": {"temp": 72, "condition": "Sunny", "humidity": 45},
    "london": {"temp": 55, "condition": "Cloudy", "humidity": 78},
    "tokyo": {"temp": 65, "condition": "Rainy", "humidity": 82},
    "paris": {"temp": 60, "condition": "Partly Cloudy", "humidity": 65},
    "sydney": {"temp": 78, "condition": "Sunny", "humidity": 55},
    "bogota": {"temp": 58, "condition": "Cloudy", "humidity": 72},
}


@register_tool()
def get_weather(city: str) -> str:
    """Get the current weather for a city.
    
    Args:
        city: The name of the city (e.g., "New York", "London", "Tokyo")
    
    Returns:
        A string describing the current weather conditions.
    """
    city_lower = city.lower()
    
    if city_lower in MOCK_WEATHER_DATA:
        data = MOCK_WEATHER_DATA[city_lower]
        return (
            f"Weather in {city}:\n"
            f"- Temperature: {data['temp']}°F\n"
            f"- Condition: {data['condition']}\n"
            f"- Humidity: {data['humidity']}%"
        )
    
    return f"Weather data not available for {city}. Try: New York, London, Tokyo, Paris, Sydney, or Bogota."


@register_tool()
def get_forecast(city: str, days: int = 3) -> str:
    """Get a weather forecast for a city.
    
    Args:
        city: The name of the city
        days: Number of days to forecast (1-7)
    
    Returns:
        A string with the weather forecast.
    """
    city_lower = city.lower()
    
    if city_lower not in MOCK_WEATHER_DATA:
        return f"Forecast not available for {city}."
    
    days = min(max(days, 1), 7)  # Clamp between 1 and 7
    
    # Mock forecast based on current conditions
    base = MOCK_WEATHER_DATA[city_lower]
    forecast_lines = [f"{days}-day forecast for {city}:"]
    
    for i in range(days):
        temp_variation = (i % 3 - 1) * 5  # Vary temperature slightly
        forecast_lines.append(
            f"- Day {i + 1}: {base['temp'] + temp_variation}°F, {base['condition']}"
        )
    
    return "\n".join(forecast_lines)
