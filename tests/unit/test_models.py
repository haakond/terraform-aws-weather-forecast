"""
Unit tests for weather service data models.
"""

import pytest
from datetime import date, timedelta
from src.weather_service.models import (
    Coordinates, Temperature, WeatherForecast, CityWeatherData, CityConfig,
    WeatherCondition
)


class TestCoordinates:
    def test_valid_coordinates(self):
        coords = Coordinates(latitude=59.9139, longitude=10.7522)
        assert coords.latitude == 59.9139
        assert coords.longitude == 10.7522

    def test_invalid_latitude(self):
        with pytest.raises(ValueError):
            Coordinates(latitude=91.0, longitude=10.0)


class TestTemperature:
    def test_valid_temperature(self):
        temp = Temperature(value=20.5, unit="celsius")
        assert temp.value == 20.5
        assert temp.unit == "celsius"

    def test_default_unit(self):
        temp = Temperature(value=20.0)
        assert temp.unit == "celsius"


class TestWeatherForecast:
    def test_valid_forecast(self):
        temp = Temperature(value=15.0)
        forecast = WeatherForecast(
            date=date.today() + timedelta(days=1),
            temperature=temp,
            condition=WeatherCondition.PARTLY_CLOUDY,
            description="Partly cloudy",
            icon="partly_cloudy_day"
        )
        assert forecast.temperature.value == 15.0
        assert forecast.condition == WeatherCondition.PARTLY_CLOUDY


class TestCityConfig:
    def test_valid_city_config(self):
        coords = Coordinates(latitude=59.9139, longitude=10.7522)
        config = CityConfig(
            id="oslo",
            name="Oslo",
            country="Norway",
            coordinates=coords
        )
        assert config.id == "oslo"
        assert config.name == "Oslo"