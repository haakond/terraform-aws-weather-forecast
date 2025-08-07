# Backend Module - Lambda, API Gateway, and DynamoDB
# This module handles the serverless backend infrastructure

# DynamoDB table for weather data caching
resource "aws_dynamodb_table" "weather_cache" {
  name         = "${var.project_name}-weather-cache"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "city_id"

  attribute {
    name = "city_id"
    type = "S"
  }

  # TTL configuration for automatic cache expiration (1 hour = 3600 seconds)
  ttl {
    attribute_name = "ttl"
    enabled        = true
  }

  # Point-in-time recovery for data protection
  point_in_time_recovery {
    enabled = true
  }

  # Server-side encryption with AWS managed keys
  server_side_encryption {
    enabled = true
  }

  # Deletion protection for production environments
  deletion_protection_enabled = var.environment == "prod" ? true : false

  tags = merge(var.common_tags, {
    Name    = "${var.project_name}-weather-cache"
    Service = var.service_name
  })
}

# IAM role for Lambda function to access DynamoDB
resource "aws_iam_role" "lambda_dynamodb_role" {
  name = "${var.project_name}-lambda-dynamodb-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = merge(var.common_tags, {
    Name    = "${var.project_name}-lambda-dynamodb-role"
    Service = var.service_name
  })
}

# IAM policy for DynamoDB access with least privilege
resource "aws_iam_policy" "lambda_dynamodb_policy" {
  name        = "${var.project_name}-lambda-dynamodb-policy"
  description = "IAM policy for Lambda to access DynamoDB weather cache table"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:Query"
        ]
        Resource = aws_dynamodb_table.weather_cache.arn
        Condition = {
          "ForAllValues:StringEquals" = {
            "dynamodb:Attributes" = [
              "city_id",
              "city_name",
              "country",
              "forecast",
              "last_updated",
              "ttl"
            ]
          }
        }
      },
      {
        Effect = "Allow"
        Action = [
          "xray:PutTraceSegments",
          "xray:PutTelemetryRecords"
        ]
        Resource = "*"
      }
    ]
  })

  tags = merge(var.common_tags, {
    Name    = "${var.project_name}-lambda-dynamodb-policy"
    Service = var.service_name
  })
}

# Attach DynamoDB policy to Lambda role
resource "aws_iam_role_policy_attachment" "lambda_dynamodb_policy_attachment" {
  role       = aws_iam_role.lambda_dynamodb_role.name
  policy_arn = aws_iam_policy.lambda_dynamodb_policy.arn
}

# Attach basic Lambda execution role
resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.lambda_dynamodb_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# CloudWatch Log Group for Lambda function
resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/${var.project_name}-weather-api"
  retention_in_days = var.log_retention_days

  tags = merge(var.common_tags, {
    Name    = "${var.project_name}-lambda-logs"
    Service = var.service_name
  })
}

# Create deployment package for Lambda function
data "archive_file" "lambda_zip" {
  type        = "zip"
  output_path = "${path.module}/../../lambda_deployment.zip"
  source_dir  = "${path.module}/../../src"

  excludes = [
    "__pycache__",
    "*.pyc",
    "*.pyo",
    "*.pyd",
    ".pytest_cache",
    "tests",
    "**/__pycache__",
    "**/*.pyc",
    "**/*.pyo",
    "**/*.pyd"
  ]
}

