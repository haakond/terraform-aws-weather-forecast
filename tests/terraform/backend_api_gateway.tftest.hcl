# API Gateway Configuration Tests
# Tests for the API Gateway REST API, methods, integrations, and CORS configuration

variables {
  project_name = "weather-forecast-test"
  service_name = "weather-forecast-app"
  environment  = "test"

  common_tags = {
    Environment = "test"
    Project     = "weather-forecast-test"
    Service     = "weather-forecast-app"
  }

  # API Gateway specific test variables
  api_stage_name             = "test"
  api_throttling_rate_limit  = 50
  api_throttling_burst_limit = 100
  api_quota_limit           = 5000
}

# Test API Gateway REST API creation
run "test_api_gateway_creation" {
  command = plan

  module {
    source = "../../modules/backend"
  }

  # Verify API Gateway REST API is created with correct configuration
  assert {
    condition     = aws_api_gateway_rest_api.weather_api.name == "weather-forecast-test-weather-api"
    error_message = "API Gateway REST API name should match project name pattern"
  }

  assert {
    condition     = aws_api_gateway_rest_api.weather_api.endpoint_configuration[0].types[0] == "REGIONAL"
    error_message = "API Gateway should use REGIONAL endpoint configuration"
  }

  assert {
    condition     = contains(keys(aws_api_gateway_rest_api.weather_api.tags), "Service")
    error_message = "API Gateway should have Service tag"
  }
}

# Test API Gateway stage configuration
run "test_api_gateway_stage" {
  command = plan

  module {
    source = "../../modules/backend"
  }

  variables {
    api_stage_name = "test"
  }

  assert {
    condition     = aws_api_gateway_stage.weather_api.stage_name == "test"
    error_message = "API Gateway stage name should match variable"
  }

  assert {
    condition     = aws_api_gateway_stage.weather_api.xray_tracing_enabled == true
    error_message = "API Gateway stage should have X-Ray tracing enabled"
  }

  assert {
    condition     = aws_api_gateway_stage.weather_api.access_log_settings != null
    error_message = "API Gateway stage should have access logging configured"
  }
}

# Test API Gateway resources
run "test_api_gateway_resources" {
  command = plan

  module {
    source = "../../modules/backend"
  }

  # Verify weather resource
  assert {
    condition     = aws_api_gateway_resource.weather.path_part == "weather"
    error_message = "Weather resource should have correct path part"
  }

  # Verify health resource
  assert {
    condition     = aws_api_gateway_resource.health.path_part == "health"
    error_message = "Health resource should have correct path part"
  }
}

# Test API Gateway methods
run "test_api_gateway_methods" {
  command = plan

  module {
    source = "../../modules/backend"
  }

  # Test weather GET method
  assert {
    condition     = aws_api_gateway_method.weather_get.http_method == "GET"
    error_message = "Weather endpoint should support GET method"
  }

  assert {
    condition     = aws_api_gateway_method.weather_get.authorization == "NONE"
    error_message = "Weather endpoint should not require authorization"
  }

  # Test weather OPTIONS method for CORS
  assert {
    condition     = aws_api_gateway_method.weather_options.http_method == "OPTIONS"
    error_message = "Weather endpoint should support OPTIONS method for CORS"
  }

  # Test health GET method
  assert {
    condition     = aws_api_gateway_method.health_get.http_method == "GET"
    error_message = "Health endpoint should support GET method"
  }
}

# Test Lambda integrations
run "test_lambda_integrations" {
  command = plan

  module {
    source = "../../modules/backend"
  }

  # Test weather Lambda integration
  assert {
    condition     = aws_api_gateway_integration.weather_lambda.type == "AWS_PROXY"
    error_message = "Weather endpoint should use AWS_PROXY integration"
  }

  assert {
    condition     = aws_api_gateway_integration.weather_lambda.integration_http_method == "POST"
    error_message = "Lambda integration should use POST method"
  }

  assert {
    condition     = aws_api_gateway_integration.weather_lambda.timeout_milliseconds == 29000
    error_message = "Lambda integration should have appropriate timeout"
  }
}

# Test CORS configuration
run "test_cors_configuration" {
  command = plan

  module {
    source = "../../modules/backend"
  }

  # Test weather OPTIONS integration
  assert {
    condition     = aws_api_gateway_integration.weather_options.type == "MOCK"
    error_message = "Weather OPTIONS should use MOCK integration for CORS"
  }

  # Test method responses include CORS headers
  assert {
    condition     = contains(keys(aws_api_gateway_method_response.weather_get_200.response_parameters), "method.response.header.Access-Control-Allow-Origin")
    error_message = "Weather GET 200 response should include CORS headers"
  }
}

# Test throttling configuration
run "test_throttling_configuration" {
  command = plan

  module {
    source = "../../modules/backend"
  }

  variables {
    api_throttling_rate_limit  = 50
    api_throttling_burst_limit = 100
    api_quota_limit           = 5000
  }

  # Test method settings
  assert {
    condition     = aws_api_gateway_method_settings.weather_api.settings[0].throttling_rate_limit == 50
    error_message = "API Gateway should have correct throttling rate limit"
  }

  assert {
    condition     = aws_api_gateway_method_settings.weather_api.settings[0].throttling_burst_limit == 100
    error_message = "API Gateway should have correct throttling burst limit"
  }

  assert {
    condition     = aws_api_gateway_method_settings.weather_api.settings[0].metrics_enabled == true
    error_message = "API Gateway should have CloudWatch metrics enabled"
  }
}

# Test CloudWatch logging
run "test_cloudwatch_logging" {
  command = plan

  module {
    source = "../../modules/backend"
  }

  # Test API Gateway log group
  assert {
    condition     = aws_cloudwatch_log_group.api_gateway_logs.retention_in_days == 180
    error_message = "API Gateway log group should have 180 days retention"
  }

  assert {
    condition     = contains(keys(aws_cloudwatch_log_group.api_gateway_logs.tags), "Service")
    error_message = "API Gateway log group should have Service tag"
  }

  # Test method settings logging
  assert {
    condition     = aws_api_gateway_method_settings.weather_api.settings[0].logging_level == "INFO"
    error_message = "API Gateway should have INFO logging level"
  }
}

# Test Lambda permissions
run "test_lambda_permissions" {
  command = plan

  module {
    source = "../../modules/backend"
  }

  assert {
    condition     = aws_lambda_permission.api_gateway_invoke.action == "lambda:InvokeFunction"
    error_message = "Lambda permission should allow InvokeFunction action"
  }

  assert {
    condition     = aws_lambda_permission.api_gateway_invoke.principal == "apigateway.amazonaws.com"
    error_message = "Lambda permission should be granted to API Gateway service"
  }

  assert {
    condition     = aws_lambda_permission.api_gateway_invoke.qualifier == "live"
    error_message = "Lambda permission should target the live alias"
  }
}