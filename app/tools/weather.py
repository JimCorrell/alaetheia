"""
Aletheia — Weather Tool
Uses Open-Meteo (free, no API key required).
"""
import httpx

_GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
_FORECAST_URL  = "https://api.open-meteo.com/v1/forecast"

_WMO_CODES: dict[int, str] = {
    0: "Clear sky",
    1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Icy fog",
    51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
    80: "Slight rain showers", 81: "Moderate rain showers", 82: "Heavy rain showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail", 99: "Thunderstorm with heavy hail",
}

TOOL_SCHEMA = {
    "type": "object",
    "properties": {
        "location": {
            "type": "string",
            "description": "City name, e.g. 'Chicago' or 'London, UK'",
        },
        "units": {
            "type": "string",
            "enum": ["fahrenheit", "celsius"],
            "description": "Temperature units. Defaults to fahrenheit.",
        },
    },
    "required": ["location"],
}


async def get_weather(args: dict) -> dict:
    location: str = args.get("location", "")
    units: str = args.get("units", "fahrenheit")

    async with httpx.AsyncClient(timeout=10.0) as client:
        geo = await client.get(
            _GEOCODING_URL,
            params={"name": location, "count": 1, "language": "en", "format": "json"},
        )
        geo.raise_for_status()
        results = geo.json().get("results")
        if not results:
            return {"error": f"Location '{location}' not found."}

        r = results[0]
        lat, lon = r["latitude"], r["longitude"]
        parts = [r["name"], r.get("admin1", ""), r.get("country", "")]
        display = ", ".join(p for p in parts if p)

        wx = await client.get(
            _FORECAST_URL,
            params={
                "latitude": lat,
                "longitude": lon,
                "current": (
                    "temperature_2m,apparent_temperature,"
                    "relative_humidity_2m,wind_speed_10m,weather_code"
                ),
                "temperature_unit": units,
                "wind_speed_unit": "mph" if units == "fahrenheit" else "kmh",
                "timezone": "auto",
            },
        )
        wx.raise_for_status()
        c = wx.json()["current"]

    unit_sym = "°F" if units == "fahrenheit" else "°C"
    wind_sym = "mph" if units == "fahrenheit" else "km/h"

    return {
        "location": display,
        "conditions": _WMO_CODES.get(c["weather_code"], "Unknown"),
        "temperature": f"{c['temperature_2m']}{unit_sym}",
        "feels_like": f"{c['apparent_temperature']}{unit_sym}",
        "humidity": f"{c['relative_humidity_2m']}%",
        "wind": f"{c['wind_speed_10m']} {wind_sym}",
    }
