# Production Weather Forecast App Deployment Example
# This example shows a production-ready deployment with enhanced configuration

terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

# Configure the AWS Provider with additional tags
provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      Owner       = var.owner
      CostCenter  = var.cost_center
      ManagedBy   = "terraform"
    }
  }
}

# Deploy the weather forecast app with production configuration
module "weather_forecast_app" {
  source = "../../" # Path to the root module

  project_name       = var.project_name
  environment        = var.environment
  aws_region         = var.aws_region
  company_website    = var.company_website
  budget_limit       = var.budget_limit
  log_retention_days = var.log_retention_days
}

# Additional monitoring for production
resource "aws_cloudwatch_metric_alarm" "high_api_usage" {
  alarm_name          = "${var.project_name}-${var.environment}-high-api-usage"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "Count"
  namespace           = "AWS/ApiGateway"
  period              = "300"
  statistic           = "Sum"
  threshold           = "1000"
  alarm_description   = "This metric monitors high API usage"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    ApiName = "${var.project_name}-${var.environment}-weather-api"
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-high-api-usage"
    Service     = "weather-forecast-app"
    Environment = var.environment
  }
}

# SNS topic for production alerts
resource "aws_sns_topic" "alerts" {
  name = "${var.project_name}-${var.environment}-alerts"

  tags = {
    Name        = "${var.project_name}-${var.environment}-alerts"
    Service     = "weather-forecast-app"
    Environment = var.environment
  }
}

# Email subscription for alerts (optional)
resource "aws_sns_topic_subscription" "email_alerts" {
  count     = var.alert_email != "" ? 1 : 0
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

# Output comprehensive deployment information
output "deployment_info" {
  description = "Complete deployment information for production"
  value = {
    # Application URLs
    website_url = "https://${module.weather_forecast_app.cloudfront_distribution_domain}"
    api_url     = module.weather_forecast_app.api_gateway_url

    # Resource identifiers
    lambda_function_name       = module.weather_forecast_app.lambda_function_name
    dynamodb_table_name        = module.weather_forecast_app.dynamodb_table_name
    s3_bucket_name             = module.weather_forecast_app.s3_bucket_name
    cloudfront_distribution_id = module.weather_forecast_app.cloudfront_distribution_id

    # Monitoring
    cloudwatch_dashboard_url = module.weather_forecast_app.cloudwatch_dashboard_url
    cost_dashboard_url       = module.weather_forecast_app.cost_dashboard_url
    budget_name              = module.weather_forecast_app.budget_name
    alert_topic_arn          = aws_sns_topic.alerts.arn

    # Operational
    environment     = var.environment
    aws_region      = var.aws_region
    deployment_time = timestamp()
  }
}

output "website_url" {
  description = "Weather forecast application URL"
  value       = "https://${module.weather_forecast_app.cloudfront_distribution_domain}"
}

output "monitoring_urls" {
  description = "Monitoring and operational URLs"
  value = {
    cloudwatch_dashboard = module.weather_forecast_app.cloudwatch_dashboard_url
    cost_dashboard       = module.weather_forecast_app.cost_dashboard_url
    api_gateway_console  = "https://console.aws.amazon.com/apigateway/home?region=${var.aws_region}#/apis"
    lambda_console       = "https://console.aws.amazon.com/lambda/home?region=${var.aws_region}#/functions"
    cloudfront_console   = "https://console.aws.amazon.com/cloudfront/v3/home#/distributions"
  }
}