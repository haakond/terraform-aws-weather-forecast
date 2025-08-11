"""
Data transformation utilities for met.no API response parsing.

This module provides utilities to transform weather data from the Norwegian
Meteorological Institute API format into the application's internal data models.
"""

from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any
import logging

from weather_service.models import (
    CityWeatherData, WeatherForecast, Temperature, WeatherCondition,
    Coordinates, ValidationError
)
from weather_service.config import get_city_config

logger = logging.getLogger(__name__)


# Mapping from met.no weather symbols to our internal weather conditions
WEATHER_SYMBOL_MAPPING = {
    # Clear sky
    "clearsky_day": WeatherCondition.CLEAR_SKY,
    "clearsky_night": WeatherCondition.CLEAR_SKY,
    "clearsky_polartwilight": WeatherCondition.CLEAR_SKY,

    # Partly cloudy
    "fair_day": WeatherCondition.PARTLY_CLOUDY,
    "fair_night": WeatherCondition.PARTLY_CLOUDY,
    "fair_polartwilight": WeatherCondition.PARTLY_CLOUDY,
    "partlycloudy_day": WeatherCondition.PARTLY_CLOUDY,
    "partlycloudy_night": WeatherCondition.PARTLY_CLOUDY,
    "partlycloudy_polartwilight": WeatherCondition.PARTLY_CLOUDY,

    # Cloudy
    "cloudy": WeatherCondition.CLOUDY,

    # Rain
    "lightrain": WeatherCondition.LIGHT_RAIN,
    "lightrainshowers_day": WeatherCondition.LIGHT_RAIN,
    "lightrainshowers_night": WeatherCondition.LIGHT_RAIN,
    "lightrainshowers_polartwilight": WeatherCondition.LIGHT_RAIN,
    "rain": WeatherCondition.RAIN,
    "rainshowers_day": WeatherCondition.RAIN,
    "rainshowers_night": WeatherCondition.RAIN,
    "rainshowers_polartwilight": WeatherCondition.RAIN,
    "heavyrain": WeatherCondition.HEAVY_RAIN,
    "heavyrainshowers_day": WeatherCondition.HEAVY_RAIN,
    "heavyrainshowers_night": WeatherCondition.HEAVY_RAIN,
    "heavyrainshowers_polartwilight": WeatherCondition.HEAVY_RAIN,

    # Snow
    "lightsnow": WeatherCondition.LIGHT_SNOW,
    "lightsnowshowers_day": WeatherCondition.LIGHT_SNOW,
    "lightsnowshowers_night": WeatherCondition.LIGHT_SNOW,
    "lightsnowshowers_polartwilight": WeatherCondition.LIGHT_SNOW,
    "snow": WeatherCondition.SNOW,
    "snowshowers_day": WeatherCondition.SNOW,
    "snowshowers_night": WeatherCondition.SNOW,
    "snowshowers_polartwilight": WeatherCondition.SNOW,
    "heavysnow": WeatherCondition.HEAVY_SNOW,
    "heavysnowshowers_day": WeatherCondition.HEAVY_SNOW,
    "heavysnowshowers_night": WeatherCondition.HEAVY_SNOW,
    "heavysnowshowers_polartwilight": WeatherCondition.HEAVY_SNOW,

    # Mixed precipitation
    "lightrainandthunder": WeatherCondition.THUNDERSTORM,
    "rainandthunder": WeatherCondition.THUNDERSTORM,
    "heavyrainandthunder": WeatherCondition.THUNDERSTORM,
    "lightsnowandthunder": WeatherCondition.THUNDERSTORM,
    "snowandthunder": WeatherCondition.THUNDERSTORM,
    "heavysnowandthunder": WeatherCondition.THUNDERSTORM,

    # Fog
    "fog": WeatherCondition.FOG,
}


