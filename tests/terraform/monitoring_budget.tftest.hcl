# Test for monitoring module AWS Budget and cost monitoring

provider "aws" {
  region                      = "us-east-1"
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true
  access_key                  = "mock_access_key"
  secret_key                  = "mock_secret_key"
}

run "test_budget_configuration" {
  command = plan

  module {
    source = "../../modules/monitoring"
  }

  variables {
    name_prefix                   = "weather-test"
    environment                   = "test"
    budget_limit                  = 100
    lambda_function_name          = "weather-test-lambda"
    api_gateway_id                = "test-api-gateway"
    api_gateway_stage_name        = "prod"
    dynamodb_table_name           = "weather-test-cache"
    cloudwatch_log_group_name     = "/aws/lambda/weather-test-lambda"
    api_gateway_log_group_name    = "/aws/apigateway/weather-test-api"
    common_tags = {
      Service     = "weather-forecast-app"
      Environment = "test"
      ManagedBy   = "terraform"
    }
  }

  # Test that AWS Budget is created with correct configuration
  assert {
    condition     = aws_budgets_budget.weather_app_budget.name == "weather-test-budget"
    error_message = "AWS Budget name should match expected pattern"
  }

  assert {
    condition     = aws_budgets_budget.weather_app_budget.limit_amount == "100"
    error_message = "AWS Budget limit should match the provided budget_limit variable"
  }

  assert {
    condition     = aws_budgets_budget.weather_app_budget.budget_type == "COST"
    error_message = "AWS Budget type should be COST"
  }

  assert {
    condition     = aws_budgets_budget.weather_app_budget.time_unit == "MONTHLY"
    error_message = "AWS Budget time unit should be MONTHLY"
  }

  # Test that cost monitoring dashboard is created
  assert {
    condition     = aws_cloudwatch_dashboard.cost_monitoring.dashboard_name == "weather-test-cost-dashboard"
    error_message = "Cost monitoring dashboard name should match expected pattern"
  }

  # Test that budget has Service tag filter
  assert {
    condition     = length(aws_budgets_budget.weather_app_budget.cost_filter) > 0
    error_message = "AWS Budget should have cost filters configured"
  }

  # Test that budget has notification thresholds
  assert {
    condition     = length(aws_budgets_budget.weather_app_budget.notification) == 2
    error_message = "AWS Budget should have two notification thresholds (80% actual, 100% forecasted)"
  }
}

run "test_budget_with_different_limit" {
  command = plan

  module {
    source = "../../modules/monitoring"
  }

  variables {
    name_prefix                   = "weather-prod"
    environment                   = "production"
    budget_limit                  = 500
    lambda_function_name          = "weather-prod-lambda"
    api_gateway_id                = "prod-api-gateway"
    api_gateway_stage_name        = "prod"
    dynamodb_table_name           = "weather-prod-cache"
    cloudwatch_log_group_name     = "/aws/lambda/weather-prod-lambda"
    api_gateway_log_group_name    = "/aws/apigateway/weather-prod-api"
    common_tags = {
      Service     = "weather-forecast-app"
      Environment = "production"
      ManagedBy   = "terraform"
    }
  }

  # Test that budget limit is correctly set for different environments
  assert {
    condition     = aws_budgets_budget.weather_app_budget.limit_amount == "500"
    error_message = "AWS Budget limit should match the provided budget_limit variable for production"
  }

  assert {
    condition     = aws_budgets_budget.weather_app_budget.name == "weather-prod-budget"
    error_message = "AWS Budget name should include environment prefix"
  }
}