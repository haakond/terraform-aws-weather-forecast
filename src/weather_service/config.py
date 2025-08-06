"""
City configuration for the weather forecast application.

This module defines the configuration for the four European cities:
Oslo (Norway), Paris (France), London (United Kingdom), and Barcelona (Spain).
"""

from typing import Dict, List
from .models import CityConfig, Coordinates


# City configurations with precise coordinates
CITIES_CONFIG: List[CityConfig] = [
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