"""
Unit tests for the weather API client.

Tests cover HTTP client functionality, error handling, and User-Agent configuration.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aiohttp import ClientResponseError, ClientConnectionError, ServerTimeoutError

from src.weather_service.api_client import (
    WeatherAPIClient, WeatherAPIError, RateLimitError, APIConnectionError,
    MalformedResponseError, RateLimiter, create_weather_client
)


class TestRateLimiter:
    """Test cases for the RateLimiter class."""

    @pytest.mark.asyncio
    async def test_rate_limiter_initialization(self):
        """Test that rate limiter initializes correctly."""
        limiter = RateLimiter(max_requests=5, time_window=1.0)
        assert limiter.max_requests == 5
        assert limiter.time_window == 1.0
        assert limiter._requests == []

    @pytest.mark.asyncio
    async def test_rate_limiter_allows_single_request(self):
        """Test that rate limiter allows a single request."""
        limiter = RateLimiter(max_requests=5, time_window=1.0)
        # Should not raise any exception
        await limiter.acquire()


class TestWeatherAPIClient:
    """Test cases for the WeatherAPIClient class."""

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
            company_website="example.com",
            timeout=60.0,
            max_retries=5
        )

        assert client.company_website == "example.com"
        assert client.timeout == 60.0
        assert client.max_retries == 5
        assert client.user_agent == "weather-forecast-app/1.0 (+https://example.com)"

    @patch.dict('os.environ', {'COMPANY_WEBSITE': 'env-example.com'})
    def test_client_uses_environment_variable(self):
        """Test that client uses environment variable for company website."""
        client = WeatherAPIClient()
        assert client.company_website == "env-example.com"
        assert client.user_agent == "weather-forecast-app/1.0 (+https://env-example.com)"

    def test_user_agent_getter(self):
        """Test the user agent getter method."""
        client = WeatherAPIClient(company_website="test.com")
        assert client.get_user_agent() == "weather-forecast-app/1.0 (+https://test.com)"

    def test_company_website_getter(self):
        """Test the company website getter method."""
        client = WeatherAPIClient(company_website="test.com")
        assert client.get_company_website() == "test.com"

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test that client works as an async context manager."""
        async with WeatherAPIClient() as client:
            assert isinstance(client, WeatherAPIClient)

    @pytest.mark.asyncio
    async def test_close_method(self):
        """Test the close method doesn't raise errors."""
        client = WeatherAPIClient()
        # Should not raise any exception
        await client.close()

    def test_should_retry_logic(self):
        """Test the retry logic for different exception types."""
        client = WeatherAPIClient()

        # Should retry on connection errors
        assert client._should_retry(ClientConnectionError())
        assert client._should_retry(ServerTimeoutError())
        assert client._should_retry(asyncio.TimeoutError())

        # Should retry on server errors (5xx)
        server_error = ClientResponseError(
            request_info=MagicMock(),
            history=(),
            status=500
        )
        assert client._should_retry(server_error)

        # Should retry on rate limiting (429)
        rate_limit_error = ClientResponseError(
            request_info=MagicMock(),
            history=(),
            status=429
        )
        assert client._should_retry(rate_limit_error)

        # Should not retry on client errors (4xx except 429)
        client_error = ClientResponseError(
            request_info=MagicMock(),
            history=(),
            status=400
        )
        assert not client._should_retry(client_error)

    @pytest.mark.asyncio
    async def test_get_weather_forecast_success(self):
        """Test successful weather forecast retrieval."""
        mock_response_data = {
            "properties": {
                "timeseries": [
                    {
                        "time": "2024-01-15T12:00:00Z",
                        "data": {
                            "instant": {
                                "details": {
                                    "air_temperature": 5.0
                                }
                            }
                        }
                    }
                ]
            }
        }

        client = WeatherAPIClient()

        with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response_data

            result = await client.get_weather_forecast(59.9139, 10.7522)

            assert result == mock_response_data
            mock_request.assert_called_once_with(
                "https://api.met.no/weatherapi/locationforecast/2.0/compact",
                {"lat": 59.9139, "lon": 10.7522}
            )

    @pytest.mark.asyncio
    async def test_get_weather_forecast_with_altitude(self):
        """Test weather forecast retrieval with altitude parameter."""
        mock_response_data = {"properties": {"timeseries": []}}

        client = WeatherAPIClient()

        with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response_data

            await client.get_weather_forecast(59.9139, 10.7522, altitude=100)

            mock_request.assert_called_once_with(
                "https://api.met.no/weatherapi/locationforecast/2.0/compact",
                {"lat": 59.9139, "lon": 10.7522, "altitude": 100}
            )

    @pytest.mark.asyncio
    async def test_get_weather_forecast_invalid_coordinates(self):
        """Test weather forecast with invalid coordinates."""
        client = WeatherAPIClient()

        # Invalid latitude
        with pytest.raises(ValueError, match="Latitude must be between -90 and 90"):
            await client.get_weather_forecast(91.0, 10.0)

        # Invalid longitude
        with pytest.raises(ValueError, match="Longitude must be between -180 and 180"):
            await client.get_weather_forecast(59.0, 181.0)

    @pytest.mark.asyncio
    async def test_get_weather_forecast_invalid_altitude(self):
        """Test weather forecast with invalid altitude."""
        client = WeatherAPIClient()

        with pytest.raises(ValueError, match="Altitude must be between -500 and 9000"):
            await client.get_weather_forecast(59.0, 10.0, altitude=10000)

    @pytest.mark.asyncio
    async def test_get_weather_forecast_malformed_response(self):
        """Test handling of malformed API response."""
        client = WeatherAPIClient()

        # Test non-dict response
        with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = "not a dict"

            with pytest.raises(MalformedResponseError, match="Response is not a JSON object"):
                await client.get_weather_forecast(59.0, 10.0)

        # Test missing properties field
        with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"no_properties": True}

            with pytest.raises(MalformedResponseError, match="Response missing 'properties' field"):
                await client.get_weather_forecast(59.0, 10.0)

        # Test missing timeseries field
        with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"properties": {"no_timeseries": True}}

            with pytest.raises(MalformedResponseError, match="Response missing 'timeseries' field"):
                await client.get_weather_forecast(59.0, 10.0)

    @pytest.mark.asyncio
    async def test_get_weather_for_city_success(self):
        """Test successful weather retrieval for a city."""
        city_config = {
            "id": "oslo",
            "name": "Oslo",
            "coordinates": {"lat": 59.9139, "lon": 10.7522}
        }

        mock_response_data = {"properties": {"timeseries": []}}

        client = WeatherAPIClient()

        with patch.object(client, 'get_weather_forecast', new_callable=AsyncMock) as mock_forecast:
            mock_forecast.return_value = mock_response_data

            result = await client.get_weather_for_city(city_config)

            assert result == mock_response_data
            mock_forecast.assert_called_once_with(59.9139, 10.7522)

    @pytest.mark.asyncio
    async def test_get_weather_for_city_latitude_longitude_format(self):
        """Test weather retrieval with latitude/longitude coordinate format."""
        city_config = {
            "id": "oslo",
            "name": "Oslo",
            "coordinates": {"latitude": 59.9139, "longitude": 10.7522}
        }

        client = WeatherAPIClient()

        with patch.object(client, 'get_weather_forecast', new_callable=AsyncMock) as mock_forecast:
            mock_forecast.return_value = {"properties": {"timeseries": []}}

            await client.get_weather_for_city(city_config)

            mock_forecast.assert_called_once_with(59.9139, 10.7522)

    @pytest.mark.asyncio
    async def test_get_weather_for_city_invalid_config(self):
        """Test weather retrieval with invalid city configuration."""
        client = WeatherAPIClient()

        # Non-dict config
        with pytest.raises(ValueError, match="City configuration must be a dictionary"):
            await client.get_weather_for_city("not a dict")

        # Missing coordinates
        with pytest.raises(ValueError, match="City configuration missing 'coordinates' field"):
            await client.get_weather_for_city({"id": "oslo"})

        # Invalid coordinate format
        with pytest.raises(ValueError, match="City coordinates must include"):
            await client.get_weather_for_city({
                "id": "oslo",
                "coordinates": {"invalid": "format"}
            })

    @pytest.mark.asyncio
    async def test_make_request_mocked(self):
        """Test that _make_request can be mocked successfully."""
        client = WeatherAPIClient()

        mock_response_data = {"test": "data"}

        with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response_data

            result = await client._make_request("http://test.com", {"param": "value"})

            assert result == mock_response_data


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


class TestWeatherAPIExceptions:
    """Test cases for weather API exception classes."""

    def test_weather_api_error(self):
        """Test WeatherAPIError exception."""
        error = WeatherAPIError("Test error")
        assert str(error) == "Test error"
        assert isinstance(error, Exception)

    def test_rate_limit_error(self):
        """Test RateLimitError exception."""
        error = RateLimitError("Rate limited")
        assert str(error) == "Rate limited"
        assert isinstance(error, WeatherAPIError)

    def test_api_connection_error(self):
        """Test APIConnectionError exception."""
        error = APIConnectionError("Connection failed")
        assert str(error) == "Connection failed"
        assert isinstance(error, WeatherAPIError)

    def test_malformed_response_error(self):
        """Test MalformedResponseError exception."""
        error = MalformedResponseError("Invalid response")
        assert str(error) == "Invalid response"
        assert isinstance(error, WeatherAPIError)