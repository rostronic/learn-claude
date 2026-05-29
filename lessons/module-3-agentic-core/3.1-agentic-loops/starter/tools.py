"""Dummy tools and their Claude tool-use schemas for chapter 3.1.

The schemas (WEATHER_TOOL, TIME_TOOL) are the shape Claude's API expects in the
`tools` parameter of client.messages.create(). The functions (get_weather,
get_time) are what your tool_handler will dispatch to.
"""

from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def get_weather(location: str) -> dict:
    """Pretend to look up the weather. Returns a fixed payload."""
    return {
        "location": location,
        "temperature_f": 68,
        "conditions": "partly cloudy",
        "humidity_pct": 55,
    }


def get_time(timezone: str) -> dict:
    """Return the current time in the given IANA timezone (e.g. 'Europe/Paris')."""
    try:
        now = datetime.now(ZoneInfo(timezone))
    except ZoneInfoNotFoundError:
        return {"error": f"unknown timezone: {timezone}"}
    return {
        "timezone": timezone,
        "iso": now.isoformat(timespec="seconds"),
    }


WEATHER_TOOL = {
    "name": "get_weather",
    "description": (
        "Look up the current weather for a city. Returns temperature in "
        "Fahrenheit, conditions, and humidity. Use when the user asks about "
        "weather, temperature, or whether they need an umbrella."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "City name, e.g. 'Paris' or 'San Francisco, CA'.",
            },
        },
        "required": ["location"],
    },
}

TIME_TOOL = {
    "name": "get_time",
    "description": (
        "Get the current local time in a given timezone. Use when the user "
        "asks 'what time is it in X' or needs to coordinate across timezones."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "timezone": {
                "type": "string",
                "description": "IANA timezone identifier, e.g. 'Europe/Paris', 'Asia/Tokyo', 'America/Los_Angeles'.",
            },
        },
        "required": ["timezone"],
    },
}