# Lambda function
resource "aws_lambda_function" "weather_api" {
  filename      = data.archive_file.lambda_zip.output_path
  function_name = "${var.project_name}-weather-api"
  role          = aws_iam_role.lambda_dynamodb_role.arn
  handler       = "lambda_handler.lambda_handler"
  runtime       = "python3.11"
  timeout       = 30
  memory_size   = var.lambda_memory_size

  # Source code hash for deployment updates
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256

  # Environment variables
  environment {
    variables = {
      COMPANY_WEBSITE     = var.company_website
      CITIES_CONFIG       = jsonencode(var.cities_config)
      DYNAMODB_TABLE_NAME = aws_dynamodb_table.weather_cache.name
      LOG_LEVEL           = var.log_level
    }
  }

  # X-Ray tracing configuration
  tracing_config {
    mode = "Active"
  }

  # VPC configuration (optional - can be enabled for enhanced security)
  dynamic "vpc_config" {
    for_each = var.vpc_config != null ? [var.vpc_config] : []
    content {
      subnet_ids         = vpc_config.value.subnet_ids
      security_group_ids = vpc_config.value.security_group_ids
    }
  }

  # Dead letter queue configuration
  dynamic "dead_letter_config" {
    for_each = var.dlq_target_arn != null ? [var.dlq_target_arn] : []
    content {
      target_arn = dead_letter_config.value
    }
  }

  # Reserved concurrency to prevent runaway costs
  reserved_concurrent_executions = var.lambda_reserved_concurrency

  depends_on = [
    aws_iam_role_policy_attachment.lambda_dynamodb_policy_attachment,
    aws_iam_role_policy_attachment.lambda_basic_execution,
    aws_cloudwatch_log_group.lambda_logs
  ]

  tags = merge(var.common_tags, {
    Name    = "${var.project_name}-weather-api"
    Service = var.service_name
  })
}

# Lambda function alias for blue-green deployments
resource "aws_lambda_alias" "weather_api_live" {
  name             = "live"
  description      = "Live alias for weather API Lambda function"
  function_name    = aws_lambda_function.weather_api.function_name
  function_version = "$LATEST"
}

# Data source for current AWS region
data "aws_region" "current" {}

# Data source for current AWS caller identity
data "aws_caller_identity" "current" {}

# IAM role for API Gateway CloudWatch Logs
resource "aws_iam_role" "api_gateway_cloudwatch_role" {
  name = "${var.project_name}-api-gateway-cloudwatch-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "apigateway.amazonaws.com"
        }
      }
    ]
  })

  tags = merge(var.common_tags, {
    Name    = "${var.project_name}-api-gateway-cloudwatch-role"
    Service = var.service_name
  })
}

# Attach the AWS managed policy for API Gateway CloudWatch Logs
resource "aws_iam_role_policy_attachment" "api_gateway_cloudwatch_logs" {
  role       = aws_iam_role.api_gateway_cloudwatch_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonAPIGatewayPushToCloudWatchLogs"
}

# Configure API Gateway account settings for CloudWatch Logs
resource "aws_api_gateway_account" "main" {
  cloudwatch_role_arn = aws_iam_role.api_gateway_cloudwatch_role.arn

  depends_on = [aws_iam_role_policy_attachment.api_gateway_cloudwatch_logs]
}

# API Gateway REST API
resource "aws_api_gateway_rest_api" "weather_api" {
  name        = "${var.project_name}-weather-api"
  description = "Weather forecast API for ${var.project_name}"

  endpoint_configuration {
    types = ["REGIONAL"]
  }

  # Binary media types for potential future file uploads
  binary_media_types = ["application/octet-stream"]

  tags = merge(var.common_tags, {
    Name    = "${var.project_name}-weather-api"
    Service = var.service_name
  })
}

# API Gateway deployment
resource "aws_api_gateway_deployment" "weather_api" {
  depends_on = [
    aws_api_gateway_method.weather_get,
    aws_api_gateway_method.weather_options,
    aws_api_gateway_method.health_get,
    aws_api_gateway_method.health_options,
    aws_api_gateway_integration.weather_lambda,
    aws_api_gateway_integration.weather_options,
    aws_api_gateway_integration.health_lambda,
    aws_api_gateway_integration.health_options
  ]

  rest_api_id = aws_api_gateway_rest_api.weather_api.id

  triggers = {
    redeployment = sha1(jsonencode([
      aws_api_gateway_resource.weather.id,
      aws_api_gateway_resource.health.id,
      aws_api_gateway_method.weather_get.id,
      aws_api_gateway_method.weather_options.id,
      aws_api_gateway_method.health_get.id,
      aws_api_gateway_method.health_options.id,
      aws_api_gateway_integration.weather_lambda.id,
      aws_api_gateway_integration.weather_options.id,
      aws_api_gateway_integration.health_lambda.id,
      aws_api_gateway_integration.health_options.id,
    ]))
  }

  lifecycle {
    create_before_destroy = true
  }
}

