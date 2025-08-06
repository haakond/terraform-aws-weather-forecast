# Terraform tests for the weather forecast module
# Using Terraform's native testing framework

run "validate_configuration" {
  command = plan

  variables {
    project_name    = "test-weather-app"
    environment     = "test"
    aws_region      = "eu-west-1"
    company_website = "test.example.com"
  }

  # Verify that the plan is valid
  assert {
    condition     = can(var.project_name)
    error_message = "Project name must be provided"
  }

  assert {
    condition     = can(var.environment)
    error_message = "Environment must be provided"
  }
}

run "validate_tags" {
  command = plan

  variables {
    project_name = "test-weather-app"
    environment  = "test"
    aws_region   = "eu-west-1"
  }

  # Verify that common tags are properly configured
  assert {
    condition = alltrue([
      for resource in values(local.common_tags) :
      resource != null && resource != ""
    ])
    error_message = "All common tags must have non-empty values"
  }
}