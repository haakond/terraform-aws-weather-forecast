# Monitoring Module - CloudWatch and AWS Budget
# This module handles monitoring, alerting, and cost management

# Data sources
data "aws_region" "current" {}

# CloudWatch Dashboard for Weather Forecast App
resource "aws_cloudwatch_dashboard" "weather_app" {
  dashboard_name = "${var.name_prefix}-dashboard"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AWS/Lambda", "Duration", "FunctionName", var.lambda_function_name],
            [".", "Errors", ".", "."],
            [".", "Invocations", ".", "."],
            [".", "Throttles", ".", "."]
          ]
          view    = "timeSeries"
          stacked = false
          region  = data.aws_region.current.id
          title   = "Lambda Function Metrics"
          period  = 300
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 0
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AWS/ApiGateway", "4XXError", "ApiName", var.api_gateway_id],
            [".", "5XXError", ".", "."],
            [".", "Count", ".", "."],
            [".", "Latency", ".", "."]
          ]
          view    = "timeSeries"
          stacked = false
          region  = data.aws_region.current.id
          title   = "API Gateway Metrics"
          period  = 300
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AWS/DynamoDB", "ConsumedReadCapacityUnits", "TableName", var.dynamodb_table_name],
            [".", "ConsumedWriteCapacityUnits", ".", "."],
            [".", "ThrottledRequests", ".", "."],
            [".", "SuccessfulRequestLatency", ".", ".", "Operation", "GetItem"],
            [".", "SuccessfulRequestLatency", ".", ".", "Operation", "PutItem"]
          ]
          view    = "timeSeries"
          stacked = false
          region  = data.aws_region.current.id
          title   = "DynamoDB Metrics"
          period  = 300
        }
      },
      {
        type   = "log"
        x      = 12
        y      = 6
        width  = 12
        height = 6

        properties = {
          query  = "SOURCE '${var.cloudwatch_log_group_name}' | fields @timestamp, @message | filter @message like /ERROR/ | sort @timestamp desc | limit 20"
          region = data.aws_region.current.id
          title  = "Recent Lambda Errors"
          view   = "table"
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 12
        width  = 12
        height = 6

        properties = {
          metrics = var.cloudfront_distribution_domain != "" ? [
            ["CloudWatchSynthetics", "SuccessPercent", "CanaryName", aws_synthetics_canary.weather_app_e2e.name],
            [".", "Duration", ".", "."],
            [".", "Failed", ".", "."]
          ] : []
          view    = "timeSeries"
          stacked = false
          region  = data.aws_region.current.id
          title   = "End-to-End Test Results"
          period  = 300
        }
      },
      {
        type   = "log"
        x      = 12
        y      = 12
        width  = 12
        height = 6

        properties = {
          query  = var.cloudfront_distribution_domain != "" ? "SOURCE '/aws/lambda/cwsyn-${aws_synthetics_canary.weather_app_e2e.name}' | fields @timestamp, @message | filter @message like /ERROR/ or @message like /FAIL/ | sort @timestamp desc | limit 10" : "fields @timestamp | limit 1"
          region = data.aws_region.current.id
          title  = "End-to-End Test Failures"
          view   = "table"
        }
      }
    ]
  })
}

# CloudWatch Alarms

# Lambda Function Error Rate Alarm
resource "aws_cloudwatch_metric_alarm" "lambda_error_rate" {
  alarm_name          = "${var.name_prefix}-lambda-error-rate"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = "300"
  statistic           = "Sum"
  threshold           = "5"
  alarm_description   = "This metric monitors lambda error rate"
  alarm_actions       = []

  dimensions = {
    FunctionName = var.lambda_function_name
  }

  tags = var.common_tags
}

# Lambda Function Duration Alarm
resource "aws_cloudwatch_metric_alarm" "lambda_duration" {
  alarm_name          = "${var.name_prefix}-lambda-duration"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "Duration"
  namespace           = "AWS/Lambda"
  period              = "300"
  statistic           = "Average"
  threshold           = "25000" # 25 seconds (Lambda timeout is 30s)
  alarm_description   = "This metric monitors lambda duration"
  alarm_actions       = []

  dimensions = {
    FunctionName = var.lambda_function_name
  }

  tags = var.common_tags
}

