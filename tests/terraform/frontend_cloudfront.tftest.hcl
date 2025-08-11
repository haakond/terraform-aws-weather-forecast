# CloudFront configuration validation tests for frontend module only
# These tests validate the CloudFront price class and optimization settings

variables {
  name_prefix     = "test-weather-app"
  environment     = "test"
  api_gateway_url = "https://api.example.com"
  common_tags = {
    Service     = "weather-forecast-app"
    Environment = "test"
  }
}

run "validate_frontend_cloudfront_price_class" {
  command = plan

  module {
    source = "../../modules/frontend"
  }

  # Test that CloudFront uses price class 100 for cost optimization
  assert {
    condition     = var.cloudfront_price_class == "PriceClass_100"
    error_message = "CloudFront should use PriceClass_100 for cost optimization covering Europe and US"
  }
}

run "validate_frontend_cloudfront_outputs" {
  command = plan

  module {
    source = "../../modules/frontend"
  }

  # Test that CloudFront price class output is available
  assert {
    condition     = output.cloudfront_price_class == "PriceClass_100"
    error_message = "CloudFront price class output should be PriceClass_100"
  }
}