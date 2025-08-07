# Test for monitoring module CloudWatch dashboard and alarms

provider "aws" {
  region                      = "us-east-1"
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true
  access_key                  = "mock_access_key"
  secret_key                  = "mock_secret_key"
}

run "test_monitoring_module" {
  command = plan

  module {
    source = "../../modules/monitoring"
  }

  variables {
    name_prefix                   = "weather-test"
    environment                   = "test"
    budget_limit                  = 50
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

  # Test that CloudWatch dashboard is created
  assert {
    condition     = aws_cloudwatch_dashboard.weather_app.dashboard_name == "weather-test-dashboard"
    error_message = "CloudWatch dashboard name should match expected pattern"
  }

  # Test that all required alarms are created
  assert {
    condition     = aws_cloudwatch_metric_alarm.lambda_error_rate.alarm_name == "weather-test-lambda-error-rate"
    error_message = "Lambda error rate alarm should be created with correct name"
  }

  assert {
    condition     = aws_cloudwatch_metric_alarm.api_gateway_5xx_errors.alarm_name == "weather-test-api-gateway-5xx-errors"
    error_message = "API Gateway 5XX error alarm should be created with correct name"
  }

  assert {
    condition     = aws_cloudwatch_metric_alarm.dynamodb_throttling.alarm_name == "weather-test-dynamodb-throttling"
    error_message = "DynamoDB throttling alarm should be created with correct name"
  }

  # Test that custom metric filters are created when log group is provided
  assert {
    condition     = length(aws_cloudwatch_log_metric_filter.weather_api_success) == 1
    error_message = "Weather API success metric filter should be created when log group is provided"
  }

  assert {
    condition     = length(aws_cloudwatch_log_metric_filter.weather_api_failure) == 1
    error_message = "Weather API failure metric filter should be created when log group is provided"
  }

  # Test that log retention is set correctly
  assert {
    condition     = length(aws_cloudwatch_log_group.lambda_logs_retention) == 1
    error_message = "Lambda log retention should be configured when log group is provided"
  }
}

run "test_monitoring_without_log_groups" {
  command = plan

  module {
    source = "../../modules/monitoring"
  }

  variables {
    name_prefix                   = "weather-test"
    environment                   = "test"
    budget_limit                  = 50
    lambda_function_name          = "weather-test-lambda"
    api_gateway_id                = "test-api-gateway"
    api_gateway_stage_name        = "prod"
    dynamodb_table_name           = "weather-test-cache"
    cloudwatch_log_group_name     = ""
    api_gateway_log_group_name    = ""
    common_tags = {
      Service     = "weather-forecast-app"
      Environment = "test"
      ManagedBy   = "terraform"
    }
  }

  # Test that metric filters are not created when log groups are not provided
  assert {
    condition     = length(aws_cloudwatch_log_metric_filter.weather_api_success) == 0
    error_message = "Weather API success metric filter should not be created when log group is not provided"
  }

  assert {
    condition     = length(aws_cloudwatch_log_metric_filter.weather_api_failure) == 0
    error_message = "Weather API failure metric filter should not be created when log group is not provided"
  }

  # Test that log retention resources are not created when log groups are not provided
  assert {
    condition     = length(aws_cloudwatch_log_group.lambda_logs_retention) == 0
    error_message = "Lambda log retention should not be configured when log group is not provided"
  }

  assert {
    condition     = length(aws_cloudwatch_log_group.api_gateway_logs_retention) == 0
    error_message = "API Gateway log retention should not be configured when log group is not provided"
  }
}