# API Gateway 5XX Error Alarm
resource "aws_cloudwatch_metric_alarm" "api_gateway_5xx_errors" {
  alarm_name          = "${var.name_prefix}-api-gateway-5xx-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "5XXError"
  namespace           = "AWS/ApiGateway"
  period              = "300"
  statistic           = "Sum"
  threshold           = "5"
  alarm_description   = "This metric monitors API Gateway 5XX errors"
  alarm_actions       = []

  dimensions = {
    ApiName = var.api_gateway_id
  }

  tags = var.common_tags
}

# API Gateway High Latency Alarm
resource "aws_cloudwatch_metric_alarm" "api_gateway_latency" {
  alarm_name          = "${var.name_prefix}-api-gateway-latency"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "Latency"
  namespace           = "AWS/ApiGateway"
  period              = "300"
  statistic           = "Average"
  threshold           = "5000" # 5 seconds
  alarm_description   = "This metric monitors API Gateway latency"
  alarm_actions       = []

  dimensions = {
    ApiName = var.api_gateway_id
  }

  tags = var.common_tags
}

# DynamoDB Throttling Alarm
resource "aws_cloudwatch_metric_alarm" "dynamodb_throttling" {
  alarm_name          = "${var.name_prefix}-dynamodb-throttling"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "ThrottledRequests"
  namespace           = "AWS/DynamoDB"
  period              = "300"
  statistic           = "Sum"
  threshold           = "0"
  alarm_description   = "This metric monitors DynamoDB throttling"
  alarm_actions       = []

  dimensions = {
    TableName = var.dynamodb_table_name
  }

  tags = var.common_tags
}

# Custom CloudWatch Log Metric Filter for Weather API Success Rate
resource "aws_cloudwatch_log_metric_filter" "weather_api_success" {
  count          = var.cloudwatch_log_group_name != "" ? 1 : 0
  name           = "${var.name_prefix}-weather-api-success"
  log_group_name = var.cloudwatch_log_group_name
  pattern        = "[timestamp, request_id, level=\"INFO\", message=\"Weather data retrieved successfully\"]"

  metric_transformation {
    name      = "WeatherAPISuccess"
    namespace = "WeatherForecastApp"
    value     = "1"
  }
}

# Custom CloudWatch Log Metric Filter for Weather API Failures
resource "aws_cloudwatch_log_metric_filter" "weather_api_failure" {
  count          = var.cloudwatch_log_group_name != "" ? 1 : 0
  name           = "${var.name_prefix}-weather-api-failure"
  log_group_name = var.cloudwatch_log_group_name
  pattern        = "[timestamp, request_id, level=\"ERROR\", message=\"Failed to retrieve weather data\"]"

  metric_transformation {
    name      = "WeatherAPIFailure"
    namespace = "WeatherForecastApp"
    value     = "1"
  }
}

# Weather API Success Rate Alarm
resource "aws_cloudwatch_metric_alarm" "weather_api_success_rate" {
  count               = var.cloudwatch_log_group_name != "" ? 1 : 0
  alarm_name          = "${var.name_prefix}-weather-api-success-rate"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = "2"
  threshold           = "0.8" # 80% success rate
  alarm_description   = "This metric monitors weather API success rate"
  alarm_actions       = []
  treat_missing_data  = "notBreaching"

  metric_query {
    id          = "success_rate"
    return_data = true

    metric {
      metric_name = "WeatherAPISuccess"
      namespace   = "WeatherForecastApp"
      period      = 300
      stat        = "Sum"
    }
  }

  metric_query {
    id          = "failure_rate"
    return_data = false

    metric {
      metric_name = "WeatherAPIFailure"
      namespace   = "WeatherForecastApp"
      period      = 300
      stat        = "Sum"
    }
  }

  metric_query {
    id          = "total_requests"
    return_data = false
    expression  = "success_rate + failure_rate"
  }

  metric_query {
    id          = "success_percentage"
    return_data = false
    expression  = "success_rate / total_requests"
  }

  tags = var.common_tags
}

# Log Retention Policies (180 days as per requirements)
resource "aws_cloudwatch_log_group" "lambda_logs_retention" {
  count             = var.cloudwatch_log_group_name != "" ? 1 : 0
  name              = var.cloudwatch_log_group_name
  retention_in_days = 180

  tags = var.common_tags
}

