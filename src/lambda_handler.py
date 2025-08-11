"""
AWS Lambda handler for the weather forecast API.

This module provides the main Lambda function handler for the weather forecast
application, including API endpoints for weather data and health checks.
"""

import json
import logging
import os
import traceback
import time
import urllib.request
import urllib.parse
import boto3
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

# Weather service functionality embedded to avoid import issues

# Initialize DynamoDB client
dynamodb = boto3.client('dynamodb')

# Configuration
BASE_URL = "https://api.met.no/weatherapi/locationforecast/2.0/compact"
DEFAULT_CITIES = [
    {
        "id": "oslo",
        "name": "Oslo",
        "country": "Norway",
        "coordinates": {"latitude": 59.9139, "longitude": 10.7522}
    },
    {
        "id": "paris",
        "name": "Paris",
        "country": "France",
        "coordinates": {"latitude": 48.8566, "longitude": 2.3522}
    },
    {
        "id": "london",
        "name": "London",
        "country": "United Kingdom",
        "coordinates": {"latitude": 51.5074, "longitude": -0.1278}
    },
    {
        "id": "barcelona",
        "name": "Barcelona",
        "country": "Spain",
        "coordinates": {"latitude": 41.3851, "longitude": 2.1734}
    }
]


class WeatherServiceError(Exception):
    """Base exception for weather service errors."""
    pass


def get_cities_config() -> List[Dict[str, Any]]:
    """Get cities configuration from environment or use defaults."""
    cities_config = os.getenv("CITIES_CONFIG")
    if cities_config:
        try:
            return json.loads(cities_config)
        except json.JSONDecodeError:
            logger.warning("Invalid CITIES_CONFIG, using defaults")
    return DEFAULT_CITIES


def fetch_weather_data(latitude: float, longitude: float) -> Dict[str, Any]:
    """Fetch weather data from met.no API."""
    company_website = os.getenv("COMPANY_WEBSITE", "example.com")
    user_agent = f"weather-forecast-app/1.0 (+https://{company_website})"

    # Build URL
    params = urllib.parse.urlencode({
        "lat": latitude,
        "lon": longitude
    })
    url = f"{BASE_URL}?{params}"

    # Create request
    req = urllib.request.Request(url)
    req.add_header("User-Agent", user_agent)
    req.add_header("Accept", "application/json")

    try:
        logger.info(f"Fetching weather data for lat={latitude}, lon={longitude}")
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode())
            logger.info("Successfully fetched weather data")
            return data
    except Exception as e:
        logger.error(f"Failed to fetch weather data: {e}")
        raise WeatherServiceError(f"Failed to fetch weather data: {e}")


