"""
Unit tests for the weather data processor - Core functionality only.
"""

import pytest
from unittest.mock import MagicMock

from src.weather_service.processor import WeatherProcessor, create_weather_processor
from src.weather_service.api_client import WeatherAPIClient


class TestWeatherProcessor:
    """Test cases for the WeatherProcessor class - basic functionality only."""

    def test_processor_initialization(self):
        """Test processor initialization."""
        processor = WeatherProcessor()
        assert isinstance(processor.api_client, WeatherAPIClient)

        # Test with custom client
        mock_client = MagicMock(spec=WeatherAPIClient)
        processor = WeatherProcessor(api_client=mock_client)
        assert processor.api_client is mock_client


class TestCreateWeatherProcessor:
    """Test cases for the create_weather_processor convenience function."""

    def test_create_weather_processor_default(self):
        """Test creating a processor with default parameters."""
        processor = create_weather_processor()

        assert isinstance(processor, WeatherProcessor)
        assert isinstance(processor.api_client, WeatherAPIClient)

    def test_create_weather_processor_custom_client(self):
        """Test creating a processor with custom API client."""
        mock_client = MagicMock(spec=WeatherAPIClient)
        processor = create_weather_processor(api_client=mock_client)

        assert isinstance(processor, WeatherProcessor)
        assert processor.api_client is mock_client