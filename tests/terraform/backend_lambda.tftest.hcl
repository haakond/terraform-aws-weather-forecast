# Test file for backend Lambda configuration
# This file tests the Lambda function Terraform configuration

variables {
  project_name    = "test-weather-app"
  service_name    = "weather-forecast-app"
  environment     = "test"
  company_website = "example.com"

  common_tags = {
    Environment = "test"
    Owner       = "terraform"
  }
}

# Test Lambda function configuration
run "test_lambda_function_configuration" {
  command = plan

  module {
    source = "../../modules/backend"
  }

  # Test that Lambda function is configured correctly
  assert {
    condition     = aws_lambda_function.weather_api.runtime == "python3.11"
    error_message = "Lambda function should use Python 3.11 runtime"
  }

  assert {
    condition     = aws_lambda_function.weather_api.timeout == 30
    error_message = "Lambda function timeout should be 30 seconds"
  }

  assert {
    condition     = aws_lambda_function.weather_api.memory_size == 512
    error_message = "Lambda function memory should be 512 MB by default"
  }

  assert {
    condition     = aws_lambda_function.weather_api.handler == "lambda_handler.lambda_handler"
    error_message = "Lambda function handler should be lambda_handler.lambda_handler"
  }
}

# Test X-Ray tracing configuration
run "test_xray_tracing" {
  command = plan

  module {
    source = "../../modules/backend"
  }

  assert {
    condition     = aws_lambda_function.weather_api.tracing_config[0].mode == "Active"
    error_message = "X-Ray tracing should be active"
  }
}

# Test environment variables
run "test_environment_variables" {
  command = plan

  module {
    source = "../../modules/backend"
  }

  variables {
    company_website = "example.com"
    log_level      = "DEBUG"
  }

  assert {
    condition     = aws_lambda_function.weather_api.environment[0].variables.COMPANY_WEBSITE == "example.com"
    error_message = "COMPANY_WEBSITE environment variable should be set correctly"
  }

  assert {
    condition     = aws_lambda_function.weather_api.environment[0].variables.LOG_LEVEL == "DEBUG"
    error_message = "LOG_LEVEL environment variable should be set correctly"
  }

  assert {
    condition     = contains(keys(aws_lambda_function.weather_api.environment[0].variables), "DYNAMODB_TABLE_NAME")
    error_message = "DYNAMODB_TABLE_NAME environment variable should be present"
  }
}

# Test CloudWatch log group
run "test_cloudwatch_logs" {
  command = plan

  module {
    source = "../../modules/backend"
  }

  variables {
    log_retention_days = 90
  }

  assert {
    condition     = aws_cloudwatch_log_group.lambda_logs.name == "/aws/lambda/test-weather-app-weather-api"
    error_message = "CloudWatch log group should have correct name"
  }

  assert {
    condition     = aws_cloudwatch_log_group.lambda_logs.retention_in_days == 90
    error_message = "CloudWatch log group should have correct retention period"
  }
}

# Test Lambda alias
run "test_lambda_alias" {
  command = plan

  module {
    source = "../../modules/backend"
  }

  assert {
    condition     = aws_lambda_alias.weather_api_live.name == "live"
    error_message = "Lambda alias should be named 'live'"
  }

  assert {
    condition     = aws_lambda_alias.weather_api_live.function_version == "$LATEST"
    error_message = "Lambda alias should point to $LATEST version"
  }
}