# API Gateway stage
resource "aws_api_gateway_stage" "weather_api" {
  deployment_id = aws_api_gateway_deployment.weather_api.id
  rest_api_id   = aws_api_gateway_rest_api.weather_api.id
  stage_name    = var.api_stage_name

  # X-Ray tracing
  xray_tracing_enabled = true

  # Access logging
  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_gateway_logs.arn
    format = jsonencode({
      requestId        = "$context.requestId"
      ip               = "$context.identity.sourceIp"
      caller           = "$context.identity.caller"
      user             = "$context.identity.user"
      requestTime      = "$context.requestTime"
      httpMethod       = "$context.httpMethod"
      resourcePath     = "$context.resourcePath"
      status           = "$context.status"
      protocol         = "$context.protocol"
      responseLength   = "$context.responseLength"
      responseTime     = "$context.responseTime"
      error            = "$context.error.message"
      integrationError = "$context.integration.error"
    })
  }

  tags = merge(var.common_tags, {
    Name    = "${var.project_name}-weather-api-${var.api_stage_name}"
    Service = var.service_name
  })

  # Ensure API Gateway account is configured with CloudWatch Logs role before enabling logging
  depends_on = [aws_api_gateway_account.main]
}

# CloudWatch Log Group for API Gateway
resource "aws_cloudwatch_log_group" "api_gateway_logs" {
  name              = "/aws/apigateway/${var.project_name}-weather-api"
  retention_in_days = var.log_retention_days

  tags = merge(var.common_tags, {
    Name    = "${var.project_name}-api-gateway-logs"
    Service = var.service_name
  })
}

# API Gateway method settings for throttling and logging
resource "aws_api_gateway_method_settings" "weather_api" {
  rest_api_id = aws_api_gateway_rest_api.weather_api.id
  stage_name  = aws_api_gateway_stage.weather_api.stage_name
  method_path = "*/*"

  settings {
    # Enable CloudWatch metrics
    metrics_enabled = true

    # Enable CloudWatch logging
    logging_level      = "INFO"
    data_trace_enabled = var.environment != "prod" # Disable in production for security

    # Throttling settings
    throttling_rate_limit  = var.api_throttling_rate_limit
    throttling_burst_limit = var.api_throttling_burst_limit

    # Caching settings (disabled for weather data freshness)
    caching_enabled = false
  }
}

# Usage plan for rate limiting
resource "aws_api_gateway_usage_plan" "weather_api" {
  name        = "${var.project_name}-weather-api-usage-plan"
  description = "Usage plan for weather API with rate limiting"

  api_stages {
    api_id = aws_api_gateway_rest_api.weather_api.id
    stage  = aws_api_gateway_stage.weather_api.stage_name
  }

  quota_settings {
    limit  = var.api_quota_limit
    period = "DAY"
  }

  throttle_settings {
    rate_limit  = var.api_throttling_rate_limit
    burst_limit = var.api_throttling_burst_limit
  }

  tags = merge(var.common_tags, {
    Name    = "${var.project_name}-weather-api-usage-plan"
    Service = var.service_name
  })
}

# Weather resource (/weather)
resource "aws_api_gateway_resource" "weather" {
  rest_api_id = aws_api_gateway_rest_api.weather_api.id
  parent_id   = aws_api_gateway_rest_api.weather_api.root_resource_id
  path_part   = "weather"
}

# Health resource (/health)
resource "aws_api_gateway_resource" "health" {
  rest_api_id = aws_api_gateway_rest_api.weather_api.id
  parent_id   = aws_api_gateway_rest_api.weather_api.root_resource_id
  path_part   = "health"
}