# Weather condition descriptions
WEATHER_DESCRIPTIONS = {
    WeatherCondition.CLEAR_SKY: "Clear sky",
    WeatherCondition.PARTLY_CLOUDY: "Partly cloudy",
    WeatherCondition.CLOUDY: "Cloudy",
    WeatherCondition.LIGHT_RAIN: "Light rain",
    WeatherCondition.RAIN: "Rain",
    WeatherCondition.HEAVY_RAIN: "Heavy rain",
    WeatherCondition.LIGHT_SNOW: "Light snow",
    WeatherCondition.SNOW: "Snow",
    WeatherCondition.HEAVY_SNOW: "Heavy snow",
    WeatherCondition.FOG: "Fog",
    WeatherCondition.THUNDERSTORM: "Thunderstorm",
    WeatherCondition.UNKNOWN: "Unknown conditions",
}


# Icon mapping for frontend display
WEATHER_ICONS = {
    WeatherCondition.CLEAR_SKY: "clear_day",
    WeatherCondition.PARTLY_CLOUDY: "partly_cloudy_day",
    WeatherCondition.CLOUDY: "cloudy",
    WeatherCondition.LIGHT_RAIN: "light_rain",
    WeatherCondition.RAIN: "rain",
    WeatherCondition.HEAVY_RAIN: "heavy_rain",
    WeatherCondition.LIGHT_SNOW: "light_snow",
    WeatherCondition.SNOW: "snow",
    WeatherCondition.HEAVY_SNOW: "heavy_snow",
    WeatherCondition.FOG: "fog",
    WeatherCondition.THUNDERSTORM: "thunderstorm",
    WeatherCondition.UNKNOWN: "unknown",
}


def parse_met_no_response(api_response: Dict[str, Any], city_id: str) -> CityWeatherData:
    """
    Parse met.no API response and convert to CityWeatherData.

    Args:
        api_response: Raw response from met.no API
        city_id: ID of the city this data belongs to

    Returns:
        CityWeatherData object with parsed weather information

    Raises:
        ValidationError: If API response is malformed or missing required data
    """
    try:
        # Get city configuration
        city_config = get_city_config(city_id)

        # Extract tomorrow's forecast
        tomorrow_forecast = extract_tomorrow_forecast(api_response)

        if not tomorrow_forecast:
            raise ValidationError(f"No forecast data available for tomorrow for city {city_id}")

        # Parse weather data
        weather_condition = map_weather_symbol(tomorrow_forecast.get("symbol_code", "unknown"))
        temperature_value = tomorrow_forecast.get("air_temperature", 0.0)
        humidity = tomorrow_forecast.get("relative_humidity")
        wind_speed = tomorrow_forecast.get("wind_speed")

        # Create temperature object
        temperature = Temperature(value=temperature_value, unit="celsius")

        # Create forecast object
        forecast = WeatherForecast(
            date=date.today() + timedelta(days=1),  # Tomorrow
            temperature=temperature,
            condition=weather_condition,
            description=WEATHER_DESCRIPTIONS[weather_condition],
            icon=WEATHER_ICONS[weather_condition],
            humidity=int(humidity) if humidity is not None else None,
            wind_speed=wind_speed
        )

        # Create complete weather data
        weather_data = CityWeatherData(
            city_id=city_config.id,
            city_name=city_config.name,
            country=city_config.country,
            coordinates=city_config.coordinates,
            forecast=forecast,
            last_updated=datetime.utcnow(),
            ttl=int((datetime.utcnow() + timedelta(hours=1)).timestamp())  # 1 hour TTL
        )

        return weather_data

    except Exception as e:
        logger.error(f"Error parsing met.no response for city {city_id}: {str(e)}")
        raise ValidationError(f"Failed to parse weather data for {city_id}: {str(e)}")


