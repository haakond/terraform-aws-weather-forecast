"""
Unit tests for the simplified Lambda handler.

This module tests the embedded weather service functionality in the Lambda handler,
including weather data fetching, processing, response formatting, and DynamoDB caching.
"""

import json
import os
import pytest
import time
from datetime import datetime, timezone
from unittest.mock import Mock, patch, MagicMock
from moto import mock_aws
import boto3

# Import the Lambda handler and its functions
from src.lambda_handler import (
    lambda_handler,
    handle_weather_request,
    handle_health_request,
    handle_options_request,
    create_response,
    create_error_response,
    fetch_weather_data,
    extract_tomorrow_forecast,
    get_cached_weather_data,
    cache_weather_data,
    process_city_weather_with_cache,
    get_weather_summary,
    get_cities_config,
    WeatherServiceError
)


class TestLambdaHandler:
    """Test cases for the main Lambda handler function."""

    def test_lambda_handler_weather_request(self):
        """Test Lambda handler routing to weather endpoint."""
        event = {
            "httpMethod": "GET",
            "path": "/weather"
        }
        context = Mock()
        context.aws_request_id = "test-request-id"
        context.function_name = "test-function"
        context.function_version = "1"
        context.memory_limit_in_mb = 128

        with patch('src.lambda_handler.get_weather_summary') as mock_summary:
            mock_summary.return_value = {
                "cities": [],
                "lastUpdated": "2024-01-01T12:00:00Z",
                "status": "success"
            }

            response = lambda_handler(event, context)

            assert response["statusCode"] == 200
            assert "application/json" in response["headers"]["Content-Type"]
            assert "Access-Control-Allow-Origin" in response["headers"]

    def test_lambda_handler_health_request(self):
        """Test Lambda handler routing to health endpoint."""
        event = {
            "httpMethod": "GET",
            "path": "/health"
        }
        context = Mock()
        context.aws_request_id = "test-request-id"
        context.function_name = "test-function"
        context.function_version = "1"
        context.memory_limit_in_mb = 128

        response = lambda_handler(event, context)

        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["status"] == "healthy"
        assert body["service"] == "weather-forecast-app"

    def test_lambda_handler_options_request(self):
        """Test Lambda handler CORS preflight handling."""
        event = {
            "httpMethod": "OPTIONS",
            "path": "/weather"
        }
        context = Mock()
        context.aws_request_id = "test-request-id"

        response = lambda_handler(event, context)

        assert response["statusCode"] == 200
        assert response["headers"]["Access-Control-Allow-Origin"] == "*"
        assert "GET,OPTIONS" in response["headers"]["Access-Control-Allow-Methods"]

    def test_lambda_handler_not_found(self):
        """Test Lambda handler 404 for unknown paths."""
        event = {
            "httpMethod": "GET",
            "path": "/unknown"
        }
        context = Mock()
        context.aws_request_id = "test-request-id"

        response = lambda_handler(event, context)

        assert response["statusCode"] == 404
        body = json.loads(response["body"])
        assert body["error"]["type"] == "NotFound"

    def test_lambda_handler_method_not_allowed(self):
        """Test Lambda handler 405 for unsupported methods."""
        event = {
            "httpMethod": "POST",
            "path": "/weather"
        }
        context = Mock()
        context.aws_request_id = "test-request-id"

        response = lambda_handler(event, context)

        assert response["statusCode"] == 405
        body = json.loads(response["body"])
        assert body["error"]["type"] == "MethodNotAllowed"

    def test_lambda_handler_critical_error(self):
        """Test Lambda handler critical error handling."""
        event = {}  # Invalid event structure - will default to GET /
        context = Mock()
        context.aws_request_id = "test-request-id"

        # This will actually succeed as it defaults to weather endpoint
        # Let's test with a truly invalid context instead
        with patch('src.lambda_handler.get_weather_summary') as mock_summary:
            mock_summary.side_effect = Exception("Critical error")
            response = lambda_handler(event, context)

        assert response["statusCode"] == 500
        assert "application/json" in response["headers"]["Content-Type"]
        assert response["headers"]["Cache-Control"] == "max-age=0"  # Critical errors should not be cached