# GET method for weather endpoint
resource "aws_api_gateway_method" "weather_get" {
  rest_api_id   = aws_api_gateway_rest_api.weather_api.id
  resource_id   = aws_api_gateway_resource.weather.id
  http_method   = "GET"
  authorization = "NONE"

  # Request validation
  request_validator_id = aws_api_gateway_request_validator.weather_api.id
}

# OPTIONS method for weather endpoint (CORS preflight)
resource "aws_api_gateway_method" "weather_options" {
  rest_api_id   = aws_api_gateway_rest_api.weather_api.id
  resource_id   = aws_api_gateway_resource.weather.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

# GET method for health endpoint
resource "aws_api_gateway_method" "health_get" {
  rest_api_id   = aws_api_gateway_rest_api.weather_api.id
  resource_id   = aws_api_gateway_resource.health.id
  http_method   = "GET"
  authorization = "NONE"

  # Request validation
  request_validator_id = aws_api_gateway_request_validator.weather_api.id
}

# OPTIONS method for health endpoint (CORS preflight)
resource "aws_api_gateway_method" "health_options" {
  rest_api_id   = aws_api_gateway_rest_api.weather_api.id
  resource_id   = aws_api_gateway_resource.health.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

# Request validator for API Gateway
resource "aws_api_gateway_request_validator" "weather_api" {
  name                        = "${var.project_name}-weather-api-validator"
  rest_api_id                 = aws_api_gateway_rest_api.weather_api.id
  validate_request_body       = true
  validate_request_parameters = true
}

# Lambda integration for weather endpoint
resource "aws_api_gateway_integration" "weather_lambda" {
  rest_api_id = aws_api_gateway_rest_api.weather_api.id
  resource_id = aws_api_gateway_resource.weather.id
  http_method = aws_api_gateway_method.weather_get.http_method

  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_alias.weather_api_live.invoke_arn

  # Timeout configuration
  timeout_milliseconds = 29000 # Just under Lambda timeout

  # Error handling
  passthrough_behavior = "WHEN_NO_MATCH"
}

# Lambda integration for health endpoint
resource "aws_api_gateway_integration" "health_lambda" {
  rest_api_id = aws_api_gateway_rest_api.weather_api.id
  resource_id = aws_api_gateway_resource.health.id
  http_method = aws_api_gateway_method.health_get.http_method

  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_alias.weather_api_live.invoke_arn

  # Timeout configuration
  timeout_milliseconds = 29000 # Just under Lambda timeout

  # Error handling
  passthrough_behavior = "WHEN_NO_MATCH"
}

# CORS integration for weather OPTIONS method
resource "aws_api_gateway_integration" "weather_options" {
  rest_api_id = aws_api_gateway_rest_api.weather_api.id
  resource_id = aws_api_gateway_resource.weather.id
  http_method = aws_api_gateway_method.weather_options.http_method

  type = "MOCK"

  request_templates = {
    "application/json" = jsonencode({
      statusCode = 200
    })
  }
}

# CORS integration for health OPTIONS method
resource "aws_api_gateway_integration" "health_options" {
  rest_api_id = aws_api_gateway_rest_api.weather_api.id
  resource_id = aws_api_gateway_resource.health.id
  http_method = aws_api_gateway_method.health_options.http_method

  type = "MOCK"

  request_templates = {
    "application/json" = jsonencode({
      statusCode = 200
    })
  }
}

# Method responses for weather GET
resource "aws_api_gateway_method_response" "weather_get_200" {
  rest_api_id = aws_api_gateway_rest_api.weather_api.id
  resource_id = aws_api_gateway_resource.weather.id
  http_method = aws_api_gateway_method.weather_get.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin"  = true
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

# Method responses for weather GET errors
resource "aws_api_gateway_method_response" "weather_get_500" {
  rest_api_id = aws_api_gateway_rest_api.weather_api.id
  resource_id = aws_api_gateway_resource.weather.id
  http_method = aws_api_gateway_method.weather_get.http_method
  status_code = "500"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin"  = true
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
  }
}

# Method responses for health GET
resource "aws_api_gateway_method_response" "health_get_200" {
  rest_api_id = aws_api_gateway_rest_api.weather_api.id
  resource_id = aws_api_gateway_resource.health.id
  http_method = aws_api_gateway_method.health_get.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin"  = true
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

# Method responses for weather OPTIONS (CORS preflight)
resource "aws_api_gateway_method_response" "weather_options_200" {
  rest_api_id = aws_api_gateway_rest_api.weather_api.id
  resource_id = aws_api_gateway_resource.weather.id
  http_method = aws_api_gateway_method.weather_options.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin"  = true
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
  }
}

# Method responses for health OPTIONS (CORS preflight)
resource "aws_api_gateway_method_response" "health_options_200" {
  rest_api_id = aws_api_gateway_rest_api.weather_api.id
  resource_id = aws_api_gateway_resource.health.id
  http_method = aws_api_gateway_method.health_options.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin"  = true
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
  }
}

# Integration responses for weather GET
resource "aws_api_gateway_integration_response" "weather_get_200" {
  rest_api_id = aws_api_gateway_rest_api.weather_api.id
  resource_id = aws_api_gateway_resource.weather.id
  http_method = aws_api_gateway_method.weather_get.http_method
  status_code = aws_api_gateway_method_response.weather_get_200.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,OPTIONS'"
  }

  depends_on = [aws_api_gateway_integration.weather_lambda]
}

