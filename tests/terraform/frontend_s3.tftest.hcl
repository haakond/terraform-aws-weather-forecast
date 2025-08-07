# Test file for frontend S3 bucket configuration

run "validate_s3_bucket_configuration" {
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

  # Test that S3 bucket is created with proper naming
  assert {
    condition     = can(regex("^test-weather-app-frontend-[a-z0-9]{8}$", aws_s3_bucket.website.bucket))
    error_message = "S3 bucket name should follow the pattern: {name_prefix}-frontend-{random_suffix}"
  }

  # Test that versioning is enabled
  assert {
    condition     = aws_s3_bucket_versioning.website.versioning_configuration[0].status == "Enabled"
    error_message = "S3 bucket versioning should be enabled"
  }

  # Test that server-side encryption is configured
  assert {
    condition     = aws_s3_bucket_server_side_encryption_configuration.website.rule[0].apply_server_side_encryption_by_default[0].sse_algorithm == "AES256"
    error_message = "S3 bucket should have AES256 encryption enabled"
  }

  # Test that public access is blocked
  assert {
    condition = (
      aws_s3_bucket_public_access_block.website.block_public_acls == true &&
      aws_s3_bucket_public_access_block.website.block_public_policy == true &&
      aws_s3_bucket_public_access_block.website.ignore_public_acls == true &&
      aws_s3_bucket_public_access_block.website.restrict_public_buckets == true
    )
    error_message = "S3 bucket should have all public access blocked"
  }

  # Test that lifecycle configuration is present
  assert {
    condition     = length(aws_s3_bucket_lifecycle_configuration.website.rule) >= 2
    error_message = "S3 bucket should have lifecycle rules configured"
  }

  # Test that CloudFront Origin Access Control is created
  assert {
    condition     = aws_cloudfront_origin_access_control.website.origin_access_control_origin_type == "s3"
    error_message = "CloudFront OAC should be configured for S3 origin"
  }

  # Test that proper tags are applied
  assert {
    condition = (
      aws_s3_bucket.website.tags["Service"] == "weather-forecast-app" &&
      aws_s3_bucket.website.tags["Environment"] == "test" &&
      aws_s3_bucket.website.tags["Name"] == "test-weather-app-frontend-bucket"
    )
    error_message = "S3 bucket should have proper tags applied"
  }
}

run "validate_cloudfront_configuration" {
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

  # Test that CloudFront distribution is enabled
  assert {
    condition     = aws_cloudfront_distribution.website.enabled == true
    error_message = "CloudFront distribution should be enabled"
  }

  # Test that IPv6 is enabled
  assert {
    condition     = aws_cloudfront_distribution.website.is_ipv6_enabled == true
    error_message = "CloudFront distribution should have IPv6 enabled"
  }

  # Test that HTTPS redirect is configured
  assert {
    condition     = aws_cloudfront_distribution.website.default_cache_behavior[0].viewer_protocol_policy == "redirect-to-https"
    error_message = "CloudFront should redirect HTTP to HTTPS"
  }

  # Test that compression is enabled
  assert {
    condition     = aws_cloudfront_distribution.website.default_cache_behavior[0].compress == true
    error_message = "CloudFront should have compression enabled"
  }

  # Test that custom error responses are configured
  assert {
    condition     = length(aws_cloudfront_distribution.website.custom_error_response) >= 2
    error_message = "CloudFront should have custom error responses configured"
  }

  # Test that proper tags are applied to CloudFront
  assert {
    condition = (
      aws_cloudfront_distribution.website.tags["Service"] == "weather-forecast-app" &&
      aws_cloudfront_distribution.website.tags["Environment"] == "test" &&
      aws_cloudfront_distribution.website.tags["Name"] == "test-weather-app-frontend-distribution"
    )
    error_message = "CloudFront distribution should have proper tags applied"
  }
}

run "validate_outputs" {
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

  # Test that all required outputs are present
  assert {
    condition     = output.cloudfront_distribution_domain != null
    error_message = "CloudFront distribution domain output should not be null"
  }

  assert {
    condition     = output.cloudfront_distribution_id != null
    error_message = "CloudFront distribution ID output should not be null"
  }

  assert {
    condition     = output.s3_bucket_name != null
    error_message = "S3 bucket name output should not be null"
  }

  assert {
    condition     = output.s3_bucket_arn != null
    error_message = "S3 bucket ARN output should not be null"
  }

  assert {
    condition     = output.website_url != null
    error_message = "Website URL output should not be null"
  }

  # Test that website URL starts with https://
  assert {
    condition     = can(regex("^https://", output.website_url))
    error_message = "Website URL should start with https://"
  }
}