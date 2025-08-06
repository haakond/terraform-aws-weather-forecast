"""
Unit tests for the weather data processor.

Tests cover core weather data processing functionality.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, date, timedelta

from src.weather_service.processor import WeatherProcessor, create_weather_processor
from src.weather_service.api_client import WeatherAPIClient, WeatherAPIError
from src.weather_service.models import CityWeatherData, WeatherCondition, ValidationError


class TestWeatherProcessor:
    """Test cases for the WeatherProcessor class."""

    def test_processor_initialization(self):
        """Test processor initialization."""
        processor = WeatherProcessor()
        assert isinstance(processor.api_client, WeatherAPIClient)

        # Test with custom client
        mock_client = MagicMock(spec=WeatherAPIClient)
        processor = WeatherProcessor(api_client=mock_client)
        assert processor.api_client is mock_client

    @pytest.mark.asyncio
    async def test_process_city_weather_success(self):
        """Test successful weather processing for a single city."""
        # Create tomorrow's date at noon for consistent testing
        tomorrow = date.today() + timedelta(days=1)
        tomorrow_noon = datetime.combine(tomorrow, datetime.min.time().replace(hour=12))

        mock_api_response = {
            "properties": {
                "timeseries": [
                    {
                        "time": tomorrow_noon.isoformat() + "Z",
                        "data": {
                            "instant": {
                                "details": {
                                    "air_temperature": 15.0,
                                    "relative_humidity": 65.0,
                                    "wind_speed": 8.5
                                }
                            },
                            "next_6_hours": {
                                "summary": {
                                    "symbol_code": "partlycloudy_day"
                                }
                            }
                        }
                    }
                ]
            }
        }

        mock_client = AsyncMock(spec=WeatherAPIClient)
        mock_client.get_weather_forecast.return_value = mock_api_response

        processor = WeatherProcessor(api_client=mock_client)
        result = await processor.process_city_weather("oslo")

        # Verify result
        assert isinstance(result, CityWeatherData)
        assert result.city_id == "oslo"
        assert result.city_name == "Oslo"
        assert result.country == "Norway"
        assert result.forecast.condition == WeatherCondition.PARTLY_CLOUDY
        assert result.forecast.temperature.value == 15.0

        # Verify API client was called correctly
        mock_client.get_weather_forecast.assert_called_once_with(
            latitude=59.9139,
            longitude=10.7522
        )

    @pytest.mark.asyncio
    async def test_process_city_weather_invalid_city(self):
        """Test processing weather with invalid city ID."""
        processor = WeatherProcessor()

        with pytest.raises(ValueError, match="Unsupported city ID"):
            await processor.process_city_weather("invalid_city")

    @pytest.mark.asyncio
    async def test_process_city_weather_api_error(self):
        """Test handling of API errors."""
        mock_client = AsyncMock(spec=WeatherAPIClient)
        mock_client.get_weather_forecast.side_effect = WeatherAPIError("API failed")

        processor = WeatherProcessor(api_client=mock_client)

        with pytest.raises(WeatherAPIError, match="API failed"):
            await processor.process_city_weather("oslo")

    @pytest.mark.asyncio
    async def test_process_city_weather_invalid_response(self):
        """Test handling of invalid API response."""
        mock_api_response = {"invalid": "response"}

        mock_client = AsyncMock(spec=WeatherAPIClient)
        mock_client.get_weather_forecast.return_value = mock_api_response

        processor = WeatherProcessor(api_client=mock_client)

        with pytest.raises(ValidationError, match="Invalid API response structure"):
            await processor.process_city_weather("oslo")

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test processor as async context manager."""
        mock_client = AsyncMock(spec=WeatherAPIClient)

        async with WeatherProcessor(api_client=mock_client) as processor:
            assert isinstance(processor, WeatherProcessor)

        mock_client.close.assert_called_once()


class TestCreateWeatherProcessor:
    """Test cases for the create_weather_processor convenience function."""

    def test_create_weather_processor(self):
        """Test creating a processor."""
        processor = create_weather_processor()
        assert isinstance(processor, WeatherProcessor)

        # Test with custom client
        mock_client = MagicMock(spec=WeatherAPIClient)
        processor = create_weather_processor(api_client=mock_client)
        assert processor.api_client is mock_client