# Integration responses for weather GET errors
resource "aws_api_gateway_integration_response" "weather_get_500" {
  rest_api_id = aws_api_gateway_rest_api.weather_api.id
  resource_id = aws_api_gateway_resource.weather.id
  http_method = aws_api_gateway_method.weather_get.http_method
  status_code = aws_api_gateway_method_response.weather_get_500.status_code

  selection_pattern = ".*"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,OPTIONS'"
  }

  depends_on = [aws_api_gateway_integration.weather_lambda]
}

# Integration responses for health GET
resource "aws_api_gateway_integration_response" "health_get_200" {
  rest_api_id = aws_api_gateway_rest_api.weather_api.id
  resource_id = aws_api_gateway_resource.health.id
  http_method = aws_api_gateway_method.health_get.http_method
  status_code = aws_api_gateway_method_response.health_get_200.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,OPTIONS'"
  }

  depends_on = [aws_api_gateway_integration.health_lambda]
}

# Integration responses for weather OPTIONS (CORS preflight)
resource "aws_api_gateway_integration_response" "weather_options_200" {
  rest_api_id = aws_api_gateway_rest_api.weather_api.id
  resource_id = aws_api_gateway_resource.weather.id
  http_method = aws_api_gateway_method.weather_options.http_method
  status_code = aws_api_gateway_method_response.weather_options_200.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,OPTIONS'"
  }

  depends_on = [aws_api_gateway_integration.weather_options]
}

# Integration responses for health OPTIONS (CORS preflight)
resource "aws_api_gateway_integration_response" "health_options_200" {
  rest_api_id = aws_api_gateway_rest_api.weather_api.id
  resource_id = aws_api_gateway_resource.health.id
  http_method = aws_api_gateway_method.health_options.http_method
  status_code = aws_api_gateway_method_response.health_options_200.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,OPTIONS'"
  }

  depends_on = [aws_api_gateway_integration.health_options]
}

# Lambda permission for API Gateway to invoke the function
resource "aws_lambda_permission" "api_gateway_invoke" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.weather_api.function_name
  principal     = "apigateway.amazonaws.com"
  qualifier     = aws_lambda_alias.weather_api_live.name

  # More specific source ARN for security
  source_arn = "${aws_api_gateway_rest_api.weather_api.execution_arn}/*/*"
}