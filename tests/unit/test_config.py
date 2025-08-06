"""
Unit tests for weather service city configuration.
"""

import pytest
from src.weather_service.config import (
    get_cities_config, get_city_config, validate_city_id
)


class TestCityConfiguration:
    def test_get_cities_config(self):
        cities = get_cities_config()
        assert len(cities) == 4

        city_ids = [city.id for city in cities]
        expected_ids = ["oslo", "paris", "london", "barcelona"]
        assert set(city_ids) == set(expected_ids)

    def test_get_city_config_oslo(self):
        oslo = get_city_config("oslo")
        assert oslo.id == "oslo"
        assert oslo.name == "Oslo"
        assert oslo.country == "Norway"

    def test_get_city_config_invalid_id(self):
        with pytest.raises(ValueError):
            get_city_config("invalid")

    def test_validate_city_id(self):
        assert validate_city_id("oslo") is True
        assert validate_city_id("invalid") is False