def extract_tomorrow_forecast(weather_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract tomorrow's forecast from met.no response."""
    try:
        properties = weather_data.get("properties", {})
        timeseries = properties.get("timeseries", [])

        if not timeseries:
            raise WeatherServiceError("No timeseries data found")

        # Find tomorrow's data (approximately 24 hours from now)
        now = datetime.now(timezone.utc)
        tomorrow = now.replace(hour=12, minute=0, second=0, microsecond=0)
        tomorrow = tomorrow.replace(day=tomorrow.day + 1)

        # Find the closest forecast to tomorrow noon
        best_forecast = None
        min_time_diff = float('inf')

        for entry in timeseries:
            forecast_time = datetime.fromisoformat(entry["time"].replace("Z", "+00:00"))
            time_diff = abs((forecast_time - tomorrow).total_seconds())

            if time_diff < min_time_diff:
                min_time_diff = time_diff
                best_forecast = entry

        if not best_forecast:
            raise WeatherServiceError("No suitable forecast found")

        # Extract forecast data
        instant_data = best_forecast.get("data", {}).get("instant", {}).get("details", {})
        next_6h_data = best_forecast.get("data", {}).get("next_6_hours", {})

        temperature = instant_data.get("air_temperature", 0)
        symbol_code = next_6h_data.get("summary", {}).get("symbol_code", "unknown")

        # Map symbol code to condition
        condition_map = {
            "clearsky": "clear",
            "fair": "partly_cloudy",
            "partlycloudy": "partly_cloudy",
            "cloudy": "cloudy",
            "rain": "rain",
            "snow": "snow",
            "fog": "fog"
        }

        condition = "unknown"
        for key, value in condition_map.items():
            if key in symbol_code:
                condition = value
                break

        return {
            "temperature": {
                "value": round(temperature),
                "unit": "celsius"
            },
            "condition": condition,
            "description": symbol_code.replace("_", " ").title()
        }

    except Exception as e:
        logger.error(f"Failed to extract forecast: {e}")
        raise WeatherServiceError(f"Failed to extract forecast: {e}")



def get_cached_weather_data(city_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve cached weather data from DynamoDB.

    Args:
        city_id: The city identifier

    Returns:
        Cached weather data if found and not expired, None otherwise
    """
    table_name = os.getenv("DYNAMODB_TABLE_NAME")
    if not table_name:
        logger.warning("DYNAMODB_TABLE_NAME not set, skipping cache check")
        return None

    try:
        response = dynamodb.get_item(
            TableName=table_name,
            Key={
                'city_id': {'S': city_id}
            }
        )

        if 'Item' not in response:
            logger.info(f"No cached data found for city {city_id}")
            return None

        item = response['Item']

        # Check if the item has expired (TTL is handled automatically by DynamoDB,
        # but we can also check manually for logging purposes)
        ttl = int(item.get('ttl', {}).get('N', '0'))
        current_time = int(time.time())

        if ttl <= current_time:
            logger.info(f"Cached data for city {city_id} has expired")
            return None

        # Convert DynamoDB item to Python dict
        cached_data = {
            "cityId": item['city_id']['S'],
            "cityName": item['city_name']['S'],
            "country": item['country']['S'],
            "forecast": json.loads(item['forecast']['S']),
            "lastUpdated": item['last_updated']['S']
        }

        logger.info(f"Retrieved cached data for city {city_id}")
        return cached_data

    except Exception as e:
        logger.error(f"Error retrieving cached data for city {city_id}: {e}")
        return None


def cache_weather_data(city_data: Dict[str, Any]) -> bool:
    """
    Cache weather data in DynamoDB with 1-hour TTL.

    Args:
        city_data: Weather data to cache

    Returns:
        True if caching was successful, False otherwise
    """
    table_name = os.getenv("DYNAMODB_TABLE_NAME")
    if not table_name:
        logger.warning("DYNAMODB_TABLE_NAME not set, skipping cache storage")
        return False

    try:
        # Calculate TTL (1 hour = 3600 seconds from now)
        ttl = int(time.time()) + 3600

        # Prepare item for DynamoDB
        item = {
            'city_id': {'S': city_data['cityId']},
            'city_name': {'S': city_data['cityName']},
            'country': {'S': city_data['country']},
            'forecast': {'S': json.dumps(city_data['forecast'])},
            'last_updated': {'S': datetime.now(timezone.utc).isoformat()},
            'ttl': {'N': str(ttl)}
        }

        dynamodb.put_item(
            TableName=table_name,
            Item=item
        )

        logger.info(f"Cached weather data for city {city_data['cityId']}")
        return True

    except Exception as e:
        logger.error(f"Error caching weather data for city {city_data['cityId']}: {e}")
        return False


def process_city_weather_with_cache(city_config: Dict[str, Any]) -> Dict[str, Any]:
    """Process weather data for a single city with caching support."""
    city_id = city_config["id"]

    # Try to get cached data first
    cached_data = get_cached_weather_data(city_id)
    if cached_data:
        logger.info(f"Using cached data for city {city_id}")
        return cached_data

    # If no cached data, fetch from API
    logger.info(f"No cached data for city {city_id}, fetching from API")
    try:
        coords = city_config["coordinates"]
        weather_data = fetch_weather_data(coords["latitude"], coords["longitude"])
        forecast = extract_tomorrow_forecast(weather_data)

        city_weather = {
            "cityId": city_config["id"],
            "cityName": city_config["name"],
            "country": city_config["country"],
            "forecast": forecast
        }

        # Cache the successful result
        cache_weather_data(city_weather)

        return city_weather

    except Exception as e:
        logger.error(f"Failed to process weather for {city_config['name']}: {e}")
        # Return a fallback response
        return {
            "cityId": city_config["id"],
            "cityName": city_config["name"],
            "country": city_config["country"],
            "forecast": {
                "temperature": {"value": 0, "unit": "celsius"},
                "condition": "unknown",
                "description": "Data unavailable"
            },
            "error": str(e)
        }


def get_weather_summary() -> Dict[str, Any]:
    """Get weather summary for all configured cities with caching support."""
    cities_config = get_cities_config()
    cities_weather = []

    for city_config in cities_config:
        city_weather = process_city_weather_with_cache(city_config)
        cities_weather.append(city_weather)

        # Add small delay to be respectful to the API (only if we made an API call)
        if 'error' not in city_weather:
            time.sleep(0.5)

    return {
        "cities": cities_weather,
        "lastUpdated": datetime.now(timezone.utc).isoformat(),
        "status": "success"
    }


# Configure logging

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