class TestResponseHelpers:
    """Test cases for response helper functions."""

    def test_create_response_dict_body(self):
        """Test creating response with dictionary body."""
        body = {"message": "success", "data": [1, 2, 3]}
        response = create_response(200, body)

        assert response["statusCode"] == 200
        assert response["headers"]["Content-Type"] == "application/json"
        assert response["headers"]["Access-Control-Allow-Origin"] == "*"

        parsed_body = json.loads(response["body"])
        assert parsed_body["message"] == "success"
        assert parsed_body["data"] == [1, 2, 3]

    def test_create_response_string_body(self):
        """Test creating response with string body."""
        response = create_response(200, "simple string")

        assert response["statusCode"] == 200
        assert response["body"] == "simple string"

    def test_create_response_custom_headers(self):
        """Test creating response with custom headers."""
        custom_headers = {"X-Custom-Header": "test-value"}
        response = create_response(200, {}, custom_headers)

        assert response["headers"]["X-Custom-Header"] == "test-value"
        assert response["headers"]["Content-Type"] == "application/json"  # Default still present

    def test_create_response_with_cache_control(self):
        """Test creating response with cache-control header."""
        response = create_response(200, {"data": "test"}, cache_control="max-age=60")

        assert response["statusCode"] == 200
        assert response["headers"]["Cache-Control"] == "max-age=60"
        assert response["headers"]["Content-Type"] == "application/json"

    def test_create_response_cache_control_overrides_custom_headers(self):
        """Test that cache_control parameter overrides custom headers."""
        custom_headers = {"Cache-Control": "max-age=300"}
        response = create_response(200, {}, headers=custom_headers, cache_control="max-age=60")

        # cache_control parameter should take precedence
        assert response["headers"]["Cache-Control"] == "max-age=60"

    def test_create_error_response(self):
        """Test creating standardized error response."""
        response = create_error_response(400, "Bad request", "ValidationError", "req-123")

        assert response["statusCode"] == 400
        assert response["headers"]["Cache-Control"] == "max-age=0"  # Error responses should not be cached
        body = json.loads(response["body"])
        assert body["error"]["type"] == "ValidationError"
        assert body["error"]["message"] == "Bad request"
        assert body["error"]["requestId"] == "req-123"
        assert "timestamp" in body["error"]


class TestWeatherDataFetching:
    """Test cases for weather data fetching functionality."""

    @patch.dict(os.environ, {"COMPANY_WEBSITE": "test.com"})
    @patch('src.lambda_handler.urllib.request.urlopen')
    def test_fetch_weather_data_success(self, mock_urlopen):
        """Test successful weather data fetching."""
        mock_response = Mock()
        mock_response.read.return_value = json.dumps({
            "properties": {
                "timeseries": [
                    {
                        "time": "2024-01-15T12:00:00Z",
                        "data": {
                            "instant": {"details": {"air_temperature": 15.5}},
                            "next_6_hours": {"summary": {"symbol_code": "partlycloudy_day"}}
                        }
                    }
                ]
            }
        }).encode()
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = fetch_weather_data(59.9139, 10.7522)

        assert "properties" in result
        assert "timeseries" in result["properties"]
        mock_urlopen.assert_called_once()

    @patch('src.lambda_handler.urllib.request.urlopen')
    def test_fetch_weather_data_network_error(self, mock_urlopen):
        """Test weather data fetching with network error."""
        mock_urlopen.side_effect = Exception("Network error")

        with pytest.raises(WeatherServiceError, match="Failed to fetch weather data"):
            fetch_weather_data(59.9139, 10.7522)

    @patch('src.lambda_handler.urllib.request.urlopen')
    def test_fetch_weather_data_timeout(self, mock_urlopen):
        """Test weather data fetching with timeout."""
        mock_urlopen.side_effect = TimeoutError("Request timeout")

        with pytest.raises(WeatherServiceError, match="Failed to fetch weather data"):
            fetch_weather_data(59.9139, 10.7522)


