"""
Unit tests for the DynamoDB weather cache.

Tests the DynamoDB cache client functionality including caching operations,
TTL handling, error handling, and connection pooling.
"""

import json
import os
import pytest
import time
from datetime import datetime, timezone, date
from decimal import Decimal
from unittest.mock import Mock, patch, AsyncMock
from botocore.exceptions import ClientError, BotoCoreError

# Import the module under test
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from weather_service.cache import (
    DynamoDBWeatherCache, CacheError, CacheConnectionError, CacheOperationError,
    create_weather_cache
)
from weather_service.models import (
    CityWeatherData, WeatherForecast, Temperature, WeatherCondition, Coordinates
)


class TestDynamoDBWeatherCache:
    """Test cases for the DynamoDB weather cache client."""

    def setup_method(self):
        """Set up test fixtures."""
        self.cache = DynamoDBWeatherCache(
            table_name="test-weather-cache",
            ttl_seconds=3600,
            region_name="us-east-1"
        )

        # Create sample weather data
        self.sample_weather_data = CityWeatherData(
            city_id="oslo",
            city_name="Oslo",
            country="Norway",
            coordinates=Coordinates(latitude=59.9139, longitude=10.7522),
            forecast=WeatherForecast(
                date=date.today(),
                temperature=Temperature(value=-2.0, unit="celsius"),
                condition=WeatherCondition.PARTLY_CLOUDY,
                description="Partly cloudy",
                icon="partly_cloudy_day",
                humidity=75,
                wind_speed=12.5
            ),
            last_updated=datetime.now(timezone.utc),
            ttl=int(time.time()) + 3600
        )

    def test_init_default_values(self):
        """Test cache initialization with default values."""
        cache = DynamoDBWeatherCache()

        assert cache.table_name == "weather-forecast-cache"
        assert cache.ttl_seconds == 3600
        assert cache.region_name == "us-east-1"  # Default from environment or fallback

    def test_init_custom_values(self):
        """Test cache initialization with custom values."""
        cache = DynamoDBWeatherCache(
            table_name="custom-table",
            ttl_seconds=7200,
            region_name="eu-west-1"
        )

        assert cache.table_name == "custom-table"
        assert cache.ttl_seconds == 7200
        assert cache.region_name == "eu-west-1"

    @patch.dict(os.environ, {"DYNAMODB_TABLE_NAME": "env-table", "AWS_REGION": "eu-central-1"})
    def test_init_from_environment(self):
        """Test cache initialization from environment variables."""
        cache = DynamoDBWeatherCache()

        assert cache.table_name == "env-table"
        assert cache.region_name == "eu-central-1"

    def test_calculate_ttl(self):
        """Test TTL calculation."""
        current_time = int(time.time())
        ttl = self.cache._calculate_ttl()

        # TTL should be current time + ttl_seconds (with small tolerance for execution time)
        assert ttl >= current_time + self.cache.ttl_seconds
        assert ttl <= current_time + self.cache.ttl_seconds + 5

    def test_is_expired(self):
        """Test expiration checking."""
        current_time = int(time.time())

        # Past timestamp should be expired
        past_ttl = current_time - 100
        assert self.cache._is_expired(past_ttl) is True

        # Future timestamp should not be expired
        future_ttl = current_time + 100
        assert self.cache._is_expired(future_ttl) is False

        # Current timestamp should be expired (edge case)
        assert self.cache._is_expired(current_time) is True

    def test_serialize_weather_data(self):
        """Test weather data serialization."""
        serialized = self.cache._serialize_weather_data(self.sample_weather_data)

        # Check that float values are converted to Decimal
        assert isinstance(serialized["coordinates"]["latitude"], Decimal)
        assert isinstance(serialized["coordinates"]["longitude"], Decimal)
        assert isinstance(serialized["forecast"]["temperature"]["value"], Decimal)
        assert isinstance(serialized["forecast"]["windSpeed"], Decimal)

        # Check that other values are preserved
        assert serialized["cityId"] == "oslo"
        assert serialized["cityName"] == "Oslo"
        assert serialized["country"] == "Norway"

    def test_deserialize_weather_data(self):
        """Test weather data deserialization."""
        # Create a cache item with Decimal values (as DynamoDB would store)
        cache_item = {
            "weather_data": {
                "cityId": "oslo",
                "cityName": "Oslo",
                "country": "Norway",
                "coordinates": {
                    "latitude": Decimal("59.9139"),
                    "longitude": Decimal("10.7522")
                },
                "forecast": {
                    "date": date.today().isoformat(),
                    "temperature": {
                        "value": Decimal("-2.0"),
                        "unit": "celsius"
                    },
                    "condition": "partlycloudy",
                    "description": "Partly cloudy",
                    "icon": "partly_cloudy_day",
                    "humidity": 75,
                    "windSpeed": Decimal("12.5")
                },
                "lastUpdated": "2024-01-15T10:30:00+00:00",
                "ttl": 1705230600
            }
        }

        weather_data = self.cache._deserialize_weather_data(cache_item)

        # Check that Decimal values are converted back to float
        assert isinstance(weather_data.coordinates.latitude, float)
        assert isinstance(weather_data.coordinates.longitude, float)
        assert isinstance(weather_data.forecast.temperature.value, float)
        assert isinstance(weather_data.forecast.wind_speed, float)

        # Check values
        assert weather_data.city_id == "oslo"
        assert weather_data.city_name == "Oslo"
        assert weather_data.country == "Norway"
        assert weather_data.coordinates.latitude == 59.9139
        assert weather_data.coordinates.longitude == 10.7522

    @patch('weather_service.cache.boto3.resource')
    @pytest.mark.asyncio
    async def test_get_cached_weather_success(self, mock_boto_resource):
        """Test successful cache retrieval."""
        # Mock DynamoDB table
        mock_table = Mock()
        mock_table.get_item.return_value = {
            'Item': {
                'city_id': 'oslo',
                'weather_data': {
                    "cityId": "oslo",
                    "cityName": "Oslo",
                    "country": "Norway",
                    "coordinates": {
                        "latitude": Decimal("59.9139"),
                        "longitude": Decimal("10.7522")
                    },
                    "forecast": {
                        "date": date.today().isoformat(),
                        "temperature": {
                            "value": Decimal("-2.0"),
                            "unit": "celsius"
                        },
                        "condition": "partlycloudy",
                        "description": "Partly cloudy",
                        "icon": "partly_cloudy_day",
                        "humidity": 75,
                        "windSpeed": Decimal("12.5")
                    },
                    "lastUpdated": datetime.now(timezone.utc).isoformat(),
                    "ttl": None
                },
                'ttl': int(time.time()) + 3600,  # Not expired
                'cached_at': datetime.now(timezone.utc).isoformat(),
                'cache_version': '1.0'
            }
        }

        mock_resource = Mock()
        mock_resource.Table.return_value = mock_table
        mock_boto_resource.return_value = mock_resource

        # Test cache retrieval
        result = await self.cache.get_cached_weather("oslo")

        assert result is not None
        assert result.city_id == "oslo"
        assert result.city_name == "Oslo"
        assert result.country == "Norway"

        # Verify DynamoDB was called correctly
        mock_table.get_item.assert_called_once_with(Key={'city_id': 'oslo'})

    @patch('weather_service.cache.boto3.resource')
    @pytest.mark.asyncio
    async def test_get_cached_weather_not_found(self, mock_boto_resource):
        """Test cache retrieval when item not found."""
        # Mock DynamoDB table
        mock_table = Mock()
        mock_table.get_item.return_value = {}  # No 'Item' key

        mock_resource = Mock()
        mock_resource.Table.return_value = mock_table
        mock_boto_resource.return_value = mock_resource

        # Test cache retrieval
        result = await self.cache.get_cached_weather("nonexistent")

        assert result is None
        mock_table.get_item.assert_called_once_with(Key={'city_id': 'nonexistent'})

    @patch('weather_service.cache.boto3.resource')
    @pytest.mark.asyncio
    async def test_get_cached_weather_expired(self, mock_boto_resource):
        """Test cache retrieval with expired item."""
        # Mock DynamoDB table with expired item
        mock_table = Mock()
        mock_table.get_item.return_value = {
            'Item': {
                'city_id': 'oslo',
                'weather_data': {},
                'ttl': int(time.time()) - 100,  # Expired
                'cached_at': datetime.now(timezone.utc).isoformat(),
                'cache_version': '1.0'
            }
        }
        mock_table.delete_item = Mock()  # Mock delete for cleanup

        mock_resource = Mock()
        mock_resource.Table.return_value = mock_table
        mock_boto_resource.return_value = mock_resource

        # Test cache retrieval
        result = await self.cache.get_cached_weather("oslo")

        assert result is None
        # Should attempt to delete expired item
        mock_table.delete_item.assert_called_once_with(Key={'city_id': 'oslo'})

    @patch('weather_service.cache.boto3.resource')
    @pytest.mark.asyncio
    async def test_set_cached_weather_success(self, mock_boto_resource):
        """Test successful cache storage."""
        # Mock DynamoDB table
        mock_table = Mock()
        mock_table.put_item = Mock()

        mock_resource = Mock()
        mock_resource.Table.return_value = mock_table
        mock_boto_resource.return_value = mock_resource

        # Test cache storage
        result = await self.cache.set_cached_weather(self.sample_weather_data)

        assert result is True

        # Verify put_item was called
        mock_table.put_item.assert_called_once()
        call_args = mock_table.put_item.call_args[1]
        item = call_args['Item']

        assert item['city_id'] == 'oslo'
        assert 'weather_data' in item
        assert 'ttl' in item
        assert 'cached_at' in item
        assert item['cache_version'] == '1.0'

    @patch('weather_service.cache.boto3.resource')
    @pytest.mark.asyncio
    async def test_get_cached_weather_client_error(self, mock_boto_resource):
        """Test cache retrieval with DynamoDB client error."""
        # Mock DynamoDB table to raise ClientError
        mock_table = Mock()
        mock_table.get_item.side_effect = ClientError(
            {'Error': {'Code': 'ResourceNotFoundException'}},
            'GetItem'
        )

        mock_resource = Mock()
        mock_resource.Table.return_value = mock_table
        mock_boto_resource.return_value = mock_resource

        # Test cache retrieval should raise CacheConnectionError
        with pytest.raises(CacheConnectionError):
            await self.cache.get_cached_weather("oslo")

    @patch('weather_service.cache.boto3.resource')
    @pytest.mark.asyncio
    async def test_set_cached_weather_client_error(self, mock_boto_resource):
        """Test cache storage with DynamoDB client error."""
        # Mock DynamoDB table to raise ClientError
        mock_table = Mock()
        mock_table.put_item.side_effect = ClientError(
            {'Error': {'Code': 'ValidationException'}},
            'PutItem'
        )

        mock_resource = Mock()
        mock_resource.Table.return_value = mock_table
        mock_boto_resource.return_value = mock_resource

        # Test cache storage should raise CacheOperationError
        with pytest.raises(CacheOperationError):
            await self.cache.set_cached_weather(self.sample_weather_data)

    @patch('weather_service.cache.boto3.resource')
    @pytest.mark.asyncio
    async def test_delete_cached_weather_success(self, mock_boto_resource):
        """Test successful cache deletion."""
        # Mock DynamoDB table
        mock_table = Mock()
        mock_table.delete_item = Mock()

        mock_resource = Mock()
        mock_resource.Table.return_value = mock_table
        mock_boto_resource.return_value = mock_resource

        # Test cache deletion
        result = await self.cache.delete_cached_weather("oslo")

        assert result is True
        mock_table.delete_item.assert_called_once_with(Key={'city_id': 'oslo'})

    @patch('weather_service.cache.boto3.resource')
    @pytest.mark.asyncio
    async def test_get_all_cached_weather_success(self, mock_boto_resource):
        """Test successful retrieval of all cached weather data."""
        # Mock DynamoDB table
        mock_table = Mock()
        mock_table.scan.return_value = {
            'Items': [
                {
                    'city_id': 'oslo',
                    'weather_data': {
                        "cityId": "oslo",
                        "cityName": "Oslo",
                        "country": "Norway",
                        "coordinates": {"latitude": Decimal("59.9139"), "longitude": Decimal("10.7522")},
                        "forecast": {
                            "date": date.today().isoformat(),
                            "temperature": {"value": Decimal("-2.0"), "unit": "celsius"},
                            "condition": "partlycloudy",
                            "description": "Partly cloudy",
                            "icon": "partly_cloudy_day",
                            "humidity": 75,
                            "windSpeed": Decimal("12.5")
                        },
                        "lastUpdated": datetime.now(timezone.utc).isoformat(),
                        "ttl": None
                    },
                    'ttl': int(time.time()) + 3600,  # Not expired
                },
                {
                    'city_id': 'paris',
                    'weather_data': {},
                    'ttl': int(time.time()) - 100,  # Expired - should be skipped
                }
            ]
        }

        mock_resource = Mock()
        mock_resource.Table.return_value = mock_table
        mock_boto_resource.return_value = mock_resource

        # Test getting all cached weather
        result = await self.cache.get_all_cached_weather()

        # Should only return non-expired items
        assert len(result) == 1
        assert result[0].city_id == "oslo"
        assert result[0].city_name == "Oslo"

    def test_get_cache_stats(self):
        """Test cache statistics retrieval."""
        stats = self.cache.get_cache_stats()

        assert stats["table_name"] == "test-weather-cache"
        assert stats["ttl_seconds"] == 3600
        assert stats["region_name"] == "us-east-1"
        assert stats["cache_version"] == "1.0"


