"""
DynamoDB cache client for weather data persistence.

This module provides DynamoDB integration for caching weather data with
1-hour TTL, connection pooling, and comprehensive error handling.
"""

import json
import logging
import os
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Union
from decimal import Decimal

import boto3
from botocore.exceptions import ClientError, BotoCoreError
from botocore.config import Config

from weather_service.models import CityWeatherData, ValidationError

logger = logging.getLogger(__name__)


class CacheError(Exception):
    """Base exception for cache-related errors."""
    pass


class CacheConnectionError(CacheError):
    """Exception raised when cache connection fails."""
    pass


class CacheOperationError(CacheError):
    """Exception raised when cache operation fails."""
    pass


class DynamoDBWeatherCache:
    """
    DynamoDB client for weather data caching with connection pooling.

    Provides weather data caching operations with 1-hour TTL, connection
    pooling, and comprehensive error handling for DynamoDB operations.
    """

    DEFAULT_TABLE_NAME = "weather-forecast-cache"
    DEFAULT_TTL_SECONDS = 3600  # 1 hour

    def __init__(
        self,
        table_name: Optional[str] = None,
        ttl_seconds: int = DEFAULT_TTL_SECONDS,
        region_name: Optional[str] = None
    ):
        """
        Initialize the DynamoDB weather cache client.

        Args:
            table_name: DynamoDB table name (default from environment or DEFAULT_TABLE_NAME)
            ttl_seconds: Cache TTL in seconds (default: 3600 = 1 hour)
            region_name: AWS region name (default from environment)
        """
        self.table_name = table_name or os.getenv("DYNAMODB_TABLE_NAME", self.DEFAULT_TABLE_NAME)
        self.ttl_seconds = ttl_seconds
        self.region_name = region_name or os.getenv("AWS_REGION", "us-east-1")

        # Configure boto3 with connection pooling and retries
        self.config = Config(
            region_name=self.region_name,
            retries={
                'max_attempts': 3,
                'mode': 'adaptive'
            },
            max_pool_connections=10
        )

        # Initialize DynamoDB client and table resource
        self._dynamodb_client = None
        self._dynamodb_resource = None
        self._table = None

    def _get_dynamodb_client(self):
        """Get or create DynamoDB client with connection pooling."""
        if self._dynamodb_client is None:
            try:
                self._dynamodb_client = boto3.client('dynamodb', config=self.config)
                logger.debug(f"Created DynamoDB client for region {self.region_name}")
            except Exception as e:
                logger.error(f"Failed to create DynamoDB client: {e}")
                raise CacheConnectionError(f"Failed to create DynamoDB client: {e}") from e

        return self._dynamodb_client

    def _get_dynamodb_resource(self):
        """Get or create DynamoDB resource with connection pooling."""
        if self._dynamodb_resource is None:
            try:
                self._dynamodb_resource = boto3.resource('dynamodb', config=self.config)
                logger.debug(f"Created DynamoDB resource for region {self.region_name}")
            except Exception as e:
                logger.error(f"Failed to create DynamoDB resource: {e}")
                raise CacheConnectionError(f"Failed to create DynamoDB resource: {e}") from e

        return self._dynamodb_resource

    def _get_table(self):
        """Get or create DynamoDB table reference."""
        if self._table is None:
            try:
                dynamodb = self._get_dynamodb_resource()
                self._table = dynamodb.Table(self.table_name)
                logger.debug(f"Created table reference for {self.table_name}")
            except Exception as e:
                logger.error(f"Failed to create table reference: {e}")
                raise CacheConnectionError(f"Failed to create table reference: {e}") from e

        return self._table

    def _calculate_ttl(self) -> int:
        """
        Calculate TTL timestamp for cache expiration.

        Returns:
            Unix timestamp for cache expiration (current time + TTL seconds)
        """
        return int(time.time()) + self.ttl_seconds

    def _is_expired(self, ttl_timestamp: int) -> bool:
        """
        Check if a cache entry is expired.

        Args:
            ttl_timestamp: TTL timestamp from cache entry

        Returns:
            True if expired, False otherwise
        """
        return int(time.time()) >= ttl_timestamp

    def _serialize_weather_data(self, weather_data: CityWeatherData) -> Dict[str, Any]:
        """
        Serialize weather data for DynamoDB storage.

        Args:
            weather_data: CityWeatherData object to serialize

        Returns:
            Dictionary suitable for DynamoDB storage
        """
        try:
            # Convert to dictionary and handle Decimal conversion
            data_dict = weather_data.to_dict()

            # Convert float values to Decimal for DynamoDB
            def convert_floats(obj):
                if isinstance(obj, dict):
                    return {k: convert_floats(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_floats(item) for item in obj]
                elif isinstance(obj, float):
                    return Decimal(str(obj))
                else:
                    return obj

            return convert_floats(data_dict)

        except Exception as e:
            logger.error(f"Failed to serialize weather data: {e}")
            raise CacheOperationError(f"Failed to serialize weather data: {e}") from e

    def _deserialize_weather_data(self, cache_item: Dict[str, Any]) -> CityWeatherData:
        """
        Deserialize weather data from DynamoDB storage.

        Args:
            cache_item: Dictionary from DynamoDB

        Returns:
            CityWeatherData object
        """
        try:
            # Convert Decimal values back to float
            def convert_decimals(obj):
                if isinstance(obj, dict):
                    return {k: convert_decimals(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_decimals(item) for item in obj]
                elif isinstance(obj, Decimal):
                    return float(obj)
                else:
                    return obj

            # Extract weather data from cache item
            weather_dict = convert_decimals(cache_item.get('weather_data', {}))

            # Create CityWeatherData object from dictionary
            return CityWeatherData.from_dict(weather_dict)

        except Exception as e:
            logger.error(f"Failed to deserialize weather data: {e}")
            raise CacheOperationError(f"Failed to deserialize weather data: {e}") from e

    def get_cached_weather(self, city_id: str) -> Optional[CityWeatherData]:
        """
        Get cached weather data for a city.

        Args:
            city_id: ID of the city to retrieve

        Returns:
            CityWeatherData object if found and not expired, None otherwise

        Raises:
            CacheError: For cache operation errors
        """
        try:
            table = self._get_table()

            logger.debug(f"Getting cached weather data for city: {city_id}")

            # Get item from DynamoDB
            response = table.get_item(
                Key={'city_id': city_id}
            )

            # Check if item exists
            if 'Item' not in response:
                logger.debug(f"No cached data found for city: {city_id}")
                return None

            item = response['Item']

            # Check if cache entry is expired
            ttl_timestamp = item.get('ttl', 0)
            if self._is_expired(ttl_timestamp):
                logger.debug(f"Cached data expired for city: {city_id}")
                # Optionally delete expired item
                await self._delete_expired_item(city_id)
                return None

            # Deserialize and return weather data
            weather_data = self._deserialize_weather_data(item)
            logger.info(f"Retrieved cached weather data for city: {city_id}")

            return weather_data

        except ClientError as e:
            error_code = e.response['Error']['Code']
            logger.error(f"DynamoDB client error getting cached weather for {city_id}: {error_code}")

            if error_code == 'ResourceNotFoundException':
                logger.warning(f"DynamoDB table {self.table_name} not found")
                raise CacheConnectionError(f"Cache table not found: {self.table_name}")
            else:
                raise CacheOperationError(f"Failed to get cached weather: {error_code}") from e

        except BotoCoreError as e:
            logger.error(f"Boto3 error getting cached weather for {city_id}: {e}")
            raise CacheConnectionError(f"AWS connection error: {e}") from e

        except Exception as e:
            logger.error(f"Unexpected error getting cached weather for {city_id}: {e}")
            raise CacheOperationError(f"Unexpected cache error: {e}") from e

    def set_cached_weather(self, weather_data: CityWeatherData) -> bool:
        """
        Set cached weather data for a city.

        Args:
            weather_data: CityWeatherData object to cache

        Returns:
            True if successful, False otherwise

        Raises:
            CacheError: For cache operation errors
        """
        try:
            table = self._get_table()
            city_id = weather_data.city_id

            logger.debug(f"Setting cached weather data for city: {city_id}")

            # Calculate TTL
            ttl_timestamp = self._calculate_ttl()

            # Serialize weather data
            serialized_data = self._serialize_weather_data(weather_data)

            # Create cache item
            cache_item = {
                'city_id': city_id,
                'weather_data': serialized_data,
                'ttl': ttl_timestamp,
                'cached_at': datetime.now(timezone.utc).isoformat(),
                'cache_version': '1.0'
            }

            # Put item in DynamoDB
            table.put_item(Item=cache_item)

            logger.info(f"Cached weather data for city: {city_id} (expires at {ttl_timestamp})")
            return True

        except ClientError as e:
            error_code = e.response['Error']['Code']
            logger.error(f"DynamoDB client error setting cached weather for {weather_data.city_id}: {error_code}")

            if error_code == 'ResourceNotFoundException':
                logger.warning(f"DynamoDB table {self.table_name} not found")
                raise CacheConnectionError(f"Cache table not found: {self.table_name}")
            else:
                raise CacheOperationError(f"Failed to set cached weather: {error_code}") from e

        except BotoCoreError as e:
            logger.error(f"Boto3 error setting cached weather for {weather_data.city_id}: {e}")
            raise CacheConnectionError(f"AWS connection error: {e}") from e

        except Exception as e:
            logger.error(f"Unexpected error setting cached weather for {weather_data.city_id}: {e}")
            raise CacheOperationError(f"Unexpected cache error: {e}") from e

    async def get_all_cached_weather(self) -> List[CityWeatherData]:
        """
        Get all cached weather data for all cities.

        Returns:
            List of CityWeatherData objects for non-expired cache entries

        Raises:
            CacheError: For cache operation errors
        """
        try:
            table = self._get_table()

            logger.debug("Getting all cached weather data")

            # Scan table for all items
            response = table.scan()
            items = response.get('Items', [])

            # Handle pagination if needed
            while 'LastEvaluatedKey' in response:
                response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
                items.extend(response.get('Items', []))

            # Filter non-expired items and deserialize
            weather_data_list = []
            current_time = int(time.time())

            for item in items:
                ttl_timestamp = item.get('ttl', 0)

                # Skip expired items
                if self._is_expired(ttl_timestamp):
                    city_id = item.get('city_id', 'unknown')
                    logger.debug(f"Skipping expired cache entry for city: {city_id}")
                    continue

                try:
                    weather_data = self._deserialize_weather_data(item)
                    weather_data_list.append(weather_data)
                except Exception as e:
                    city_id = item.get('city_id', 'unknown')
                    logger.warning(f"Failed to deserialize cached data for city {city_id}: {e}")
                    continue

            logger.info(f"Retrieved {len(weather_data_list)} cached weather entries")
            return weather_data_list

        except ClientError as e:
            error_code = e.response['Error']['Code']
            logger.error(f"DynamoDB client error getting all cached weather: {error_code}")

            if error_code == 'ResourceNotFoundException':
                logger.warning(f"DynamoDB table {self.table_name} not found")
                raise CacheConnectionError(f"Cache table not found: {self.table_name}")
            else:
                raise CacheOperationError(f"Failed to get all cached weather: {error_code}") from e

        except BotoCoreError as e:
            logger.error(f"Boto3 error getting all cached weather: {e}")
            raise CacheConnectionError(f"AWS connection error: {e}") from e

        except Exception as e:
            logger.error(f"Unexpected error getting all cached weather: {e}")
            raise CacheOperationError(f"Unexpected cache error: {e}") from e

    async def delete_cached_weather(self, city_id: str) -> bool:
        """
        Delete cached weather data for a city.

        Args:
            city_id: ID of the city to delete from cache

        Returns:
            True if successful, False otherwise

        Raises:
            CacheError: For cache operation errors
        """
        try:
            table = self._get_table()

            logger.debug(f"Deleting cached weather data for city: {city_id}")

            # Delete item from DynamoDB
            table.delete_item(
                Key={'city_id': city_id}
            )

            logger.info(f"Deleted cached weather data for city: {city_id}")
            return True

        except ClientError as e:
            error_code = e.response['Error']['Code']
            logger.error(f"DynamoDB client error deleting cached weather for {city_id}: {error_code}")

            if error_code == 'ResourceNotFoundException':
                logger.warning(f"DynamoDB table {self.table_name} not found")
                raise CacheConnectionError(f"Cache table not found: {self.table_name}")
            else:
                raise CacheOperationError(f"Failed to delete cached weather: {error_code}") from e

        except BotoCoreError as e:
            logger.error(f"Boto3 error deleting cached weather for {city_id}: {e}")
            raise CacheConnectionError(f"AWS connection error: {e}") from e

        except Exception as e:
            logger.error(f"Unexpected error deleting cached weather for {city_id}: {e}")
            raise CacheOperationError(f"Unexpected cache error: {e}") from e

    async def _delete_expired_item(self, city_id: str) -> None:
        """
        Delete an expired cache item.

        Args:
            city_id: ID of the city to delete
        """
        try:
            await self.delete_cached_weather(city_id)
            logger.debug(f"Deleted expired cache entry for city: {city_id}")
        except Exception as e:
            logger.warning(f"Failed to delete expired cache entry for city {city_id}: {e}")

    async def clear_all_cache(self) -> int:
        """
        Clear all cached weather data.

        Returns:
            Number of items deleted

        Raises:
            CacheError: For cache operation errors
        """
        try:
            table = self._get_table()

            logger.debug("Clearing all cached weather data")

            # Scan table to get all items
            response = table.scan(ProjectionExpression='city_id')
            items = response.get('Items', [])

            # Handle pagination
            while 'LastEvaluatedKey' in response:
                response = table.scan(
                    ProjectionExpression='city_id',
                    ExclusiveStartKey=response['LastEvaluatedKey']
                )
                items.extend(response.get('Items', []))

            # Delete all items
            deleted_count = 0
            for item in items:
                city_id = item['city_id']
                try:
                    await self.delete_cached_weather(city_id)
                    deleted_count += 1
                except Exception as e:
                    logger.warning(f"Failed to delete cache entry for city {city_id}: {e}")

            logger.info(f"Cleared {deleted_count} cached weather entries")
            return deleted_count

        except Exception as e:
            logger.error(f"Error clearing all cache: {e}")
            raise CacheOperationError(f"Failed to clear cache: {e}") from e

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics and configuration.

        Returns:
            Dictionary with cache statistics
        """
        return {
            "table_name": self.table_name,
            "ttl_seconds": self.ttl_seconds,
            "region_name": self.region_name,
            "cache_version": "1.0"
        }


# Convenience function for creating a cache client instance
def create_weather_cache(
    table_name: Optional[str] = None,
    ttl_seconds: int = DynamoDBWeatherCache.DEFAULT_TTL_SECONDS,
    region_name: Optional[str] = None
) -> DynamoDBWeatherCache:
    """
    Create a DynamoDB weather cache client instance.

    Args:
        table_name: DynamoDB table name
        ttl_seconds: Cache TTL in seconds
        region_name: AWS region name

    Returns:
        Configured DynamoDBWeatherCache instance
    """
    return DynamoDBWeatherCache(
        table_name=table_name,
        ttl_seconds=ttl_seconds,
        region_name=region_name
    )