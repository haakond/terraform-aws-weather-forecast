"""
Local end-to-end testing script for the weather forecast application.
This script can be used for local testing and development.
The actual CloudWatch Synthetics canary is deployed via Terraform using JavaScript.
"""

import json
import time
import requests
import argparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options


def main(url, api_url=None, headless=True):
    """Main function for local end-to-end testing."""

    print(f"Starting end-to-end tests for: {url}")

    # Configure Chrome options
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    # Initialize webdriver
    driver = webdriver.Chrome(options=chrome_options)
    driver.set_page_load_timeout(30)

    try:
        # Test 1: Page Load and Basic Structure
        test_page_load(driver, url, 30)

        # Test 2: Weather Data Loading
        test_weather_data_loading(driver, 30)

        # Test 3: Responsive Design
        test_responsive_design(driver)

        # Test 4: API Endpoint Health (if API URL provided)
        if api_url:
            test_api_health_direct(api_url)

        # Test 5: Performance Check
        test_performance(driver, url)

        print("All end-to-end tests passed successfully!")
        return True

    except Exception as e:
        print(f"End-to-end test failed: {str(e)}")
        return False
    finally:
        driver.quit()


def test_page_load(driver, url, timeout):
    """Test that the main page loads correctly."""
    print(f"Testing page load for URL: {url}")

    # Navigate to the application
    driver.get(url)

    # Wait for page to load
    WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )

    # Verify page title
    assert "Weather Forecast" in driver.title, f"Unexpected page title: {driver.title}"

    # Verify main container is present
    main_container = WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.CLASS_NAME, "weather-container"))
    )
    assert main_container.is_displayed(), "Main weather container not visible"

    print("Page load test passed")


def test_weather_data_loading(driver, timeout):
    """Test that weather data loads for all cities."""
    print("Testing weather data loading")

    expected_cities = ["Oslo", "Paris", "London", "Barcelona"]

    # Wait for weather cards to load
    weather_cards = WebDriverWait(driver, timeout).until(
        EC.presence_of_all_elements_located((By.CLASS_NAME, "weather-card"))
    )

    # Verify we have 4 weather cards
    assert len(weather_cards) == 4, f"Expected 4 weather cards, found {len(weather_cards)}"

    # Verify each city is present and has weather data
    for card in weather_cards:
        # Check city name is present
        city_name = card.find_element(By.CLASS_NAME, "city-name")
        assert city_name.text in expected_cities, f"Unexpected city: {city_name.text}"

        # Check temperature is displayed
        temperature = card.find_element(By.CLASS_NAME, "temperature")
        assert temperature.text, "Temperature not displayed"
        assert "°C" in temperature.text, "Temperature not in Celsius"

        # Check weather icon is present
        weather_icon = card.find_element(By.CLASS_NAME, "weather-icon")
        assert weather_icon.is_displayed(), "Weather icon not visible"

        # Check weather description is present
        description = card.find_element(By.CLASS_NAME, "weather-description")
        assert description.text, "Weather description not displayed"

    print("Weather data loading test passed")


def test_responsive_design(driver):
    """Test responsive design at different screen sizes."""
    print("Testing responsive design")

    # Test desktop view (1920x1080)
    driver.set_window_size(1920, 1080)
    time.sleep(1)

    weather_container = driver.find_element(By.CLASS_NAME, "weather-container")
    assert weather_container.is_displayed(), "Weather container not visible on desktop"

    # Test tablet view (768x1024)
    driver.set_window_size(768, 1024)
    time.sleep(1)

    weather_cards = driver.find_elements(By.CLASS_NAME, "weather-card")
    assert len(weather_cards) == 4, "Not all weather cards visible on tablet"

    # Test mobile view (375x667)
    driver.set_window_size(375, 667)
    time.sleep(1)

    weather_cards = driver.find_elements(By.CLASS_NAME, "weather-card")
    assert len(weather_cards) == 4, "Not all weather cards visible on mobile"

    # Reset to desktop view
    driver.set_window_size(1920, 1080)

    print("Responsive design test passed")


def test_api_health_direct(api_url):
    """Test API health endpoint directly."""
    print("Testing API health endpoint")

    health_url = f"{api_url}/health"

    try:
        response = requests.get(health_url, timeout=10)
        response.raise_for_status()

        response_data = response.json()
        assert response_data.get('status') == 'healthy', "API health check failed"
        assert 'timestamp' in response_data, "Health response missing timestamp"
        assert 'version' in response_data, "Health response missing version"

        print("API health test passed")

    except requests.exceptions.RequestException as e:
        raise AssertionError(f"API health check failed: {e}")
    except json.JSONDecodeError as e:
        raise AssertionError(f"Invalid JSON response from health endpoint: {e}")


def test_performance(driver, url):
    """Test basic performance metrics."""
    print("Testing performance metrics")

    # Navigate to page and measure load time
    start_time = time.time()
    driver.get(url)

    # Wait for page to be fully loaded
    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.CLASS_NAME, "weather-container"))
    )

    load_time = time.time() - start_time

    # Basic performance assertions
    assert load_time < 10, f"Page load time too slow: {load_time:.2f}s"

    print(f"Performance test passed - Load time: {load_time:.2f}s")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run end-to-end tests for Weather Forecast App')
    parser.add_argument('url', help='URL of the weather forecast application')
    parser.add_argument('--api-url', help='API Gateway URL for health checks')
    parser.add_argument('--headless', action='store_true', default=True,
                       help='Run browser in headless mode (default: True)')
    parser.add_argument('--no-headless', action='store_false', dest='headless',
                       help='Run browser with GUI')

    args = parser.parse_args()

    success = main(args.url, args.api_url, args.headless)
    exit(0 if success else 1)