class TestWeatherDataProcessing:
    """Test cases for weather data processing functionality."""

    def create_mock_weather_data(self, temperature=15.5, symbol_code="partlycloudy_day"):
        """Create mock weather data for testing."""
        tomorrow = datetime.now(timezone.utc).replace(hour=12, minute=0, second=0, microsecond=0)
        tomorrow = tomorrow.replace(day=tomorrow.day + 1)

        return {
            "properties": {
                "timeseries": [
                    {
                        "time": tomorrow.isoformat().replace("+00:00", "Z"),
                        "data": {
                            "instant": {
                                "details": {
                                    "air_temperature": temperature
                                }
                            },
                            "next_6_hours": {
                                "summary": {
                                    "symbol_code": symbol_code
                                }
                            }
                        }
                    }
                ]
            }
        }

    def test_extract_tomorrow_forecast_success(self):
        """Test successful forecast extraction."""
        weather_data = self.create_mock_weather_data(20.5, "clearsky_day")

        forecast = extract_tomorrow_forecast(weather_data)

        assert forecast["temperature"]["value"] == 20  # Rounded
        assert forecast["temperature"]["unit"] == "celsius"
        assert forecast["condition"] == "clear"
        assert "Clear" in forecast["description"]

    def test_extract_tomorrow_forecast_condition_mapping(self):
        """Test weather condition mapping."""
        test_cases = [
            ("clearsky_day", "clear"),
            ("fair_day", "partly_cloudy"),
            ("partlycloudy_day", "partly_cloudy"),
            ("cloudy", "cloudy"),
            ("rain", "rain"),
            ("snow", "snow"),
            ("fog", "fog"),
            ("unknown_symbol", "unknown")
        ]

        for symbol_code, expected_condition in test_cases:
            weather_data = self.create_mock_weather_data(15.0, symbol_code)
            forecast = extract_tomorrow_forecast(weather_data)
            assert forecast["condition"] == expected_condition

    def test_extract_tomorrow_forecast_no_timeseries(self):
        """Test forecast extraction with no timeseries data."""
        weather_data = {"properties": {"timeseries": []}}

        with pytest.raises(WeatherServiceError, match="No timeseries data found"):
            extract_tomorrow_forecast(weather_data)

    def test_extract_tomorrow_forecast_invalid_data(self):
        """Test forecast extraction with invalid data structure."""
        weather_data = {"invalid": "structure"}

        with pytest.raises(WeatherServiceError, match="Failed to extract forecast"):
            extract_tomorrow_forecast(weather_data)


class TestDynamoDBCaching:
    """Test cases for DynamoDB caching functionality."""

    @patch.dict(os.environ, {"DYNAMODB_TABLE_NAME": "test-weather-cache"})
    @patch('src.lambda_handler.dynamodb')
    def test_cache_weather_data_success(self, mock_dynamodb):
        """Test successful weather data caching."""
        mock_dynamodb.put_item.return_value = {}

        city_data = {
            "cityId": "oslo",
            "cityName": "Oslo",
            "country": "Norway",
            "forecast": {
                "temperature": {"value": 15, "unit": "celsius"},
                "condition": "partly_cloudy",
                "description": "Partly cloudy"
            }
        }

        result = cache_weather_data(city_data)

        assert result is True
        mock_dynamodb.put_item.assert_called_once()

    @patch.dict(os.environ, {}, clear=True)
    def test_cache_weather_data_no_table_name(self):
        """Test caching when no table name is configured."""
        city_data = {"cityId": "oslo", "cityName": "Oslo", "country": "Norway", "forecast": {}}

        result = cache_weather_data(city_data)

        assert result is False

    @patch.dict(os.environ, {"DYNAMODB_TABLE_NAME": "test-weather-cache"})
    @patch('src.lambda_handler.dynamodb')
    def test_get_cached_weather_data_success(self, mock_dynamodb):
        """Test successful retrieval of cached weather data."""
        future_ttl = int(time.time()) + 3600
        mock_dynamodb.get_item.return_value = {
            'Item': {
                'city_id': {'S': 'oslo'},
                'city_name': {'S': 'Oslo'},
                'country': {'S': 'Norway'},
                'forecast': {'S': json.dumps({
                    "temperature": {"value": 15, "unit": "celsius"},
                    "condition": "partly_cloudy"
                })},
                'last_updated': {'S': datetime.now(timezone.utc).isoformat()},
                'ttl': {'N': str(future_ttl)}
            }
        }

        result = get_cached_weather_data("oslo")

        assert result is not None
        assert result["cityId"] == "oslo"
        assert result["cityName"] == "Oslo"
        assert result["forecast"]["temperature"]["value"] == 15

    @patch.dict(os.environ, {"DYNAMODB_TABLE_NAME": "test-weather-cache"})
    @patch('src.lambda_handler.dynamodb')
    def test_get_cached_weather_data_expired(self, mock_dynamodb):
        """Test retrieval of expired cached data."""
        past_ttl = int(time.time()) - 3600
        mock_dynamodb.get_item.return_value = {
            'Item': {
                'city_id': {'S': 'oslo'},
                'city_name': {'S': 'Oslo'},
                'country': {'S': 'Norway'},
                'forecast': {'S': json.dumps({})},
                'last_updated': {'S': datetime.now(timezone.utc).isoformat()},
                'ttl': {'N': str(past_ttl)}
            }
        }

        result = get_cached_weather_data("oslo")

        assert result is None

    @patch.dict(os.environ, {"DYNAMODB_TABLE_NAME": "test-weather-cache"})
    @patch('src.lambda_handler.dynamodb')
    def test_get_cached_weather_data_not_found(self, mock_dynamodb):
        """Test retrieval when no cached data exists."""
        mock_dynamodb.get_item.return_value = {}  # No Item key means not found

        result = get_cached_weather_data("nonexistent")

        assert result is None

    @patch.dict(os.environ, {}, clear=True)
    def test_get_cached_weather_data_no_table_name(self):
        """Test retrieval when no table name is configured."""
        result = get_cached_weather_data("oslo")

        assert result is None


