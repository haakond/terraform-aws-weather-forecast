"""
Weather API client for the Norwegian Meteorological Institute API.

This module provides an HTTP client for fetching weather data from the met.no API
with proper User-Agent identification, rate limiting, retry logic, and error handling.
"""

import asyncio
import logging
import os
import time
from typing import Dict, Optional, Any
from urllib.parse import urlencode
import aiohttp
import backoff
from dataclasses import dataclass


logger = logging.getLogger(__name__)


class WeatherAPIError(Exception):
    """Base exception for weather API errors."""
    pass


class RateLimitError(WeatherAPIError):
    """Exception raised when API rate limit is exceeded."""
    pass


class APIConnectionError(WeatherAPIError):
    """Exception raised when API connection fails."""
    pass


class MalformedResponseError(WeatherAPIError):
    """Exception raised when API response is malformed."""
    pass


@dataclass
class RateLimiter:
    """Simple rate limiter for API requests."""
    max_requests: int = 20  # met.no allows max 20 requests per second
    time_window: float = 1.0  # 1 second window

    def __post_init__(self):
        self._requests = []
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Acquire permission to make a request, blocking if necessary."""
        async with self._lock:
            now = time.time()

            # Remove requests older than the time window
            self._requests = [req_time for req_time in self._requests
                            if now - req_time < self.time_window]

            # If we're at the limit, wait until we can make another request
            if len(self._requests) >= self.max_requests:
                oldest_request = min(self._requests)
                wait_time = self.time_window - (now - oldest_request)
                if wait_time > 0:
                    logger.debug(f"Rate limit reached, waiting {wait_time:.2f} seconds")
                    await asyncio.sleep(wait_time)
                    # Recursively try again after waiting
                    await self.acquire()
                    return

            # Record this request
            self._requests.append(now)


class WeatherAPIClient:
    """
    HTTP client for the Norwegian Meteorological Institute weather API.

    Provides weather data retrieval with proper User-Agent identification,
    rate limiting, retry logic, and comprehensive error handling.
    """

    BASE_URL = "https://api.met.no/weatherapi/locationforecast/2.0/"
    DEFAULT_TIMEOUT = 30.0
    MAX_RETRIES = 3

    def __init__(
        self,
        company_website: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = MAX_RETRIES
    ):
        """
        Initialize the weather API client.

        Args:
            company_website: Company website for User-Agent header (default: example.com)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.company_website = company_website or os.getenv("COMPANY_WEBSITE", "example.com")
        self.timeout = timeout
        self.max_retries = max_retries
        self.rate_limiter = RateLimiter()

        # User-Agent as per met.no terms of service
        self.user_agent = f"weather-forecast-app/1.0 (+https://{self.company_website})"

        # Session will be created when needed
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session with proper configuration."""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            headers = {
                "User-Agent": self.user_agent,
                "Accept": "application/json",
                "Accept-Encoding": "gzip, deflate"
            }

            self._session = aiohttp.ClientSession(
                timeout=timeout,
                headers=headers,
                connector=aiohttp.TCPConnector(limit=10, limit_per_host=5)
            )

        return self._session

    async def close(self) -> None:
        """Close the HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    def _should_retry(self, exception: Exception) -> bool:
        """
        Determine if a request should be retried based on the exception.

        Args:
            exception: The exception that occurred

        Returns:
            True if the request should be retried, False otherwise
        """
        # Retry on connection errors and server errors (5xx)
        if isinstance(exception, (aiohttp.ClientConnectionError,
                                aiohttp.ServerTimeoutError,
                                asyncio.TimeoutError)):
            return True

        # Retry on specific HTTP status codes
        if isinstance(exception, aiohttp.ClientResponseError):
            # Retry on server errors (5xx) and rate limiting (429)
            return exception.status >= 500 or exception.status == 429

        return False

    @backoff.on_exception(
        backoff.expo,
        (aiohttp.ClientError, asyncio.TimeoutError, RateLimitError),
        max_tries=MAX_RETRIES,
        max_time=300,  # Maximum total time for retries: 5 minutes
        jitter=backoff.random_jitter
    )
    async def _make_request(self, url: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make an HTTP request with retry logic and error handling.

        Args:
            url: The URL to request
            params: Query parameters

        Returns:
            Parsed JSON response

        Raises:
            WeatherAPIError: For various API-related errors
        """
        # Apply rate limiting
        await self.rate_limiter.acquire()

        session = await self._get_session()

        try:
            logger.debug(f"Making request to {url} with params: {params}")

            async with session.get(url, params=params) as response:
                # Check for rate limiting
                if response.status == 429:
                    retry_after = response.headers.get('Retry-After')
                    wait_time = int(retry_after) if retry_after else 60
                    logger.warning(f"Rate limited, waiting {wait_time} seconds")
                    await asyncio.sleep(wait_time)
                    raise RateLimitError(f"Rate limited, retry after {wait_time} seconds")

                # Check for client errors (4xx)
                if 400 <= response.status < 500:
                    error_text = await response.text()
                    raise WeatherAPIError(
                        f"Client error {response.status}: {error_text}"
                    )

                # Check for server errors (5xx)
                if response.status >= 500:
                    error_text = await response.text()
                    raise APIConnectionError(
                        f"Server error {response.status}: {error_text}"
                    )

                # Ensure we got a successful response
                response.raise_for_status()

                # Parse JSON response
                try:
                    data = await response.json()
                    logger.debug(f"Received response with {len(str(data))} characters")
                    return data

                except (aiohttp.ContentTypeError, ValueError) as e:
                    response_text = await response.text()
                    logger.error(f"Failed to parse JSON response: {e}")
                    logger.error(f"Response content: {response_text[:500]}...")
                    raise MalformedResponseError(
                        f"Invalid JSON response: {e}"
                    ) from e

        except aiohttp.ClientError as e:
            logger.error(f"HTTP client error: {e}")
            if self._should_retry(e):
                raise  # Let backoff handle the retry
            else:
                raise APIConnectionError(f"HTTP client error: {e}") from e

        except asyncio.TimeoutError as e:
            logger.error(f"Request timeout: {e}")
            raise APIConnectionError(f"Request timeout: {e}") from e

    async def get_weather_forecast(
        self,
        latitude: float,
        longitude: float,
        altitude: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get weather forecast for specific coordinates.

        Args:
            latitude: Latitude coordinate (-90 to 90)
            longitude: Longitude coordinate (-180 to 180)
            altitude: Altitude in meters (optional)

        Returns:
            Weather forecast data from met.no API

        Raises:
            WeatherAPIError: For various API-related errors
            ValueError: For invalid coordinate values
        """
        # Validate coordinates
        if not -90 <= latitude <= 90:
            raise ValueError(f"Latitude must be between -90 and 90, got {latitude}")

        if not -180 <= longitude <= 180:
            raise ValueError(f"Longitude must be between -180 and 180, got {longitude}")

        # Build request parameters
        params = {
            "lat": latitude,
            "lon": longitude
        }

        if altitude is not None:
            if altitude < -500 or altitude > 9000:  # Reasonable altitude limits
                raise ValueError(f"Altitude must be between -500 and 9000 meters, got {altitude}")
            params["altitude"] = altitude

        url = f"{self.BASE_URL}compact"

        try:
            data = await self._make_request(url, params)

            # Basic validation of response structure
            if not isinstance(data, dict):
                raise MalformedResponseError("Response is not a JSON object")

            if "properties" not in data:
                raise MalformedResponseError("Response missing 'properties' field")

            if "timeseries" not in data["properties"]:
                raise MalformedResponseError("Response missing 'timeseries' field")

            return data

        except WeatherAPIError:
            # Re-raise weather API errors as-is
            raise

        except Exception as e:
            logger.error(f"Unexpected error in get_weather_forecast: {e}")
            raise WeatherAPIError(f"Unexpected error: {e}") from e

    async def get_weather_for_city(self, city_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get weather forecast for a city using its configuration.

        Args:
            city_config: City configuration dictionary with coordinates

        Returns:
            Weather forecast data from met.no API

        Raises:
            WeatherAPIError: For various API-related errors
            ValueError: For invalid city configuration
        """
        if not isinstance(city_config, dict):
            raise ValueError("City configuration must be a dictionary")

        if "coordinates" not in city_config:
            raise ValueError("City configuration missing 'coordinates' field")

        coords = city_config["coordinates"]

        # Support both lat/lon and latitude/longitude formats
        if "lat" in coords and "lon" in coords:
            latitude = coords["lat"]
            longitude = coords["lon"]
        elif "latitude" in coords and "longitude" in coords:
            latitude = coords["latitude"]
            longitude = coords["longitude"]
        else:
            raise ValueError("City coordinates must include lat/lon or latitude/longitude")

        return await self.get_weather_forecast(latitude, longitude)

    def get_user_agent(self) -> str:
        """Get the User-Agent string used for API requests."""
        return self.user_agent

    def get_company_website(self) -> str:
        """Get the company website used in the User-Agent."""
        return self.company_website


# Convenience function for creating a client instance
def create_weather_client(
    company_website: Optional[str] = None,
    timeout: float = WeatherAPIClient.DEFAULT_TIMEOUT,
    max_retries: int = WeatherAPIClient.MAX_RETRIES
) -> WeatherAPIClient:
    """
    Create a weather API client instance.

    Args:
        company_website: Company website for User-Agent header
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts

    Returns:
        Configured WeatherAPIClient instance
    """
    return WeatherAPIClient(
        company_website=company_website,
        timeout=timeout,
        max_retries=max_retries
    )