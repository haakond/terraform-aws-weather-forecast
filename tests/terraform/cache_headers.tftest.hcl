# Test file to validate cache header configuration for frontend assets
# This test ensures that static assets are configured with proper Cache-Control headers

variables {
  name_prefix = "test-weather-app"
  environment = "test"
  common_tags = {
    Service = "weather-forecast-app"
    Environment = "test"
  }
}

run "validate_cache_headers" {
  command = plan

  module {
    source = "../../modules/frontend"
  }

  variables {
    name_prefix = var.name_prefix
    environment = var.environment
    common_tags = var.common_tags
    frontend_source_path = "frontend"
    api_gateway_url = "https://test-api.example.com"
  }

  # Test that S3 objects have proper cache control headers
  assert {
    condition = alltrue([
      for obj in aws_s3_object.frontend_files :
      can(regex("max-age=900", obj.cache_control))
    ])
    error_message = "All S3 objects should have Cache-Control headers with max-age=900 (15 minutes)"
  }

  # Test that CloudFront default cache behavior has 15-minute TTL
  assert {
    condition = aws_cloudfront_distribution.website.default_cache_behavior[0].default_ttl == 900
    error_message = "CloudFront default cache behavior should have 15-minute TTL (900 seconds)"
  }

  # Test that CloudFront static assets cache behavior has 15-minute TTL
  assert {
    condition = aws_cloudfront_distribution.website.ordered_cache_behavior[0].default_ttl == 900
    error_message = "CloudFront static assets cache behavior should have 15-minute TTL (900 seconds)"
  }

  # Test that CloudFront forwards Cache-Control headers for static assets
  assert {
    condition = contains(
      aws_cloudfront_distribution.website.ordered_cache_behavior[0].forwarded_values[0].headers,
      "Cache-Control"
    )
    error_message = "CloudFront should forward Cache-Control headers for static assets"
  }

  # Test that CloudFront has additional cache behavior for other static content
  assert {
    condition = length(aws_cloudfront_distribution.website.ordered_cache_behavior) >= 2
    error_message = "CloudFront should have cache behaviors for different static content types"
  }

  # Test that additional static content cache behavior has 15-minute TTL
  assert {
    condition = aws_cloudfront_distribution.website.ordered_cache_behavior[1].default_ttl == 900
    error_message = "CloudFront additional static content cache behavior should have 15-minute TTL (900 seconds)"
  }

  # Test that additional static content cache behavior forwards Cache-Control headers
  assert {
    condition = contains(
      aws_cloudfront_distribution.website.ordered_cache_behavior[1].forwarded_values[0].headers,
      "Cache-Control"
    )
    error_message = "CloudFront should forward Cache-Control headers for additional static content"
  }

  # Test that max TTL is also set to 15 minutes for consistency
  assert {
    condition = aws_cloudfront_distribution.website.default_cache_behavior[0].max_ttl == 900
    error_message = "CloudFront default cache behavior max TTL should be 15 minutes (900 seconds)"
  }

  assert {
    condition = aws_cloudfront_distribution.website.ordered_cache_behavior[0].max_ttl == 900
    error_message = "CloudFront static assets cache behavior max TTL should be 15 minutes (900 seconds)"
  }

  # Test that additional static content cache behavior max TTL is also set to 15 minutes
  assert {
    condition = aws_cloudfront_distribution.website.ordered_cache_behavior[1].max_ttl == 900
    error_message = "CloudFront additional static content cache behavior max TTL should be 15 minutes (900 seconds)"
  }
}