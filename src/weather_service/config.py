"""
City configuration for the weather forecast application.

This module defines the configuration for cities, which can be customized
via the CITIES_CONFIG environment variable or defaults to the four European cities:
Oslo (Norway), Paris (France), London (United Kingdom), and Barcelona (Spain).
"""

import json
import os
from typing import Dict, List
from weather_service.models import CityConfig, Coordinates


# Default city configurations with precise coordinates
DEFAULT_CITIES_CONFIG: List[CityConfig] = [
    CityConfig(
        id="oslo",
        name="Oslo",
        country="Norway",
        coordinates=Coordinates(latitude=59.9139, longitude=10.7522)
    ),
    CityConfig(
        id="paris",
        name="Paris",
        country="France",
        coordinates=Coordinates(latitude=48.8566, longitude=2.3522)
    ),
    CityConfig(
        id="london",
        name="London",
        country="United Kingdom",
        coordinates=Coordinates(latitude=51.5074, longitude=-0.1278)
    ),
    CityConfig(
        id="barcelona",
        name="Barcelona",
        country="Spain",
        coordinates=Coordinates(latitude=41.3851, longitude=2.1734)
    )
]


def _load_cities_from_env() -> List[CityConfig]:
    """
    Load cities configuration from environment variable.

    Returns:
        List of CityConfig objects loaded from environment or defaults
    """
    cities_json = os.getenv("CITIES_CONFIG")

    if not cities_json:
        return DEFAULT_CITIES_CONFIG.copy()

    try:
        cities_data = json.loads(cities_json)
        cities_config = []

        for city_data in cities_data:
            city_config = CityConfig(
                id=city_data["id"],
                name=city_data["name"],
                country=city_data["country"],
                coordinates=Coordinates(
                    latitude=city_data["coordinates"]["latitude"],
                    longitude=city_data["coordinates"]["longitude"]
                )
            )
            cities_config.append(city_config)

        return cities_config

    except (json.JSONDecodeError, KeyError, ValueError) as e:
        # Log the error and fall back to defaults
        print(f"Warning: Failed to parse CITIES_CONFIG environment variable: {e}")
        print("Falling back to default cities configuration")
        return DEFAULT_CITIES_CONFIG.copy()


# Load cities configuration from environment or use defaults
CITIES_CONFIG: List[CityConfig] = _load_cities_from_env()


def get_cities_config() -> List[CityConfig]:
    """
    Get the list of configured cities.

    Returns:
        List of CityConfig objects for all supported cities
    """
    return CITIES_CONFIG.copy()


def get_city_config(city_id: str) -> CityConfig:
    """
    Get configuration for a specific city.

    Args:
        city_id: The ID of the city to retrieve

    Returns:
        CityConfig object for the specified city

    Raises:
        ValueError: If city_id is not found
    """
    for city in CITIES_CONFIG:
        if city.id == city_id:
            return city

    raise ValueError(f"City with ID '{city_id}' not found. Available cities: {[c.id for c in CITIES_CONFIG]}")


def get_cities_dict() -> Dict[str, Dict]:
    """
    Get cities configuration as a dictionary.

    Returns:
        Dictionary with city configurations in the format expected by the frontend
    """
    return {
        "cities": [city.to_dict() for city in CITIES_CONFIG]
    }


def validate_city_id(city_id: str) -> bool:
    """
    Validate if a city ID is supported.

    Args:
        city_id: The city ID to validate

    Returns:
        True if city ID is valid, False otherwise
    """
    return any(city.id == city_id for city in CITIES_CONFIG)


def get_supported_city_ids() -> List[str]:
    """
    Get list of all supported city IDs.

    Returns:
        List of supported city ID strings
    """
    return [city.id for city in CITIES_CONFIG]