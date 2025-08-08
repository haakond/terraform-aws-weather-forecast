"""
AWS Lambda handler for the weather forecast API.

This module provides the main Lambda function handler for the weather forecast
application, including API endpoints for weather data and health checks.
"""

import json
import logging
import os
import traceback
from datetime import datetime, timezone
from typing import Dict, Any, Optional

# Use the simple weather service to avoid dependency issues
from simple_weather_service import get_weather_summary, WeatherServiceError

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def create_response(
    status_code: int,
    body: Any,
    headers: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Create a standardized Lambda response.

    Args:
        status_code: HTTP status code
        body: Response body (will be JSON serialized)
        headers: Optional HTTP headers

    Returns:
        Lambda response dictionary
    """
    default_headers = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
        "Access-Control-Allow-Methods": "GET,OPTIONS"
    }

    if headers:
        default_headers.update(headers)

    # Ensure body is JSON serializable
    if isinstance(body, (dict, list)):
        response_body = json.dumps(body, default=str)
    else:
        response_body = str(body)

    return {
        "statusCode": status_code,
        "headers": default_headers,
        "body": response_body
    }


def create_error_response(
    status_code: int,
    error_message: str,
    error_type: str = "Error",
    request_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a standardized error response.

    Args:
        status_code: HTTP status code
        error_message: Error message
        error_type: Type of error
        request_id: Optional request ID for tracking

    Returns:
        Lambda error response dictionary
    """
    error_body = {
        "error": {
            "type": error_type,
            "message": error_message,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    }

    if request_id:
        error_body["error"]["requestId"] = request_id

    return create_response(status_code, error_body)


def handle_weather_request(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle weather data request.

    Args:
        event: Lambda event
        context: Lambda context

    Returns:
        Lambda response with weather data
    """
    try:
        logger.info("Processing weather data request")

        # Get weather summary using simple service
        weather_summary = get_weather_summary()

        # Add metadata
        weather_summary.update({
            "requestId": context.aws_request_id,
            "version": "1.0.0",
            "service": "weather-forecast-app"
        })

        logger.info(f"Successfully processed weather data for {len(weather_summary.get('cities', []))} cities")

        return create_response(200, weather_summary)

    except WeatherServiceError as e:
        logger.error(f"Weather service error: {str(e)}")
        return create_error_response(
            502,
            "Weather service temporarily unavailable",
            "WeatherServiceError",
            context.aws_request_id
        )

    except Exception as e:
        logger.error(f"Unexpected error in weather request: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return create_error_response(
            500,
            "Internal server error",
            "InternalError",
            context.aws_request_id
        )


def handle_health_request(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle health check request.

    Args:
        event: Lambda event
        context: Lambda context

    Returns:
        Lambda response with health status
    """
    try:
        # Basic health check information
        health_data = {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": "1.0.0",
            "service": "weather-forecast-app",
            "requestId": context.aws_request_id,
            "environment": {
                "company_website": os.getenv("COMPANY_WEBSITE", "example.com"),
                "aws_region": os.getenv("AWS_REGION", "unknown"),
                "function_name": context.function_name,
                "function_version": context.function_version,
                "memory_limit": context.memory_limit_in_mb
            }
        }

        logger.info("Health check successful")
        return create_response(200, health_data)

    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return create_error_response(
            500,
            "Health check failed",
            "HealthCheckError",
            context.aws_request_id
        )


def handle_options_request(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle CORS preflight OPTIONS request.

    Args:
        event: Lambda event
        context: Lambda context

    Returns:
        Lambda response for CORS preflight
    """
    return create_response(200, "", {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
        "Access-Control-Allow-Methods": "GET,OPTIONS",
        "Access-Control-Max-Age": "86400"
    })


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler function.

    Routes requests to appropriate handlers based on HTTP method and path.

    Args:
        event: Lambda event containing request information
        context: Lambda context with runtime information

    Returns:
        HTTP response dictionary
    """
    try:
        # Log request information
        logger.info(f"Received request: {json.dumps(event, default=str)}")

        # Extract HTTP method and path
        http_method = event.get("httpMethod", "GET")
        path = event.get("path", "/")

        # Handle CORS preflight requests
        if http_method == "OPTIONS":
            return handle_options_request(event, context)

        # Route requests based on path
        if path == "/health":
            return handle_health_request(event, context)
        elif path == "/" or path == "/weather":
            if http_method == "GET":
                # Handle weather request
                return handle_weather_request(event, context)
            else:
                return create_error_response(
                    405,
                    f"Method {http_method} not allowed",
                    "MethodNotAllowed",
                    context.aws_request_id
                )
        else:
            return create_error_response(
                404,
                f"Path {path} not found",
                "NotFound",
                context.aws_request_id
            )

    except Exception as e:
        logger.error(f"Unexpected error in lambda_handler: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")

        # Fallback error response
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "error": {
                    "type": "CriticalError",
                    "message": "Critical system error",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            })
        }