class TestCityWeatherProcessing:
    """Test cases for city weather processing with caching."""

    @patch('src.lambda_handler.get_cached_weather_data')
    def test_process_city_weather_with_cache_hit(self, mock_get_cached):
        """Test processing city weather with cache hit."""
        cached_data = {
            "cityId": "oslo",
            "cityName": "Oslo",
            "country": "Norway",
            "forecast": {"temperature": {"value": 15, "unit": "celsius"}}
        }
        mock_get_cached.return_value = cached_data

        city_config = {
            "id": "oslo",
            "name": "Oslo",
            "country": "Norway",
            "coordinates": {"latitude": 59.9139, "longitude": 10.7522}
        }

        result = process_city_weather_with_cache(city_config)

        assert result == cached_data
        mock_get_cached.assert_called_once_with("oslo")

    @patch('src.lambda_handler.cache_weather_data')
    @patch('src.lambda_handler.extract_tomorrow_forecast')
    @patch('src.lambda_handler.fetch_weather_data')
    @patch('src.lambda_handler.get_cached_weather_data')
    def test_process_city_weather_with_cache_miss(self, mock_get_cached, mock_fetch, mock_extract, mock_cache):
        """Test processing city weather with cache miss."""
        mock_get_cached.return_value = None
        mock_fetch.return_value = {"properties": {"timeseries": []}}
        mock_extract.return_value = {
            "temperature": {"value": 20, "unit": "celsius"},
            "condition": "clear",
            "description": "Clear sky"
        }
        mock_cache.return_value = True

        city_config = {
            "id": "paris",
            "name": "Paris",
            "country": "France",
            "coordinates": {"latitude": 48.8566, "longitude": 2.3522}
        }

        result = process_city_weather_with_cache(city_config)

        assert result["cityId"] == "paris"
        assert result["cityName"] == "Paris"
        assert result["forecast"]["temperature"]["value"] == 20
        mock_fetch.assert_called_once_with(48.8566, 2.3522)
        mock_cache.assert_called_once()

    @patch('src.lambda_handler.fetch_weather_data')
    @patch('src.lambda_handler.get_cached_weather_data')
    def test_process_city_weather_with_api_error(self, mock_get_cached, mock_fetch):
        """Test processing city weather with API error."""
        mock_get_cached.return_value = None
        mock_fetch.side_effect = WeatherServiceError("API error")

        city_config = {
            "id": "london",
            "name": "London",
            "country": "United Kingdom",
            "coordinates": {"latitude": 51.5074, "longitude": -0.1278}
        }

        result = process_city_weather_with_cache(city_config)

        assert result["cityId"] == "london"
        assert result["cityName"] == "London"
        assert "error" in result
        assert result["forecast"]["condition"] == "unknown"
        assert result["forecast"]["description"] == "Data unavailable"