def extract_tomorrow_forecast(api_response: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Extract tomorrow's forecast from met.no API response.

    Args:
        api_response: Raw response from met.no API

    Returns:
        Dictionary with tomorrow's forecast data, or None if not found
    """
    try:
        properties = api_response.get("properties", {})
        timeseries = properties.get("timeseries", [])

        if not timeseries:
            logger.warning("No timeseries data found in API response")
            return None

        # Find forecast for tomorrow (next day)
        tomorrow = date.today() + timedelta(days=1)

        for entry in timeseries:
            entry_time = datetime.fromisoformat(entry["time"].replace("Z", "+00:00"))
            entry_date = entry_time.date()

            # Look for forecast around noon tomorrow for best representation
            if entry_date == tomorrow and 10 <= entry_time.hour <= 14:
                data = entry.get("data", {})
                instant = data.get("instant", {}).get("details", {})
                next_6_hours = data.get("next_6_hours", {})

                # Combine instant data with forecast data
                forecast_data = {
                    "air_temperature": instant.get("air_temperature"),
                    "relative_humidity": instant.get("relative_humidity"),
                    "wind_speed": instant.get("wind_speed"),
                    "symbol_code": next_6_hours.get("summary", {}).get("symbol_code", "unknown")
                }

                return forecast_data

        # Fallback: use first available forecast for tomorrow
        for entry in timeseries:
            entry_time = datetime.fromisoformat(entry["time"].replace("Z", "+00:00"))
            entry_date = entry_time.date()

            if entry_date == tomorrow:
                data = entry.get("data", {})
                instant = data.get("instant", {}).get("details", {})
                next_6_hours = data.get("next_6_hours", {})

                forecast_data = {
                    "air_temperature": instant.get("air_temperature"),
                    "relative_humidity": instant.get("relative_humidity"),
                    "wind_speed": instant.get("wind_speed"),
                    "symbol_code": next_6_hours.get("summary", {}).get("symbol_code", "unknown")
                }

                return forecast_data

        logger.warning(f"No forecast data found for tomorrow ({tomorrow})")
        return None

    except Exception as e:
        logger.error(f"Error extracting tomorrow's forecast: {str(e)}")
        return None


def map_weather_symbol(symbol_code: str) -> WeatherCondition:
    """
    Map met.no weather symbol to internal weather condition.

    Args:
        symbol_code: Weather symbol code from met.no API

    Returns:
        WeatherCondition enum value
    """
    # Remove any suffix numbers (e.g., "clearsky_day_1" -> "clearsky_day", "rain_2" -> "rain")
    base_symbol = symbol_code.split("_")
    if len(base_symbol) >= 2 and base_symbol[-1].isdigit():
        base_symbol = "_".join(base_symbol[:-1])
    else:
        base_symbol = symbol_code

    return WEATHER_SYMBOL_MAPPING.get(base_symbol, WeatherCondition.UNKNOWN)


def validate_met_no_response(api_response: Dict[str, Any]) -> bool:
    """
    Validate that met.no API response has the expected structure.

    Args:
        api_response: Raw response from met.no API

    Returns:
        True if response is valid, False otherwise
    """
    try:
        # Check basic structure
        if not isinstance(api_response, dict):
            return False

        properties = api_response.get("properties")
        if not properties or not isinstance(properties, dict):
            return False

        timeseries = properties.get("timeseries")
        if not timeseries or not isinstance(timeseries, list):
            return False

        # Check that at least one entry has the required structure
        for entry in timeseries[:5]:  # Check first 5 entries
            if not isinstance(entry, dict):
                continue

            if "time" not in entry or "data" not in entry:
                continue

            data = entry["data"]
            if not isinstance(data, dict):
                continue

            instant = data.get("instant", {})
            if not isinstance(instant, dict):
                continue

            details = instant.get("details", {})
            if isinstance(details, dict) and "air_temperature" in details:
                return True

        return False

    except Exception as e:
        logger.error(f"Error validating met.no response: {str(e)}")
        return False


def create_cache_key(city_id: str, forecast_date: date) -> str:
    """
    Create a cache key for weather data.

    Args:
        city_id: ID of the city
        forecast_date: Date of the forecast

    Returns:
        String cache key
    """
    return f"weather:{city_id}:{forecast_date.isoformat()}"


def calculate_ttl(hours: int = 1) -> int:
    """
    Calculate TTL timestamp for caching.

    Args:
        hours: Number of hours from now for TTL

    Returns:
        Unix timestamp for TTL
    """
    return int((datetime.utcnow() + timedelta(hours=hours)).timestamp())