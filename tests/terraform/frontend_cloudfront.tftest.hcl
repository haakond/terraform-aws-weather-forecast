# Test file for frontend CloudFront configuration

run "validate_cloudfront_security_headers" {
  command = plan

  module {
    source = "../../modules/frontend"
  }

  variables {
    name_prefix = "test-weather-app"
    environment = "test"
    common_tags = {
      Service     = "weather-forecast-app"
      Environment = "test"
    }
  }

  # Test that security headers policy is created
  assert {
    condition     = aws_cloudfront_response_headers_policy.security_headers.name == "test-weather-app-security-headers"
    error_message = "Security headers policy should have correct name"
  }

  # Test that HSTS is configured
  assert {
    condition = (
      aws_cloudfront_response_headers_policy.security_headers.security_headers_config[0].strict_transport_security[0].access_control_max_age_sec == 31536000 &&
      aws_cloudfront_response_headers_policy.security_headers.security_headers_config[0].strict_transport_security[0].include_subdomains == true
    )
    error_message = "HSTS should be properly configured"
  }

  # Test that frame options are set to DENY
  assert {
    condition     = aws_cloudfront_response_headers_policy.security_headers.security_headers_config[0].frame_options[0].frame_option == "DENY"
    error_message = "Frame options should be set to DENY"
  }

  # Test that content type options are enabled
  assert {
    condition     = aws_cloudfront_response_headers_policy.security_headers.security_headers_config[0].content_type_options[0].override == true
    error_message = "Content type options should be enabled"
  }
}

run "validate_cloudfront_cache_behaviors" {
  command = plan

  module {
    source = "../../modules/frontend"
  }

  variables {
    name_prefix = "test-weather-app"
    environment = "test"
    common_tags = {
      Service     = "weather-forecast-app"
      Environment = "test"
    }
  }

  # Test that default cache behavior has security headers
  assert {
    condition     = aws_cloudfront_distribution.website.default_cache_behavior[0].response_headers_policy_id != null
    error_message = "Default cache behavior should have security headers policy"
  }

  # Test that static assets cache behavior has longer TTL
  assert {
    condition = (
      aws_cloudfront_distribution.website.ordered_cache_behavior[0].default_ttl == 86400 &&
      aws_cloudfront_distribution.website.ordered_cache_behavior[0].max_ttl == 31536000
    )
    error_message = "Static assets should have longer cache TTL"
  }

  # Test that static assets cache behavior has security headers
  assert {
    condition     = aws_cloudfront_distribution.website.ordered_cache_behavior[0].response_headers_policy_id != null
    error_message = "Static assets cache behavior should have security headers policy"
  }

  # Test that compression is enabled for both behaviors
  assert {
    condition = (
      aws_cloudfront_distribution.website.default_cache_behavior[0].compress == true &&
      aws_cloudfront_distribution.website.ordered_cache_behavior[0].compress == true
    )
    error_message = "Compression should be enabled for all cache behaviors"
  }
}

run "validate_cloudfront_origin_configuration" {
  command = plan

  module {
    source = "../../modules/frontend"
  }

  variables {
    name_prefix = "test-weather-app"
    environment = "test"
    common_tags = {
      Service     = "weather-forecast-app"
      Environment = "test"
    }
  }

  # Test that only one origin is configured (no failover)
  assert {
    condition     = length(aws_cloudfront_distribution.website.origin) == 1
    error_message = "CloudFront should have exactly one origin (no failover needed)"
  }

  # Test that origin uses OAC
  assert {
    condition     = aws_cloudfront_distribution.website.origin[0].origin_access_control_id != null
    error_message = "Origin should use Origin Access Control"
  }

  # Test that origin points to S3 bucket
  assert {
    condition     = can(regex("s3", aws_cloudfront_distribution.website.origin[0].domain_name))
    error_message = "Origin should point to S3 bucket"
  }
}

run "validate_cloudfront_error_pages" {
  command = plan

  module {
    source = "../../modules/frontend"
  }

  variables {
    name_prefix = "test-weather-app"
    environment = "test"
    common_tags = {
      Service     = "weather-forecast-app"
      Environment = "test"
    }
  }

  # Test that custom error responses are configured for SPA
  assert {
    condition = (
      length([for error in aws_cloudfront_distribution.website.custom_error_response : error if error.error_code == 404]) > 0 &&
      length([for error in aws_cloudfront_distribution.website.custom_error_response : error if error.error_code == 403]) > 0
    )
    error_message = "Custom error responses should be configured for 404 and 403 errors"
  }

  # Test that error responses redirect to index.html for SPA routing
  assert {
    condition = alltrue([
      for error in aws_cloudfront_distribution.website.custom_error_response :
      error.response_page_path == "/index.html" && error.response_code == 200
    ])
    error_message = "Error responses should redirect to index.html with 200 status for SPA routing"
  }
}