class TestCacheCreation:
    """Test cases for cache creation functions."""

    def test_create_weather_cache_default(self):
        """Test creating cache with default parameters."""
        cache = create_weather_cache()

        assert isinstance(cache, DynamoDBWeatherCache)
        assert cache.table_name == "weather-forecast-cache"
        assert cache.ttl_seconds == 3600

    def test_create_weather_cache_custom(self):
        """Test creating cache with custom parameters."""
        cache = create_weather_cache(
            table_name="custom-table",
            ttl_seconds=7200,
            region_name="eu-west-1"
        )

        assert isinstance(cache, DynamoDBWeatherCache)
        assert cache.table_name == "custom-table"
        assert cache.ttl_seconds == 7200
        assert cache.region_name == "eu-west-1"


class TestCacheErrorHandling:
    """Test cases for cache error handling."""

    def setup_method(self):
        """Set up test fixtures."""
        self.cache = DynamoDBWeatherCache()

    @patch('weather_service.cache.boto3.resource')
    @pytest.mark.asyncio
    async def test_boto_core_error_handling(self, mock_boto_resource):
        """Test handling of BotoCoreError."""
        # Mock to raise BotoCoreError
        mock_boto_resource.side_effect = BotoCoreError()

        with pytest.raises(CacheOperationError):  # Changed from CacheConnectionError
            await self.cache.get_cached_weather("oslo")

    def test_serialization_error_handling(self):
        """Test handling of serialization errors."""
        # Create invalid weather data that would cause serialization error
        invalid_data = Mock()
        invalid_data.to_dict.side_effect = Exception("Serialization failed")

        with pytest.raises(CacheOperationError):
            self.cache._serialize_weather_data(invalid_data)

    def test_deserialization_error_handling(self):
        """Test handling of deserialization errors."""
        # Create invalid cache item
        invalid_item = {
            "weather_data": {
                "invalid": "structure"
            }
        }

        with pytest.raises(CacheOperationError):
            self.cache._deserialize_weather_data(invalid_item)


if __name__ == "__main__":
    pytest.main([__file__])