class TestWeatherSummary:
    """Test cases for weather summary functionality."""

    @patch('src.lambda_handler.process_city_weather_with_cache')
    @patch('src.lambda_handler.get_cities_config')
    def test_get_weather_summary_success(self, mock_get_cities, mock_process_city):
        """Test successful weather summary generation."""
        mock_get_cities.return_value = [
            {"id": "oslo", "name": "Oslo", "country": "Norway", "coordinates": {"latitude": 59.9139, "longitude": 10.7522}},
            {"id": "paris", "name": "Paris", "country": "France", "coordinates": {"latitude": 48.8566, "longitude": 2.3522}}
        ]

        mock_process_city.side_effect = [
            {"cityId": "oslo", "cityName": "Oslo", "country": "Norway", "forecast": {}},
            {"cityId": "paris", "cityName": "Paris", "country": "France", "forecast": {}}
        ]

        with patch('time.sleep'):  # Mock sleep to speed up tests
            result = get_weather_summary()

        assert result["status"] == "success"
        assert len(result["cities"]) == 2
        assert result["cities"][0]["cityId"] == "oslo"
        assert result["cities"][1]["cityId"] == "paris"
        assert "lastUpdated" in result

    @patch('src.lambda_handler.process_city_weather_with_cache')
    @patch('src.lambda_handler.get_cities_config')
    def test_get_weather_summary_with_errors(self, mock_get_cities, mock_process_city):
        """Test weather summary generation with some city errors."""
        mock_get_cities.return_value = [
            {"id": "oslo", "name": "Oslo", "country": "Norway", "coordinates": {"latitude": 59.9139, "longitude": 10.7522}}
        ]

        mock_process_city.return_value = {
            "cityId": "oslo",
            "cityName": "Oslo",
            "country": "Norway",
            "forecast": {},
            "error": "API error"
        }

        with patch('time.sleep'):  # Mock sleep to speed up tests
            result = get_weather_summary()

        assert result["status"] == "partial_failure"
        assert result["hasErrors"] is True
        assert len(result["cities"]) == 1
        # Should still include cities with errors
        assert result["cities"][0]["cityId"] == "oslo"

    @patch('src.lambda_handler.process_city_weather_with_cache')
    @patch('src.lambda_handler.get_cities_config')
    def test_get_weather_summary_no_errors(self, mock_get_cities, mock_process_city):
        """Test weather summary generation with no errors."""
        mock_get_cities.return_value = [
            {"id": "oslo", "name": "Oslo", "country": "Norway", "coordinates": {"latitude": 59.9139, "longitude": 10.7522}}
        ]

        mock_process_city.return_value = {
            "cityId": "oslo",
            "cityName": "Oslo",
            "country": "Norway",
            "forecast": {}
            # No error key means success
        }

        with patch('time.sleep'):  # Mock sleep to speed up tests
            result = get_weather_summary()

        assert result["status"] == "success"
        assert result["hasErrors"] is False
        assert len(result["cities"]) == 1
        assert result["cities"][0]["cityId"] == "oslo"


class TestCitiesConfiguration:
    """Test cases for cities configuration functionality."""

    @patch.dict(os.environ, {}, clear=True)
    def test_get_cities_config_default(self):
        """Test getting default cities configuration."""
        cities = get_cities_config()

        assert len(cities) == 4
        city_ids = [city["id"] for city in cities]
        expected_ids = ["oslo", "paris", "london", "barcelona"]
        assert set(city_ids) == set(expected_ids)

        # Verify Oslo configuration
        oslo = next(city for city in cities if city["id"] == "oslo")
        assert oslo["name"] == "Oslo"
        assert oslo["country"] == "Norway"
        assert oslo["coordinates"]["latitude"] == 59.9139
        assert oslo["coordinates"]["longitude"] == 10.7522

    @patch.dict(os.environ, {"CITIES_CONFIG": json.dumps([
        {
            "id": "tokyo",
            "name": "Tokyo",
            "country": "Japan",
            "coordinates": {"latitude": 35.6762, "longitude": 139.6503}
        }
    ])})
    def test_get_cities_config_custom(self):
        """Test getting custom cities configuration from environment."""
        cities = get_cities_config()

        assert len(cities) == 1
        assert cities[0]["id"] == "tokyo"
        assert cities[0]["name"] == "Tokyo"
        assert cities[0]["country"] == "Japan"

    @patch.dict(os.environ, {"CITIES_CONFIG": "invalid json"})
    def test_get_cities_config_invalid_json(self):
        """Test fallback to defaults with invalid JSON configuration."""
        cities = get_cities_config()

        # Should fall back to defaults
        assert len(cities) == 4
        assert cities[0]["id"] == "oslo"


