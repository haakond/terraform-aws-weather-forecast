"""
Unit tests for weather service data transformation utilities.
"""

import pytest
from datetime import date, timedelta
from unittest.mock import patch
from src.weather_service.transformers import (
    map_weather_symbol, extract_tomorrow_forecast, create_cache_key
)
from src.weather_service.models import WeatherCondition


class TestWeatherSymbolMapping:
    def test_clear_sky_mapping(self):
        assert map_weather_symbol("clearsky_day") == WeatherCondition.CLEAR_SKY

    def test_rain_mapping(self):
        assert map_weather_symbol("rain") == WeatherCondition.RAIN
        assert map_weather_symbol("lightrain") == WeatherCondition.LIGHT_RAIN

    def test_unknown_symbol_mapping(self):
        assert map_weather_symbol("unknown_symbol") == WeatherCondition.UNKNOWN

    def test_symbol_with_number_suffix(self):
        assert map_weather_symbol("rain_2") == WeatherCondition.RAIN


class TestExtractTomorrowForecast:
    def create_mock_api_response(self):
        tomorrow = date.today() + timedelta(days=1)
        return {
            "properties": {
                "timeseries": [
                    {
                        "time": f"{tomorrow}T12:00:00Z",
                        "data": {
                            "instant": {
                                "details": {
                                    "air_temperature": 15.5,
                                    "relative_humidity": 65.0,
                                    "wind_speed": 8.2
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

    def test_extract_tomorrow_forecast_success(self):
        api_response = self.create_mock_api_response()
        forecast = extract_tomorrow_forecast(api_response)

        assert forecast is not None
        assert forecast["air_temperature"] == 15.5
        assert forecast["symbol_code"] == "partlycloudy_day"

    def test_extract_tomorrow_forecast_empty_timeseries(self):
        api_response = {"properties": {"timeseries": []}}
        forecast = extract_tomorrow_forecast(api_response)
        assert forecast is None


class TestUtilityFunctions:
    def test_create_cache_key(self):
        test_date = date(2024, 1, 15)
        cache_key = create_cache_key("oslo", test_date)
        assert cache_key == "weather:oslo:2024-01-15"