resource "aws_cloudwatch_log_group" "api_gateway_logs_retention" {
  count             = var.api_gateway_log_group_name != "" ? 1 : 0
  name              = var.api_gateway_log_group_name
  retention_in_days = 180

  tags = var.common_tags
}

# AWS Budget for cost monitoring
resource "aws_budgets_budget" "weather_app_budget" {
  name              = "${var.name_prefix}-budget"
  budget_type       = "COST"
  limit_amount      = var.budget_limit
  limit_unit        = "USD"
  time_unit         = "MONTHLY"
  time_period_start = "2024-01-01_00:00"

  cost_filter {
    name   = "TagKeyValue"
    values = ["Service$weather-forecast-app"]
  }

  tags = var.common_tags
}

# CloudWatch Synthetics for End-to-End Testing

# S3 bucket for Synthetics artifacts
resource "aws_s3_bucket" "synthetics_artifacts" {
  bucket        = "${var.name_prefix}-synthetics-artifacts"
  force_destroy = true

  tags = var.common_tags
}

resource "aws_s3_bucket_versioning" "synthetics_artifacts" {
  bucket = aws_s3_bucket.synthetics_artifacts.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "synthetics_artifacts" {
  bucket = aws_s3_bucket.synthetics_artifacts.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "synthetics_artifacts" {
  bucket = aws_s3_bucket.synthetics_artifacts.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# IAM role for Synthetics canary
resource "aws_iam_role" "synthetics_canary_role" {
  name = "${var.name_prefix}-synthetics-canary-role"

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

  tags = var.common_tags
}

# IAM policy for Synthetics canary
resource "aws_iam_role_policy" "synthetics_canary_policy" {
  name = "${var.name_prefix}-synthetics-canary-policy"
  role = aws_iam_role.synthetics_canary_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:GetBucketLocation",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.synthetics_artifacts.arn,
          "${aws_s3_bucket.synthetics_artifacts.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:${data.aws_region.current.id}:*:log-group:/aws/lambda/cwsyn-*"
      },
      {
        Effect = "Allow"
        Action = [
          "cloudwatch:PutMetricData"
        ]
        Resource = "*"
        Condition = {
          StringEquals = {
            "cloudwatch:namespace" = "CloudWatchSynthetics"
          }
        }
      },
      {
        Effect = "Allow"
        Action = [
          "xray:PutTraceSegments"
        ]
        Resource = "*"
      }
    ]
  })
}

# Custom policy for Synthetics execution (replaces deprecated AWS managed policy)
resource "aws_iam_role_policy" "synthetics_canary_execution" {
  name = "${var.name_prefix}-synthetics-execution-policy"
  role = aws_iam_role.synthetics_canary_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:GetObjectVersion",
          "s3:PutObjectAcl",
          "s3:GetBucketLocation"
        ]
        Resource = [
          "${aws_s3_bucket.synthetics_artifacts.arn}",
          "${aws_s3_bucket.synthetics_artifacts.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:CreateLogGroup"
        ]
        Resource = "arn:aws:logs:*:*:log-group:/aws/lambda/cwsyn-*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:ListAllMyBuckets",
          "xray:PutTraceSegments"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "cloudwatch:PutMetricData"
        ]
        Resource = "*"
        Condition = {
          StringEquals = {
            "cloudwatch:namespace" = "CloudWatchSynthetics"
          }
        }
      }
    ]
  })
}

# CloudWatch Synthetics Canary for end-to-end testing
resource "aws_synthetics_canary" "weather_app_e2e" {
  name                 = "${replace(var.name_prefix, "-", "")}e2etest" # Canary names can't contain hyphens
  artifact_s3_location = "s3://${aws_s3_bucket.synthetics_artifacts.bucket}/canary-artifacts"
  execution_role_arn   = aws_iam_role.synthetics_canary_role.arn
  handler              = "pageLoadBlueprint.handler"
  zip_file             = data.archive_file.synthetics_canary_zip.output_path
  runtime_version      = "syn-nodejs-puppeteer-6.2"

  schedule {
    expression          = "rate(5 minutes)"
    duration_in_seconds = 0
  }

  run_config {
    timeout_in_seconds = 60
    memory_in_mb       = 960
    active_tracing     = true
    environment_variables = {
      WEBSITE_URL = var.cloudfront_distribution_domain != "" ? "https://${var.cloudfront_distribution_domain}" : "https://example.com"
      API_URL     = var.api_gateway_url != "" ? var.api_gateway_url : "https://api.example.com"
    }
  }

  failure_retention_period = 30
  success_retention_period = 30

  tags = var.common_tags

  depends_on = [
    aws_iam_role_policy.synthetics_canary_execution,
    aws_iam_role_policy.synthetics_canary_policy
  ]
}

