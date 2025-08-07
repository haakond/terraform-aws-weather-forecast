"""
Unit tests for the Lambda handler.

Tests the main Lambda function handler, including routing, error handling,
and response formatting.
"""

import json
import os
import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

# Import the module under test
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from lambda_handler import (
    lambda_handler, handle_health_request, handle_options_request,
    create_response, create_error_response, get_weather_processor
)
from weather_service import WeatherAPIError, ValidationError


class TestLambdaHandler:
    """Test cases for the main Lambda handler function."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_context = Mock()
        self.mock_context.aws_request_id = "test-request-id-123"
        self.mock_context.function_name = "weather-forecast-app"
        self.mock_context.function_version = "1"
        self.mock_context.memory_limit_in_mb = 512

    def test_health_endpoint(self):
        """Test the /health endpoint returns proper health status."""
        event = {
            "httpMethod": "GET",
            "path": "/health"
        }

        with patch.dict(os.environ, {"COMPANY_WEBSITE": "test.com", "AWS_REGION": "us-east-1"}):
            response = lambda_handler(event, self.mock_context)

        assert response["statusCode"] == 200

        body = json.loads(response["body"])
        assert body["status"] == "healthy"
        assert body["service"] == "weather-forecast-app"
        assert body["requestId"] == "test-request-id-123"
        assert body["environment"]["company_website"] == "test.com"
        assert body["environment"]["aws_region"] == "us-east-1"
        assert body["environment"]["function_name"] == "weather-forecast-app"

    def test_options_request(self):
        """Test CORS preflight OPTIONS request."""
        event = {
            "httpMethod": "OPTIONS",
            "path": "/"
        }

        response = lambda_handler(event, self.mock_context)

        assert response["statusCode"] == 200
        assert "Access-Control-Allow-Origin" in response["headers"]
        assert response["headers"]["Access-Control-Allow-Origin"] == "*"
        assert "Access-Control-Allow-Methods" in response["headers"]
        assert "GET,OPTIONS" in response["headers"]["Access-Control-Allow-Methods"]

    @patch('lambda_handler.get_weather_processor')
    def test_weather_endpoint_success(self, mock_get_processor):
        """Test successful weather data request."""
        # Mock weather processor
        mock_processor = Mock()
        mock_processor.get_weather_summary = AsyncMock(return_value={
            "timestamp": "2024-01-15T10:30:00Z",
            "cities_count": 4,
            "cities": [
                {"id": "oslo", "name": "Oslo", "temperature": {"value": -2}},
                {"id": "paris", "name": "Paris", "temperature": {"value": 5}},
                {"id": "london", "name": "London", "temperature": {"value": 8}},
                {"id": "barcelona", "name": "Barcelona", "temperature": {"value": 15}}
            ],
            "status": "success"
        })
        mock_get_processor.return_value = mock_processor

        event = {
            "httpMethod": "GET",
            "path": "/weather"
        }

        response = lambda_handler(event, self.mock_context)

        assert response["statusCode"] == 200

        body = json.loads(response["body"])
        assert body["status"] == "success"
        assert body["cities_count"] == 4
        assert body["requestId"] == "test-request-id-123"
        assert body["version"] == "1.0.0"
        assert body["service"] == "weather-forecast-app"
        assert len(body["cities"]) == 4

    @patch('lambda_handler.get_weather_processor')
    def test_weather_endpoint_api_error(self, mock_get_processor):
        """Test weather endpoint with API error."""
        # Mock weather processor to raise WeatherAPIError
        mock_processor = Mock()
        mock_processor.get_weather_summary = AsyncMock(side_effect=WeatherAPIError("API unavailable"))
        mock_get_processor.return_value = mock_processor

        event = {
            "httpMethod": "GET",
            "path": "/weather"
        }

        response = lambda_handler(event, self.mock_context)

        assert response["statusCode"] == 502

        body = json.loads(response["body"])
        assert body["error"]["type"] == "WeatherAPIError"
        assert body["error"]["message"] == "Weather service temporarily unavailable"
        assert body["error"]["requestId"] == "test-request-id-123"

    @patch('lambda_handler.get_weather_processor')
    def test_weather_endpoint_validation_error(self, mock_get_processor):
        """Test weather endpoint with validation error."""
        # Mock weather processor to raise ValidationError
        mock_processor = Mock()
        mock_processor.get_weather_summary = AsyncMock(side_effect=ValidationError("Invalid data"))
        mock_get_processor.return_value = mock_processor

        event = {
            "httpMethod": "GET",
            "path": "/weather"
        }

        response = lambda_handler(event, self.mock_context)

        assert response["statusCode"] == 500

        body = json.loads(response["body"])
        assert body["error"]["type"] == "ValidationError"
        assert body["error"]["message"] == "Weather data processing error"
        assert body["error"]["requestId"] == "test-request-id-123"

    def test_method_not_allowed(self):
        """Test unsupported HTTP method."""
        event = {
            "httpMethod": "POST",
            "path": "/weather"
        }

        response = lambda_handler(event, self.mock_context)

        assert response["statusCode"] == 405

        body = json.loads(response["body"])
        assert body["error"]["type"] == "MethodNotAllowed"
        assert "POST" in body["error"]["message"]

    def test_path_not_found(self):
        """Test unknown path."""
        event = {
            "httpMethod": "GET",
            "path": "/unknown"
        }

        response = lambda_handler(event, self.mock_context)

        assert response["statusCode"] == 404

        body = json.loads(response["body"])
        assert body["error"]["type"] == "NotFound"
        assert "/unknown" in body["error"]["message"]

    def test_root_path_routes_to_weather(self):
        """Test that root path routes to weather endpoint."""
        with patch('lambda_handler.get_weather_processor') as mock_get_processor:
            # Mock weather processor
            mock_processor = Mock()
            mock_processor.get_weather_summary = AsyncMock(return_value={
                "status": "success",
                "cities_count": 4,
                "cities": []
            })
            mock_get_processor.return_value = mock_processor

            event = {
                "httpMethod": "GET",
                "path": "/"
            }

            response = lambda_handler(event, self.mock_context)

            assert response["statusCode"] == 200
            body = json.loads(response["body"])
            assert body["status"] == "success"


class TestResponseHelpers:
    """Test cases for response helper functions."""

    def test_create_response(self):
        """Test create_response function."""
        body = {"message": "test"}
        response = create_response(200, body)

        assert response["statusCode"] == 200
        assert response["headers"]["Content-Type"] == "application/json"
        assert response["headers"]["Access-Control-Allow-Origin"] == "*"

        parsed_body = json.loads(response["body"])
        assert parsed_body == body

    def test_create_response_with_custom_headers(self):
        """Test create_response with custom headers."""
        body = {"message": "test"}
        custom_headers = {"X-Custom-Header": "custom-value"}
        response = create_response(200, body, custom_headers)

        assert response["headers"]["X-Custom-Header"] == "custom-value"
        assert response["headers"]["Content-Type"] == "application/json"  # Should still have defaults

    def test_create_error_response(self):
        """Test create_error_response function."""
        response = create_error_response(400, "Bad request", "BadRequest", "req-123")

        assert response["statusCode"] == 400

        body = json.loads(response["body"])
        assert body["error"]["type"] == "BadRequest"
        assert body["error"]["message"] == "Bad request"
        assert body["error"]["requestId"] == "req-123"
        assert "timestamp" in body["error"]

    def test_create_error_response_without_request_id(self):
        """Test create_error_response without request ID."""
        response = create_error_response(500, "Server error")

        body = json.loads(response["body"])
        assert body["error"]["type"] == "Error"  # Default type
        assert body["error"]["message"] == "Server error"
        assert "requestId" not in body["error"]


class TestHealthHandler:
    """Test cases for the health check handler."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_context = Mock()
        self.mock_context.aws_request_id = "health-request-123"
        self.mock_context.function_name = "weather-app"
        self.mock_context.function_version = "2"
        self.mock_context.memory_limit_in_mb = 256

    def test_handle_health_request(self):
        """Test health request handler."""
        event = {}

        with patch.dict(os.environ, {"COMPANY_WEBSITE": "example.com"}):
            response = handle_health_request(event, self.mock_context)

        assert response["statusCode"] == 200

        body = json.loads(response["body"])
        assert body["status"] == "healthy"
        assert body["requestId"] == "health-request-123"
        assert body["environment"]["company_website"] == "example.com"
        assert body["environment"]["function_name"] == "weather-app"
        assert body["environment"]["function_version"] == "2"
        assert body["environment"]["memory_limit"] == 256


