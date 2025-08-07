"""
Unit tests for weather service city configuration.
"""

import json
import os
import pytest
from unittest.mock import patch
from src.weather_service.config import (
    get_cities_config, get_city_config, validate_city_id, _load_cities_from_env, DEFAULT_CITIES_CONFIG
)


class TestCityConfiguration:
    def test_get_cities_config_default(self):
        """Test default cities configuration when no environment variable is set."""
        cities = get_cities_config()
        assert len(cities) == 4

        city_ids = [city.id for city in cities]
        expected_ids = ["oslo", "paris", "london", "barcelona"]
        assert set(city_ids) == set(expected_ids)

    def test_get_city_config_oslo(self):
        """Test getting specific city configuration."""
        oslo = get_city_config("oslo")
        assert oslo.id == "oslo"
        assert oslo.name == "Oslo"
        assert oslo.country == "Norway"
        assert oslo.coordinates.latitude == 59.9139
        assert oslo.coordinates.longitude == 10.7522

    def test_get_city_config_invalid_id(self):
        """Test error handling for invalid city ID."""
        with pytest.raises(ValueError, match="City with ID 'invalid' not found"):
            get_city_config("invalid")

    def test_validate_city_id(self):
        """Test city ID validation."""
        assert validate_city_id("oslo") is True
        assert validate_city_id("invalid") is False

    @patch.dict(os.environ, {}, clear=True)
    def test_load_cities_from_env_no_config(self):
        """Test loading cities when no environment variable is set."""
        cities = _load_cities_from_env()
        assert len(cities) == 4
        assert cities[0].id == "oslo"

    @patch.dict(os.environ, {"CITIES_CONFIG": json.dumps([
        {
            "id": "tokyo",
            "name": "Tokyo",
            "country": "Japan",
            "coordinates": {"latitude": 35.6762, "longitude": 139.6503}
        },
        {
            "id": "sydney",
            "name": "Sydney",
            "country": "Australia",
            "coordinates": {"latitude": -33.8688, "longitude": 151.2093}
        }
    ])})
    def test_load_cities_from_env_custom_config(self):
        """Test loading custom cities from environment variable."""
        cities = _load_cities_from_env()
        assert len(cities) == 2

        tokyo = cities[0]
        assert tokyo.id == "tokyo"
        assert tokyo.name == "Tokyo"
        assert tokyo.country == "Japan"
        assert tokyo.coordinates.latitude == 35.6762
        assert tokyo.coordinates.longitude == 139.6503

        sydney = cities[1]
        assert sydney.id == "sydney"
        assert sydney.name == "Sydney"
        assert sydney.country == "Australia"

    @patch.dict(os.environ, {"CITIES_CONFIG": "invalid json"})
    def test_load_cities_from_env_invalid_json(self):
        """Test fallback to defaults when environment variable contains invalid JSON."""
        with patch('builtins.print') as mock_print:
            cities = _load_cities_from_env()
            assert len(cities) == 4  # Should fall back to defaults
            assert cities[0].id == "oslo"
            mock_print.assert_called()

    @patch.dict(os.environ, {"CITIES_CONFIG": json.dumps([
        {
            "id": "tokyo",
            "name": "Tokyo",
            "country": "Japan"
            # Missing coordinates
        }
    ])})
    def test_load_cities_from_env_missing_fields(self):
        """Test fallback to defaults when environment variable has missing fields."""
        with patch('builtins.print') as mock_print:
            cities = _load_cities_from_env()
            assert len(cities) == 4  # Should fall back to defaults
            assert cities[0].id == "oslo"
            mock_print.assert_called()

    @patch.dict(os.environ, {"CITIES_CONFIG": json.dumps([
        {
            "id": "invalid",
            "name": "Invalid",
            "country": "Test",
            "coordinates": {"latitude": 200, "longitude": 300}  # Invalid coordinates
        }
    ])})
    def test_load_cities_from_env_invalid_coordinates(self):
        """Test fallback to defaults when environment variable has invalid coordinates."""
        with patch('builtins.print') as mock_print:
            cities = _load_cities_from_env()
            assert len(cities) == 4  # Should fall back to defaults
            assert cities[0].id == "oslo"
            mock_print.assert_called()

    def test_default_cities_config_structure(self):
        """Test that default cities configuration has correct structure."""
        assert len(DEFAULT_CITIES_CONFIG) == 4

        for city in DEFAULT_CITIES_CONFIG:
            assert hasattr(city, 'id')
            assert hasattr(city, 'name')
            assert hasattr(city, 'country')
            assert hasattr(city, 'coordinates')
            assert hasattr(city.coordinates, 'latitude')
            assert hasattr(city.coordinates, 'longitude')

            # Validate coordinate ranges
            assert -90 <= city.coordinates.latitude <= 90
            assert -180 <= city.coordinates.longitude <= 180