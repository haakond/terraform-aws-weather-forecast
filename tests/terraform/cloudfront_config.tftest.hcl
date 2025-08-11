# CloudFront configuration validation tests
# These tests validate the CloudFront price class and optimization settings

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

run "validate_cloudfront_price_class" {
  command = plan

  # Test that CloudFront uses price class 100 for cost optimization
  assert {
    condition     = output.cloudfront_price_class == "PriceClass_100"
    error_message = "CloudFront should use PriceClass_100 for cost optimization covering Europe and US"
  }
}

run "validate_cloudfront_outputs" {
  command = plan

  # Test that CloudFront distribution outputs are available
  assert {
    condition     = length(output.cloudfront_distribution_domain) > 0
    error_message = "CloudFront distribution domain should be available"
  }

  assert {
    condition     = length(output.cloudfront_distribution_id) > 0
    error_message = "CloudFront distribution ID should be available"
  }

  assert {
    condition     = length(output.website_url) > 0
    error_message = "Website URL should be available"
  }
}

run "validate_s3_bucket_outputs" {
  command = plan

  # Test that S3 bucket outputs are available
  assert {
    condition     = length(output.s3_bucket_name) > 0
    error_message = "S3 bucket name should be available"
  }

  assert {
    condition     = length(output.s3_bucket_arn) > 0
    error_message = "S3 bucket ARN should be available"
  }
}