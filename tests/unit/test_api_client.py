"""
Unit tests for the weather API client - Core functionality only.
"""

import pytest
from src.weather_service.api_client import WeatherAPIClient, create_weather_client


class TestWeatherAPIClient:
    """Test cases for the WeatherAPIClient class - basic functionality only."""

    def test_client_initialization_default_values(self):
        """Test client initialization with default values."""
        client = WeatherAPIClient()

        assert client.company_website == "example.com"
        assert client.timeout == WeatherAPIClient.DEFAULT_TIMEOUT
        assert client.max_retries == WeatherAPIClient.MAX_RETRIES
        assert client.user_agent == "weather-forecast-app/1.0 (+https://example.com)"

    def test_client_initialization_custom_values(self):
        """Test client initialization with custom values."""
        client = WeatherAPIClient(
            company_website="test.com",
            timeout=60.0,
            max_retries=5
        )

        assert client.company_website == "test.com"
        assert client.timeout == 60.0
        assert client.max_retries == 5
        assert client.user_agent == "weather-forecast-app/1.0 (+https://test.com)"

    def test_user_agent_getter(self):
        """Test the user agent getter method."""
        client = WeatherAPIClient(company_website="test.com")
        assert client.get_user_agent() == "weather-forecast-app/1.0 (+https://test.com)"

    def test_company_website_getter(self):
        """Test the company website getter method."""
        client = WeatherAPIClient(company_website="test.com")
        assert client.get_company_website() == "test.com"


class TestCreateWeatherClient:
    """Test cases for the create_weather_client convenience function."""

    def test_create_weather_client_default(self):
        """Test creating a client with default parameters."""
        client = create_weather_client()

        assert isinstance(client, WeatherAPIClient)
        assert client.company_website == "example.com"
        assert client.timeout == WeatherAPIClient.DEFAULT_TIMEOUT
        assert client.max_retries == WeatherAPIClient.MAX_RETRIES

    def test_create_weather_client_custom(self):
        """Test creating a client with custom parameters."""
        client = create_weather_client(
            company_website="custom.com",
            timeout=45.0,
            max_retries=2
        )

        assert isinstance(client, WeatherAPIClient)
        assert client.company_website == "custom.com"
        assert client.timeout == 45.0
        assert client.max_retries == 2