# Basic Terraform configuration validation tests
# These tests validate the configuration without requiring AWS credentials

variables {
  project_name                          = "test-weather-app"
  environment                           = "test"
  weather_service_identification_domain = "test.example.com"
  aws_region                            = "eu-west-1"
  budget_limit                          = 50
  log_retention_days                    = 180

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
}

run "validate_basic_configuration" {
  command = plan

  # Test that basic variables are properly set
  assert {
    condition     = var.project_name == "test-weather-app"
    error_message = "Project name should be set correctly"
  }

  assert {
    condition     = var.environment == "test"
    error_message = "Environment should be set correctly"
  }

  assert {
    condition     = length(var.cities_config) > 0
    error_message = "Cities configuration should not be empty"
  }
}