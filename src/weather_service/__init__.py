# Weather Service Package
"""
Weather forecast service for retrieving and processing weather data
from the Norwegian Meteorological Institute API.
"""

from weather_service.models import (
    CityWeatherData, WeatherForecast, Temperature, WeatherCondition,
    CityConfig, Coordinates, ValidationError
)
from weather_service.config import (
    get_cities_config, get_city_config, validate_city_id,
    get_supported_city_ids, get_cities_dict
)
from weather_service.transformers import (
    parse_met_no_response, extract_tomorrow_forecast, map_weather_symbol,
    validate_met_no_response, create_cache_key, calculate_ttl
)
from weather_service.api_client import (
    WeatherAPIClient, WeatherAPIError, RateLimitError, APIConnectionError,
    MalformedResponseError, create_weather_client
)
from weather_service.processor import (
    WeatherProcessor, create_weather_processor
)
from weather_service.cache import (
    DynamoDBWeatherCache, CacheError, CacheConnectionError, CacheOperationError,
    create_weather_cache
)

__version__ = "1.0.0"

__all__ = [
    # Models
    "CityWeatherData", "WeatherForecast", "Temperature", "WeatherCondition",
    "CityConfig", "Coordinates", "ValidationError",
    # Configuration
    "get_cities_config", "get_city_config", "validate_city_id",
    "get_supported_city_ids", "get_cities_dict",
    # Transformers
    "parse_met_no_response", "extract_tomorrow_forecast", "map_weather_symbol",
    "validate_met_no_response", "create_cache_key", "calculate_ttl",
    # API Client
    "WeatherAPIClient", "WeatherAPIError", "RateLimitError", "APIConnectionError",
    "MalformedResponseError", "create_weather_client",
    # Processor
    "WeatherProcessor", "create_weather_processor",
    # Cache
    "DynamoDBWeatherCache", "CacheError", "CacheConnectionError", "CacheOperationError",
    "create_weather_cache"
]