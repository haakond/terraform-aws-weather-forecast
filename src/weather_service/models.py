"""
Weather data models with validation for the weather forecast application.

This module defines the data structures used throughout the weather service,
including weather data, city configuration, and validation utilities.
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Dict, List, Optional, Union
import json
from enum import Enum


class WeatherCondition(Enum):
    """Enumeration of weather conditions supported by the application."""
    CLEAR_SKY = "clearsky"
    PARTLY_CLOUDY = "partlycloudy"
    CLOUDY = "cloudy"
    LIGHT_RAIN = "lightrain"
    RAIN = "rain"
    HEAVY_RAIN = "heavyrain"
    LIGHT_SNOW = "lightsnow"
    SNOW = "snow"
    HEAVY_SNOW = "heavysnow"
    FOG = "fog"
    THUNDERSTORM = "thunderstorm"
    UNKNOWN = "unknown"


@dataclass
class Coordinates:
    """Geographic coordinates for a city."""
    latitude: float
    longitude: float

    def __post_init__(self):
        """Validate coordinate values."""
        if not -90 <= self.latitude <= 90:
            raise ValueError(f"Latitude must be between -90 and 90, got {self.latitude}")
        if not -180 <= self.longitude <= 180:
            raise ValueError(f"Longitude must be between -180 and 180, got {self.longitude}")


@dataclass
class Temperature:
    """Temperature data with unit specification."""
    value: float
    unit: str = "celsius"

    def __post_init__(self):
        """Validate temperature data."""
        if self.unit not in ["celsius", "fahrenheit", "kelvin"]:
            raise ValueError(f"Unsupported temperature unit: {self.unit}")

        # Basic sanity check for temperature values
        if self.unit == "celsius" and not -100 <= self.value <= 60:
            raise ValueError(f"Temperature value {self.value}°C seems unrealistic")
        elif self.unit == "fahrenheit" and not -148 <= self.value <= 140:
            raise ValueError(f"Temperature value {self.value}°F seems unrealistic")
        elif self.unit == "kelvin" and not 173 <= self.value <= 333:
            raise ValueError(f"Temperature value {self.value}K seems unrealistic")


@dataclass
class WeatherForecast:
    """Weather forecast data for a specific date."""
    date: date
    temperature: Temperature
    condition: WeatherCondition
    description: str
    icon: str
    humidity: Optional[int] = None
    wind_speed: Optional[float] = None

    def __post_init__(self):
        """Validate forecast data."""
        if self.humidity is not None and not 0 <= self.humidity <= 100:
            raise ValueError(f"Humidity must be between 0 and 100, got {self.humidity}")

        if self.wind_speed is not None and self.wind_speed < 0:
            raise ValueError(f"Wind speed cannot be negative, got {self.wind_speed}")

        if not self.description.strip():
            raise ValueError("Weather description cannot be empty")

        if not self.icon.strip():
            raise ValueError("Weather icon cannot be empty")


@dataclass
class CityWeatherData:
    """Complete weather data for a city."""
    city_id: str
    city_name: str
    country: str
    coordinates: Coordinates
    forecast: WeatherForecast
    last_updated: datetime
    ttl: Optional[int] = None

    def __post_init__(self):
        """Validate city weather data."""
        if not self.city_id.strip():
            raise ValueError("City ID cannot be empty")

        if not self.city_name.strip():
            raise ValueError("City name cannot be empty")

        if not self.country.strip():
            raise ValueError("Country cannot be empty")

        # Validate that forecast date is not in the past (allowing today)
        if self.forecast.date < date.today():
            raise ValueError(f"Forecast date {self.forecast.date} cannot be in the past")

    def to_dict(self) -> Dict:
        """Convert weather data to dictionary format."""
        return {
            "cityId": self.city_id,
            "cityName": self.city_name,
            "country": self.country,
            "coordinates": {
                "latitude": self.coordinates.latitude,
                "longitude": self.coordinates.longitude
            },
            "forecast": {
                "date": self.forecast.date.isoformat(),
                "temperature": {
                    "value": self.forecast.temperature.value,
                    "unit": self.forecast.temperature.unit
                },
                "condition": self.forecast.condition.value,
                "description": self.forecast.description,
                "icon": self.forecast.icon,
                "humidity": self.forecast.humidity,
                "windSpeed": self.forecast.wind_speed
            },
            "lastUpdated": self.last_updated.isoformat(),
            "ttl": self.ttl
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'CityWeatherData':
        """Create CityWeatherData from dictionary."""
        coordinates = Coordinates(
            latitude=data["coordinates"]["latitude"],
            longitude=data["coordinates"]["longitude"]
        )

        temperature = Temperature(
            value=data["forecast"]["temperature"]["value"],
            unit=data["forecast"]["temperature"]["unit"]
        )

        forecast = WeatherForecast(
            date=date.fromisoformat(data["forecast"]["date"]),
            temperature=temperature,
            condition=WeatherCondition(data["forecast"]["condition"]),
            description=data["forecast"]["description"],
            icon=data["forecast"]["icon"],
            humidity=data["forecast"].get("humidity"),
            wind_speed=data["forecast"].get("windSpeed")
        )

        return cls(
            city_id=data["cityId"],
            city_name=data["cityName"],
            country=data["country"],
            coordinates=coordinates,
            forecast=forecast,
            last_updated=datetime.fromisoformat(data["lastUpdated"]),
            ttl=data.get("ttl")
        )


@dataclass
class CityConfig:
    """Configuration for a city including its coordinates."""
    id: str
    name: str
    country: str
    coordinates: Coordinates

    def __post_init__(self):
        """Validate city configuration."""
        if not self.id.strip():
            raise ValueError("City ID cannot be empty")

        if not self.name.strip():
            raise ValueError("City name cannot be empty")

        if not self.country.strip():
            raise ValueError("Country cannot be empty")

    def to_dict(self) -> Dict:
        """Convert city config to dictionary format."""
        return {
            "id": self.id,
            "name": self.name,
            "country": self.country,
            "coordinates": {
                "lat": self.coordinates.latitude,
                "lon": self.coordinates.longitude
            }
        }


class ValidationError(Exception):
    """Custom exception for data validation errors."""
    pass


def validate_weather_data(data: Dict) -> None:
    """
    Validate weather data dictionary structure.

    Args:
        data: Dictionary containing weather data

    Raises:
        ValidationError: If data structure is invalid
    """
    required_fields = ["cityId", "cityName", "country", "coordinates", "forecast", "lastUpdated"]

    for field in required_fields:
        if field not in data:
            raise ValidationError(f"Missing required field: {field}")

    # Validate coordinates
    coords = data["coordinates"]
    if "latitude" not in coords or "longitude" not in coords:
        raise ValidationError("Coordinates must include latitude and longitude")

    # Validate forecast
    forecast = data["forecast"]
    forecast_fields = ["date", "temperature", "condition", "description", "icon"]

    for field in forecast_fields:
        if field not in forecast:
            raise ValidationError(f"Missing required forecast field: {field}")

    # Validate temperature structure
    temp = forecast["temperature"]
    if "value" not in temp or "unit" not in temp:
        raise ValidationError("Temperature must include value and unit")


def validate_city_config(config: Dict) -> None:
    """
    Validate city configuration dictionary structure.

    Args:
        config: Dictionary containing city configuration

    Raises:
        ValidationError: If configuration structure is invalid
    """
    required_fields = ["id", "name", "country", "coordinates"]

    for field in required_fields:
        if field not in config:
            raise ValidationError(f"Missing required field: {field}")

    coords = config["coordinates"]
    if "lat" not in coords or "lon" not in coords:
        raise ValidationError("Coordinates must include lat and lon")