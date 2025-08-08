# Basic validation test for backend module variables
# This test validates variable constraints without requiring AWS resources

variables {
  project_name                          = "test-weather-app"
  service_name                          = "weather-forecast-app"
  environment                           = "test"
  weather_service_identification_domain = "example.com"
  log_retention_days                    = 180
  lambda_memory_size                    = 512
  lambda_timeout                        = 30

  cities_config = [
    {
      id      = "oslo"
      name    = "Oslo"
      country = "Norway"
      coordinates = {
        latitude  = 59.9139
        longitude = 10.7522
      }
    }
  ]

  common_tags = {
    Environment = "test"
    Service     = "weather-forecast-app"
  }
}

run "validate_backend_variables" {
  command = plan

  # Basic validation of variable values
  assert {
    condition     = var.project_name == "test-weather-app"
    error_message = "Project name should be set correctly"
  }

  assert {
    condition     = var.lambda_memory_size >= 128
    error_message = "Lambda memory size should be at least 128 MB"
  }

  assert {
    condition     = var.lambda_timeout <= 900
    error_message = "Lambda timeout should not exceed 15 minutes"
  }

  assert {
    condition     = length(var.cities_config) > 0
    error_message = "Cities configuration should not be empty"
  }

  assert {
    condition     = var.log_retention_days > 0
    error_message = "Log retention days should be positive"
  }
}