class TestRequestHandlers:
    """Test cases for specific request handlers."""

    @patch('src.lambda_handler.get_weather_summary')
    def test_handle_weather_request_success(self, mock_get_summary):
        """Test successful weather request handling."""
        mock_get_summary.return_value = {
            "cities": [],
            "lastUpdated": "2024-01-01T12:00:00Z",
            "status": "success",
            "hasErrors": False
        }

        event = {"httpMethod": "GET", "path": "/weather"}
        context = Mock()
        context.aws_request_id = "test-request-id"

        response = handle_weather_request(event, context)

        assert response["statusCode"] == 200
        assert response["headers"]["Cache-Control"] == "max-age=60"  # Successful response should be cached
        body = json.loads(response["body"])
        assert body["requestId"] == "test-request-id"
        assert body["version"] == "1.0.0"
        assert body["service"] == "weather-forecast-app"

    @patch('src.lambda_handler.get_weather_summary')
    def test_handle_weather_request_success_with_errors(self, mock_get_summary):
        """Test weather request handling with partial errors."""
        mock_get_summary.return_value = {
            "cities": [
                {"cityId": "oslo", "forecast": {}},
                {"cityId": "paris", "forecast": {}, "error": "API error"}
            ],
            "lastUpdated": "2024-01-01T12:00:00Z",
            "status": "partial_failure",
            "hasErrors": True
        }

        event = {"httpMethod": "GET", "path": "/weather"}
        context = Mock()
        context.aws_request_id = "test-request-id"

        response = handle_weather_request(event, context)

        assert response["statusCode"] == 200
        assert response["headers"]["Cache-Control"] == "max-age=0"  # Response with errors should not be cached
        body = json.loads(response["body"])
        assert body["hasErrors"] is True

    @patch('src.lambda_handler.get_weather_summary')
    def test_handle_weather_request_service_error(self, mock_get_summary):
        """Test weather request handling with service error."""
        mock_get_summary.side_effect = WeatherServiceError("Service unavailable")

        event = {"httpMethod": "GET", "path": "/weather"}
        context = Mock()
        context.aws_request_id = "test-request-id"

        response = handle_weather_request(event, context)

        assert response["statusCode"] == 502
        body = json.loads(response["body"])
        assert body["error"]["type"] == "WeatherServiceError"
        assert "unavailable" in body["error"]["message"]

    @patch('src.lambda_handler.get_weather_summary')
    def test_handle_weather_request_unexpected_error(self, mock_get_summary):
        """Test weather request handling with unexpected error."""
        mock_get_summary.side_effect = Exception("Unexpected error")

        event = {"httpMethod": "GET", "path": "/weather"}
        context = Mock()
        context.aws_request_id = "test-request-id"

        response = handle_weather_request(event, context)

        assert response["statusCode"] == 500
        body = json.loads(response["body"])
        assert body["error"]["type"] == "InternalError"

    @patch.dict(os.environ, {"COMPANY_WEBSITE": "test.com", "AWS_REGION": "eu-west-1"})
    def test_handle_health_request_success(self):
        """Test successful health request handling."""
        event = {"httpMethod": "GET", "path": "/health"}
        context = Mock()
        context.aws_request_id = "test-request-id"
        context.function_name = "weather-function"
        context.function_version = "1"
        context.memory_limit_in_mb = 256

        response = handle_health_request(event, context)

        assert response["statusCode"] == 200
        assert response["headers"]["Cache-Control"] == "max-age=0"  # Health endpoints should not be cached
        body = json.loads(response["body"])
        assert body["status"] == "healthy"
        assert body["environment"]["company_website"] == "test.com"
        assert body["environment"]["aws_region"] == "eu-west-1"
        assert body["environment"]["function_name"] == "weather-function"

    def test_handle_options_request(self):
        """Test CORS preflight OPTIONS request handling."""
        event = {"httpMethod": "OPTIONS", "path": "/weather"}
        context = Mock()
        context.aws_request_id = "test-request-id"

        response = handle_options_request(event, context)

        assert response["statusCode"] == 200
        assert response["headers"]["Access-Control-Allow-Origin"] == "*"
        assert "GET,OPTIONS" in response["headers"]["Access-Control-Allow-Methods"]
        assert response["headers"]["Access-Control-Max-Age"] == "86400"
        assert response["headers"]["Cache-Control"] == "max-age=86400"  # CORS preflight can be cached


if __name__ == "__main__":
    pytest.main([__file__])