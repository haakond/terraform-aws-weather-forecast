"""
Weather data processor for orchestrating weather data retrieval and processing.

This module provides the main processing logic for fetching, transforming,
and caching weather data from the met.no API.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from weather_service.api_client import WeatherAPIClient, WeatherAPIError
from weather_service.transformers import parse_met_no_response, validate_met_no_response
from weather_service.config import get_cities_config, get_city_config, validate_city_id
from weather_service.models import CityWeatherData, ValidationError
from weather_service.cache import DynamoDBWeatherCache, CacheError, create_weather_cache

logger = logging.getLogger(__name__)


class WeatherProcessor:
    """
    Main weather data processor that orchestrates data retrieval and processing.

    This class handles the complete workflow of fetching weather data from the
    met.no API, transforming it into the application's data model, and preparing
    it for caching and frontend consumption.
    """

    def __init__(
        self,
        api_client: Optional[WeatherAPIClient] = None,
        cache_client: Optional[DynamoDBWeatherCache] = None
    ):
        """
        Initialize the weather processor.

        Args:
            api_client: Optional API client instance. If not provided, a default one will be created.
            cache_client: Optional cache client instance. If not provided, a default one will be created.
        """
        self.api_client = api_client or WeatherAPIClient()
        self.cache_client = cache_client or create_weather_cache()

    def process_city_weather(self, city_id: str, use_cache: bool = True) -> CityWeatherData:
        """
        Process weather data for a single city with caching support.

        Args:
            city_id: ID of the city to process
            use_cache: Whether to use cache for data retrieval and storage

        Returns:
            CityWeatherData object with processed weather information

        Raises:
            ValueError: If city_id is not supported
            WeatherAPIError: If API request fails
            ValidationError: If data processing fails
        """
        # Validate city ID
        if not validate_city_id(city_id):
            raise ValueError(f"Unsupported city ID: {city_id}")

        # Try to get cached data first if caching is enabled
        if use_cache:
            try:
                cached_data = self.cache_client.get_cached_weather(city_id)
                if cached_data is not None:
                    logger.info(f"Using cached weather data for {cached_data.city_name}")
                    return cached_data
            except CacheError as e:
                logger.warning(f"Cache error for {city_id}, falling back to API: {str(e)}")

        try:
            # Get city configuration
            city_config = get_city_config(city_id)

            # Fetch weather data from API
            logger.info(f"Fetching weather data from API for {city_config.name}")
            api_response = self.api_client.get_weather_data(
                latitude=city_config.coordinates.latitude,
                longitude=city_config.coordinates.longitude
            )

            # Validate API response structure
            if not validate_met_no_response(api_response):
                raise ValidationError(f"Invalid API response structure for {city_id}")

            # Transform API response to internal data model
            weather_data = parse_met_no_response(api_response, city_id)

            # Cache the weather data if caching is enabled
            if use_cache:
                try:
                    self.cache_client.set_cached_weather(weather_data)
                    logger.debug(f"Cached weather data for {city_config.name}")
                except CacheError as e:
                    logger.warning(f"Failed to cache weather data for {city_id}: {str(e)}")
                    # Don't fail the request if caching fails

            logger.info(f"Successfully processed weather data for {city_config.name}")
            return weather_data

        except WeatherAPIError as e:
            logger.error(f"API error while processing weather for {city_id}: {str(e)}")
            raise

        except ValidationError as e:
            logger.error(f"Validation error while processing weather for {city_id}: {str(e)}")
            raise

        except Exception as e:
            logger.error(f"Unexpected error while processing weather for {city_id}: {str(e)}")
            raise ValidationError(f"Failed to process weather data for {city_id}: {str(e)}")

    async def process_all_cities_weather(self, use_cache: bool = True) -> List[CityWeatherData]:
        """
        Process weather data for all configured cities with caching support.

        Args:
            use_cache: Whether to use cache for data retrieval and storage

        Returns:
            List of CityWeatherData objects for all cities

        Raises:
            WeatherAPIError: If any API request fails
            ValidationError: If any data processing fails
        """
        cities_config = get_cities_config()
        weather_data_list = []

        # Process cities concurrently for better performance
        tasks = []
        for city_config in cities_config:
            task = self.process_city_weather(city_config.id, use_cache=use_cache)
            tasks.append(task)

        try:
            # Wait for all tasks to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results and handle any exceptions
            for i, result in enumerate(results):
                city_id = cities_config[i].id

                if isinstance(result, Exception):
                    logger.error(f"Failed to process weather for {city_id}: {str(result)}")
                    # Re-raise the first exception encountered
                    raise result
                else:
                    weather_data_list.append(result)

            logger.info(f"Successfully processed weather data for {len(weather_data_list)} cities")
            return weather_data_list

        except Exception as e:
            logger.error(f"Error processing weather data for all cities: {str(e)}")
            raise

    async def process_cities_weather_with_fallback(self, use_cache: bool = True) -> List[CityWeatherData]:
        """
        Process weather data for all cities with individual error handling and caching support.

        This method continues processing other cities even if some fail,
        providing better resilience for partial failures.

        Args:
            use_cache: Whether to use cache for data retrieval and storage

        Returns:
            List of CityWeatherData objects for successfully processed cities
        """
        cities_config = get_cities_config()
        weather_data_list = []

        # Process cities concurrently
        tasks = []
        for city_config in cities_config:
            task = self.process_city_weather(city_config.id, use_cache=use_cache)
            tasks.append(task)

        # Wait for all tasks to complete, collecting both successes and failures
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        successful_count = 0
        failed_count = 0

        for i, result in enumerate(results):
            city_id = cities_config[i].id
            city_name = cities_config[i].name

            if isinstance(result, Exception):
                logger.error(f"Failed to process weather for {city_name} ({city_id}): {str(result)}")
                failed_count += 1
            else:
                weather_data_list.append(result)
                successful_count += 1

        logger.info(f"Weather processing completed: {successful_count} successful, {failed_count} failed")

        if successful_count == 0:
            raise WeatherAPIError("Failed to process weather data for any city")

        return weather_data_list

    async def get_weather_summary(self, use_cache: bool = True) -> Dict[str, Any]:
        """
        Get a summary of weather data for all cities with caching support.

        Args:
            use_cache: Whether to use cache for data retrieval and storage

        Returns:
            Dictionary with weather summary information
        """
        try:
            weather_data_list = await self.process_all_cities_weather(use_cache=use_cache)

            summary = {
                "timestamp": datetime.utcnow().isoformat(),
                "cities_count": len(weather_data_list),
                "cities": [data.to_dict() for data in weather_data_list],
                "status": "success"
            }

            return summary

        except Exception as e:
            logger.error(f"Error generating weather summary: {str(e)}")
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "cities_count": 0,
                "cities": [],
                "status": "error",
                "error": str(e)
            }

    async def close(self):
        """Close the API client connection."""
        if self.api_client:
            await self.api_client.close()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


# Convenience function for creating a processor instance
def create_weather_processor(
    api_client: Optional[WeatherAPIClient] = None,
    cache_client: Optional[DynamoDBWeatherCache] = None
) -> WeatherProcessor:
    """
    Create a weather processor instance.

    Args:
        api_client: Optional API client instance
        cache_client: Optional cache client instance

    Returns:
        Configured WeatherProcessor instance
    """
    return WeatherProcessor(api_client=api_client, cache_client=cache_client)