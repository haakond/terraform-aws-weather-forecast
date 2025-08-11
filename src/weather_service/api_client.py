"""
Weather API client for fetching data from the Norwegian Meteorological Institute.

This module provides a client for interacting with the met.no weather API,
including rate limiting, error handling, and retry logic.
"""

import os
import time
import logging
from typing import Dict, Optional, Any
from urllib.parse import urlencode
import requests
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Configuration constants
BASE_URL = "https://api.met.no/weatherapi/locationforecast/2.0/compact"
MAX_RETRIES = 3
RETRY_DELAY = 1.0  # seconds
RATE_LIMIT_DELAY = 1.0  # seconds between requests


class WeatherAPIError(Exception):
    """Base exception for weather API errors."""

    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


class RateLimitError(WeatherAPIError):
    """Exception raised when rate limit is exceeded."""
    pass


class APIConnectionError(WeatherAPIError):
    """Exception raised when connection to API fails."""
    pass


class MalformedResponseError(WeatherAPIError):
    """Exception raised when API response is malformed."""
    pass


@dataclass
class RateLimiter:
    """Simple rate limiter to respect API limits."""

    last_request_time: float = 0.0
    min_interval: float = RATE_LIMIT_DELAY

    def wait_if_needed(self) -> None:
        """Wait if necessary to respect rate limits."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.min_interval:
            sleep_time = self.min_interval - time_since_last
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)

        self.last_request_time = time.time()


class WeatherAPIClient:
    """
    Client for fetching weather data from the Norwegian Meteorological Institute API.

    This client handles:
    - Rate limiting to respect API terms
    - Retry logic for transient failures
    - Proper error handling and logging
    - User-Agent identification as required by met.no
    """

    def __init__(self, company_website: Optional[str] = None, timeout: int = 30, max_retries: int = MAX_RETRIES):
        """
        Initialize the weather API client.

        Args:
            company_website: Website domain for User-Agent identification
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.company_website = company_website or os.getenv("COMPANY_WEBSITE", "example.com")
        self.timeout = timeout
        self.max_retries = max_retries
        self.rate_limiter = RateLimiter()

        # User-Agent as per met.no terms of service
        self.user_agent = f"weather-forecast-app/1.0 (+https://{self.company_website})"

        # Configure session
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": self.user_agent,
            "Accept": "application/json",
            "Accept-Encoding": "gzip, deflate"
        })

    def _should_retry(self, exception: Exception) -> bool:
        """
        Determine if a request should be retried based on the exception.

        Args:
            exception: The exception that occurred

        Returns:
            True if the request should be retried, False otherwise
        """
        # Retry on connection errors and timeouts
        if isinstance(exception, (requests.ConnectionError, requests.Timeout)):
            return True

        # Retry on specific HTTP status codes
        if isinstance(exception, requests.HTTPError):
            if hasattr(exception, 'response') and exception.response is not None:
                status_code = exception.response.status_code
                # Retry on server errors (5xx) and rate limiting (429)
                return status_code >= 500 or status_code == 429

        return False

    def get_weather_data(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """
        Fetch weather data for the specified coordinates.

        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate

        Returns:
            Weather data as a dictionary

        Raises:
            WeatherAPIError: If the API request fails
            RateLimitError: If rate limit is exceeded
            APIConnectionError: If connection fails
            MalformedResponseError: If response is malformed
        """
        # Validate coordinates
        if not (-90 <= latitude <= 90):
            raise WeatherAPIError(f"Invalid latitude: {latitude}. Must be between -90 and 90.")
        if not (-180 <= longitude <= 180):
            raise WeatherAPIError(f"Invalid longitude: {longitude}. Must be between -180 and 180.")

        # Build URL with parameters
        params = {
            "lat": latitude,
            "lon": longitude
        }
        url = f"{BASE_URL}?{urlencode(params)}"

        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                # Apply rate limiting
                self.rate_limiter.wait_if_needed()

                logger.info(f"Fetching weather data for lat={latitude}, lon={longitude} (attempt {attempt + 1})")

                # Make the request
                response = self.session.get(url, timeout=self.timeout)

                # Check for rate limiting
                if response.status_code == 429:
                    logger.warning("Rate limit exceeded, waiting before retry")
                    time.sleep(RETRY_DELAY * (2 ** attempt))  # Exponential backoff
                    raise RateLimitError("Rate limit exceeded")

                # Raise for HTTP errors
                response.raise_for_status()

                # Parse JSON response
                try:
                    data = response.json()
                    logger.info(f"Successfully fetched weather data for lat={latitude}, lon={longitude}")
                    return data

                except ValueError as e:
                    logger.error(f"Failed to parse JSON response: {e}")
                    raise MalformedResponseError(f"Invalid JSON response: {e}") from e

            except Exception as e:
                last_exception = e
                logger.warning(f"Request attempt {attempt + 1} failed: {e}")

                # Don't retry if this is the last attempt
                if attempt == self.max_retries:
                    break

                # Don't retry if it's not a retryable error
                if not self._should_retry(e):
                    break

                # Wait before retrying with exponential backoff
                sleep_time = RETRY_DELAY * (2 ** attempt)
                logger.info(f"Retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)

        # All retries exhausted, raise the last exception
        if isinstance(last_exception, requests.ConnectionError):
            raise APIConnectionError(f"Failed to connect to weather API: {last_exception}") from last_exception
        elif isinstance(last_exception, requests.Timeout):
            raise APIConnectionError(f"Request timeout: {last_exception}") from last_exception
        elif isinstance(last_exception, requests.HTTPError):
            status_code = getattr(last_exception.response, 'status_code', None) if hasattr(last_exception, 'response') else None
            raise WeatherAPIError(f"HTTP error: {last_exception}", status_code) from last_exception
        else:
            raise WeatherAPIError(f"Unexpected error: {last_exception}") from last_exception

    def close(self) -> None:
        """Close the HTTP session."""
        if self.session:
            self.session.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


def create_weather_client(company_website: Optional[str] = None, timeout: int = 30, max_retries: int = MAX_RETRIES) -> WeatherAPIClient:
    """
    Factory function to create a weather API client.

    Args:
        company_website: Website domain for User-Agent identification
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
