# Integration tests for API endpoints
"""
Integration tests for the weather forecast API.
Tests the complete weather data flow from external API to frontend.
"""

import json
import os
import pytest
import requests
import time
from unittest.mock import patch, MagicMock
import boto3
from moto import mock_dynamodb
import sys

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from lambda_handler import lambda_handler
from weather_service.models import WeatherData, CityConfig
from weather_service.api_client import WeatherAPIClient
from weather_service.cache import WeatherCache
from weather_service.processor import WeatherProcessor


class TestWeatherDataFlow:
    """Test complete weather data flow integration."""

    @pytest.fixture
    def mock_met_no_response(self):
        """Mock response from met.no API."""
        return {
            "properties": {
                "timeseries": [
                    {
                        "time": "2024-01-15T00:00:00Z",
                        "data": {
                            "instant": {
                                "details": {
                                    "air_temperature": -2.0,
                                    "relative_humidity": 75.0,
                                    "wind_speed": 12.0
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

    @pytest.fixture
    def city_config(self):
        """Test city configuration."""
        return CityConfig(
            id="oslo",
            name="Oslo",
            country="Norway",
            coordinates={"lat": 59.9139, "lon": 10.7522}
        )

    @mock_dynamodb
    def test_complete_weather_data_flow(self, mock_met_no_response, city_config):
        """Test complete flow from external API to processed weather data."""
        # Setup mock DynamoDB
        dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
        table = dynamodb.create_table(
            TableName='weather-cache-test',
            KeySchema=[
                {'AttributeName': 'city_id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'city_id', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )

        # Mock external API call
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_met_no_response
            mock_response.status_code = 200
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            # Initialize components
            api_client = WeatherAPIClient(company_website="test.com")
            cache = WeatherCache(table_name='weather-cache-test')
            processor = WeatherProcessor()

            # Test API client
            raw_data = api_client.fetch_weather_data(city_config.coordinates)
            assert raw_data is not None
            assert "properties" in raw_data

            # Test processor
            weather_data = processor.process_weather_data(raw_data, city_config)
            assert isinstance(weather_data, WeatherData)
            assert weather_data.city_id == "oslo"
            assert weather_data.city_name == "Oslo"
            assert weather_data.forecast.temperature.value == -2.0

            # Test cache storage
            cache.store_weather_data(weather_data)

            # Test cache retrieval
            cached_data = cache.get_weather_data("oslo")
            assert cached_data is not None
            assert cached_data.city_id == "oslo"
            assert cached_data.forecast.temperature.value == -2.0

    @mock_dynamodb
    def test_lambda_handler_integration(self, mock_met_no_response):
        """Test Lambda handler with complete integration."""
        # Setup mock DynamoDB
        dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
        table = dynamodb.create_table(
            TableName='weather-cache-test',
            KeySchema=[
                {'AttributeName': 'city_id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'city_id', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )

        # Mock environment variables
        with patch.dict(os.environ, {
            'DYNAMODB_TABLE_NAME': 'weather-cache-test',
            'COMPANY_WEBSITE': 'test.com',
            'LOG_LEVEL': 'INFO'
        }):
            # Mock external API calls
            with patch('requests.get') as mock_get:
                mock_response = MagicMock()
                mock_response.json.return_value = mock_met_no_response
                mock_response.status_code = 200
                mock_response.raise_for_status.return_value = None
                mock_get.return_value = mock_response

                # Test weather endpoint
                event = {
                    'httpMethod': 'GET',
                    'path': '/weather',
                    'headers': {},
                    'queryStringParameters': None
                }
                context = MagicMock()

                response = lambda_handler(event, context)

                assert response['statusCode'] == 200
                body = json.loads(response['body'])
                assert 'cities' in body
                assert len(body['cities']) == 4

                # Verify all cities are present
                city_names = [city['name'] for city in body['cities']]
                expected_cities = ['Oslo', 'Paris', 'London', 'Barcelona']
                for city in expected_cities:
                    assert city in city_names

    def test_health_endpoint_integration(self):
        """Test health endpoint integration."""
        event = {
            'httpMethod': 'GET',
            'path': '/health',
            'headers': {},
            'queryStringParameters': None
        }
        context = MagicMock()

        response = lambda_handler(event, context)

        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['status'] == 'healthy'
        assert 'timestamp' in body
        assert 'version' in body

    @mock_dynamodb
    def test_cache_integration_with_ttl(self, mock_met_no_response, city_config):
        """Test cache integration with TTL functionality."""
        # Setup mock DynamoDB
        dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
        table = dynamodb.create_table(
            TableName='weather-cache-test',
            KeySchema=[
                {'AttributeName': 'city_id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'city_id', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )

        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_met_no_response
            mock_response.status_code = 200
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            cache = WeatherCache(table_name='weather-cache-test')
            processor = WeatherProcessor()

            # Process and store weather data
            weather_data = processor.process_weather_data(mock_met_no_response, city_config)
            cache.store_weather_data(weather_data)

            # Verify data is stored with TTL
            cached_data = cache.get_weather_data("oslo")
            assert cached_data is not None
            assert cached_data.ttl > int(time.time())  # TTL should be in the future

    def test_error_handling_integration(self):
        """Test error handling in complete integration flow."""
        # Test with invalid API response
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            api_client = WeatherAPIClient(company_website="test.com")
            city_config = CityConfig(
                id="oslo",
                name="Oslo",
                country="Norway",
                coordinates={"lat": 59.9139, "lon": 10.7522}
            )

            # Should handle JSON decode error gracefully
            with pytest.raises(json.JSONDecodeError):
                api_client.fetch_weather_data(city_config.coordinates)

    @mock_dynamodb
    def test_cors_headers_integration(self):
        """Test CORS headers in API responses."""
        # Setup mock DynamoDB
        dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
        table = dynamodb.create_table(
            TableName='weather-cache-test',
            KeySchema=[
                {'AttributeName': 'city_id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'city_id', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )

        with patch.dict(os.environ, {
            'DYNAMODB_TABLE_NAME': 'weather-cache-test',
            'COMPANY_WEBSITE': 'test.com'
        }):
            event = {
                'httpMethod': 'GET',
                'path': '/health',
                'headers': {'Origin': 'https://example.com'},
                'queryStringParameters': None
            }
            context = MagicMock()

            response = lambda_handler(event, context)

            assert response['statusCode'] == 200
            assert 'Access-Control-Allow-Origin' in response['headers']
            assert 'Access-Control-Allow-Methods' in response['headers']
            assert 'Access-Control-Allow-Headers' in response['headers']


class TestAPIEndpointIntegration:
    """Test API endpoint integration scenarios."""

    def test_options_request_handling(self):
        """Test OPTIONS request for CORS preflight."""
        event = {
            'httpMethod': 'OPTIONS',
            'path': '/weather',
            'headers': {
                'Origin': 'https://example.com',
                'Access-Control-Request-Method': 'GET'
            },
            'queryStringParameters': None
        }
        context = MagicMock()

        response = lambda_handler(event, context)

        assert response['statusCode'] == 200
        assert 'Access-Control-Allow-Origin' in response['headers']
        assert 'Access-Control-Allow-Methods' in response['headers']

    def test_unsupported_method_handling(self):
        """Test handling of unsupported HTTP methods."""
        event = {
            'httpMethod': 'POST',
            'path': '/weather',
            'headers': {},
            'queryStringParameters': None
        }
        context = MagicMock()

        response = lambda_handler(event, context)

        assert response['statusCode'] == 405
        body = json.loads(response['body'])
        assert 'error' in body
        assert 'Method not allowed' in body['error']

    def test_invalid_path_handling(self):
        """Test handling of invalid API paths."""
        event = {
            'httpMethod': 'GET',
            'path': '/invalid',
            'headers': {},
            'queryStringParameters': None
        }
        context = MagicMock()

        response = lambda_handler(event, context)

        assert response['statusCode'] == 404
        body = json.loads(response['body'])
        assert 'error' in body
        assert 'Not found' in body['error']


class TestExternalAPIIntegration:
    """Test integration with external weather API."""

    def test_met_no_api_integration(self):
        """Test actual integration with met.no API (if available)."""
        # This test can be skipped in CI/CD if external API is not available
        api_client = WeatherAPIClient(company_website="test.com")
        city_config = CityConfig(
            id="oslo",
            name="Oslo",
            country="Norway",
            coordinates={"lat": 59.9139, "lon": 10.7522}
        )

        try:
            # Attempt real API call with timeout
            raw_data = api_client.fetch_weather_data(
                city_config.coordinates,
                timeout=5
            )

            # If successful, verify response structure
            if raw_data:
                assert "properties" in raw_data
                assert "timeseries" in raw_data["properties"]
                assert len(raw_data["properties"]["timeseries"]) > 0

        except (requests.exceptions.RequestException, requests.exceptions.Timeout):
            # Skip test if external API is not available
            pytest.skip("External weather API not available")

    def test_user_agent_header_integration(self):
        """Test that User-Agent header is properly set."""
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = {"properties": {"timeseries": []}}
            mock_response.status_code = 200
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            api_client = WeatherAPIClient(company_website="test.com")
            coordinates = {"lat": 59.9139, "lon": 10.7522}

            api_client.fetch_weather_data(coordinates)

            # Verify User-Agent header was set correctly
            mock_get.assert_called_once()
            call_args = mock_get.call_args
            headers = call_args[1]['headers']
            assert 'User-Agent' in headers
            assert 'weather-forecast-app/1.0' in headers['User-Agent']
            assert 'test.com' in headers['User-Agent']