class TestOptionsHandler:
    """Test cases for the OPTIONS handler."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_context = Mock()
        self.mock_context.aws_request_id = "options-request-123"

    def test_handle_options_request(self):
        """Test OPTIONS request handler."""
        event = {}
        response = handle_options_request(event, self.mock_context)

        assert response["statusCode"] == 200
        assert response["headers"]["Access-Control-Allow-Origin"] == "*"
        assert "GET,OPTIONS" in response["headers"]["Access-Control-Allow-Methods"]
        assert response["headers"]["Access-Control-Max-Age"] == "86400"


class TestWeatherProcessorCreation:
    """Test cases for weather processor creation and configuration."""

    def teardown_method(self):
        """Clean up global state."""
        # Reset global processor
        import lambda_handler
        lambda_handler._weather_processor = None

    @patch('lambda_handler.create_weather_client')
    @patch('lambda_handler.create_weather_processor')
    def test_get_weather_processor_creation(self, mock_create_processor, mock_create_client):
        """Test weather processor creation with proper configuration."""
        mock_client = Mock()
        mock_client.get_user_agent.return_value = "weather-forecast-app/1.0 (+https://test.com)"
        mock_create_client.return_value = mock_client

        mock_processor = Mock()
        mock_create_processor.return_value = mock_processor

        with patch.dict(os.environ, {"COMPANY_WEBSITE": "test.com"}):
            processor = get_weather_processor()

        # Verify client was created with correct parameters
        mock_create_client.assert_called_once_with(
            company_website="test.com",
            timeout=25.0,
            max_retries=2
        )

        # Verify processor was created with the client
        mock_create_processor.assert_called_once_with(api_client=mock_client)

        assert processor == mock_processor

    @patch('lambda_handler.create_weather_client')
    @patch('lambda_handler.create_weather_processor')
    def test_get_weather_processor_reuse(self, mock_create_processor, mock_create_client):
        """Test that weather processor is reused across calls."""
        mock_client = Mock()
        mock_client.get_user_agent.return_value = "weather-forecast-app/1.0 (+https://example.com)"
        mock_create_client.return_value = mock_client

        mock_processor = Mock()
        mock_create_processor.return_value = mock_processor

        # First call should create processor
        processor1 = get_weather_processor()

        # Second call should return same processor
        processor2 = get_weather_processor()

        assert processor1 == processor2
        assert mock_create_processor.call_count == 1  # Should only be called once

    @patch('lambda_handler.create_weather_client')
    @patch('lambda_handler.create_weather_processor')
    def test_get_weather_processor_default_website(self, mock_create_processor, mock_create_client):
        """Test weather processor creation with default company website."""
        mock_client = Mock()
        mock_client.get_user_agent.return_value = "weather-forecast-app/1.0 (+https://example.com)"
        mock_create_client.return_value = mock_client

        mock_processor = Mock()
        mock_create_processor.return_value = mock_processor

        # Don't set COMPANY_WEBSITE environment variable
        with patch.dict(os.environ, {}, clear=True):
            processor = get_weather_processor()

        # Should use default website
        mock_create_client.assert_called_once_with(
            company_website="example.com",
            timeout=25.0,
            max_retries=2
        )


if __name__ == "__main__":
    pytest.main([__file__])