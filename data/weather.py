import requests
from datetime import date

LATITUDE = 37.7749
LONGITUDE = -122.4194

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

CITIES = {
    "San Francisco, CA": (37.7749, -122.4194),
    "Phoenix, AZ":       (33.4484, -112.0740),
    "Austin, TX":        (30.2672,  -97.7431),
    "Chicago, IL":       (41.8781,  -87.6298),
    "Miami, FL":         (25.7617,  -80.1918),
    "Denver, CO":        (39.7392, -104.9903),
    "Seattle, WA":       (47.6062, -122.3321),
    "New York, NY":      (40.7128,  -74.0060),
    "Los Angeles, CA":   (34.0522, -118.2437),
    "London, UK":        (51.5074,   -0.1278),
    "Berlin, Germany":   (52.5200,   13.4050),
    "Sydney, Australia": (-33.8688, 151.2093),
}


def fetch_hourly_weather(lat: float = LATITUDE, lon: float = LONGITUDE) -> list[dict]:
    """Fetch today's hourly weather from Open-Meteo (free, no API key required).

    Returns a list of 24 dicts, one per hour (index 0 = midnight).
    """
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "temperature_2m,cloudcover,windspeed_10m,direct_radiation",
        "forecast_days": 1,
        "timezone": "auto",
    }

    response = requests.get(OPEN_METEO_URL, params=params, timeout=10)
    response.raise_for_status()
    raw = response.json()["hourly"]

    hours = []
    for i in range(24):
        hours.append(
            {
                "temperature_2m": raw["temperature_2m"][i],
                "cloudcover": raw["cloudcover"][i],
                "windspeed_10m": raw["windspeed_10m"][i],
                "direct_radiation": raw["direct_radiation"][i],
            }
        )
    return hours


def get_simulated_weather(hour: int) -> dict:
    """Fallback: return a synthetic weather profile for a typical sunny California day."""
    import math

    # Temperature: cool morning, warm afternoon
    temp = 15 + 10 * math.sin(math.pi * (hour - 6) / 12) if 6 <= hour <= 18 else 15

    # Solar radiation peaks at noon
    if 6 <= hour <= 19:
        radiation = max(0, 800 * math.sin(math.pi * (hour - 6) / 13))
    else:
        radiation = 0

    # Cloud cover: partly cloudy in afternoon
    cloudcover = 10 if hour < 14 else 35

    # Wind picks up in afternoon
    windspeed = 3 + 5 * (hour / 24)

    return {
        "temperature_2m": round(temp, 1),
        "cloudcover": round(cloudcover, 1),
        "windspeed_10m": round(windspeed, 1),
        "direct_radiation": round(radiation, 1),
    }