# Create the canary script zip file
data "archive_file" "synthetics_canary_zip" {
  type        = "zip"
  output_path = "${path.module}/synthetics_canary.zip"

  source {
    content = templatefile("${path.module}/synthetics_canary.js", {
      website_url = var.cloudfront_distribution_domain != "" ? "https://${var.cloudfront_distribution_domain}" : "https://example.com"
      api_url     = var.api_gateway_url != "" ? var.api_gateway_url : "https://api.example.com"
    })
    filename = "nodejs/node_modules/pageLoadBlueprint.js"
  }
}

# CloudWatch Alarm for Synthetics canary failures
resource "aws_cloudwatch_metric_alarm" "synthetics_canary_failure" {
  alarm_name          = "${var.name_prefix}-synthetics-canary-failure"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "SuccessPercent"
  namespace           = "CloudWatchSynthetics"
  period              = "300"
  statistic           = "Average"
  threshold           = "90"
  alarm_description   = "This metric monitors end-to-end test success rate"
  alarm_actions       = []
  treat_missing_data  = "breaching"

  dimensions = {
    CanaryName = aws_synthetics_canary.weather_app_e2e.name
  }

  tags = var.common_tags
}

# Cost monitoring CloudWatch dashboard
resource "aws_cloudwatch_dashboard" "cost_monitoring" {
  dashboard_name = "${var.name_prefix}-cost-dashboard"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AWS/Billing", "EstimatedCharges", "Currency", "USD"],
            ["AWS/Billing", "EstimatedCharges", "Currency", "USD", "ServiceName", "AmazonS3"],
            ["AWS/Billing", "EstimatedCharges", "Currency", "USD", "ServiceName", "AWSLambda"],
            ["AWS/Billing", "EstimatedCharges", "Currency", "USD", "ServiceName", "Amazon API Gateway"],
            ["AWS/Billing", "EstimatedCharges", "Currency", "USD", "ServiceName", "Amazon DynamoDB"],
            ["AWS/Billing", "EstimatedCharges", "Currency", "USD", "ServiceName", "Amazon CloudFront"]
          ]
          view    = "timeSeries"
          stacked = false
          region  = "us-east-1"
          title   = "Estimated Monthly Charges by Service"
          period  = 86400
          stat    = "Maximum"
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 0
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AWS/Lambda", "Invocations", "FunctionName", var.lambda_function_name],
            ["AWS/ApiGateway", "Count", "ApiName", var.api_gateway_id],
            ["AWS/DynamoDB", "ConsumedReadCapacityUnits", "TableName", var.dynamodb_table_name],
            ["AWS/DynamoDB", "ConsumedWriteCapacityUnits", "TableName", var.dynamodb_table_name]
          ]
          view    = "timeSeries"
          stacked = false
          region  = data.aws_region.current.id
          title   = "Usage Metrics (Cost Drivers)"
          period  = 3600
          stat    = "Sum"
        }
      },
      {
        type   = "text"
        x      = 0
        y      = 6
        width  = 24
        height = 3

        properties = {
          markdown = "## Cost Optimization Tips\n\n**Top 3 Cost Items with Heavy Production Load:**\n\n1. **API Gateway Requests** - Each API call incurs a cost. Consider implementing client-side caching and request batching.\n2. **Lambda Invocations & Duration** - Optimize function memory allocation and execution time. Consider provisioned concurrency for consistent workloads.\n3. **DynamoDB Read/Write Operations** - Implement efficient caching strategies and consider using DynamoDB on-demand billing for variable workloads.\n\n**Budget Alert:** Current monthly limit is $${var.budget_limit} USD with alerts at 80% ($${var.budget_limit * 0.8}) and 100% forecasted."
        }
      }
    ]
  })
}