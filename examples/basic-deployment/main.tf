# Basic Weather Forecast App Deployment Example
# This example shows the simplest way to deploy the weather forecast application

terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

# Configure the AWS Provider
provider "aws" {
  region = var.aws_region
}

# Deploy the weather forecast app with minimal configuration
module "weather_forecast_app" {
  source = "../../" # Path to the root module

  project_name    = var.project_name
  environment     = var.environment
  aws_region      = var.aws_region
  company_website = var.company_website
  budget_limit    = var.budget_limit
}

# Output the important URLs and information
output "website_url" {
  description = "Weather forecast application URL"
  value       = "https://${module.weather_forecast_app.cloudfront_distribution_domain}"
}

output "api_gateway_url" {
  description = "API Gateway endpoint URL"
  value       = module.weather_forecast_app.api_gateway_url
}

output "cloudwatch_dashboard_url" {
  description = "CloudWatch monitoring dashboard URL"
  value       = module.weather_forecast_app.cloudwatch_dashboard_url
}

output "deployment_summary" {
  description = "Summary of deployed resources"
  value = {
    website_url          = "https://${module.weather_forecast_app.cloudfront_distribution_domain}"
    api_url              = module.weather_forecast_app.api_gateway_url
    lambda_function      = module.weather_forecast_app.lambda_function_name
    dynamodb_table       = module.weather_forecast_app.dynamodb_table_name
    s3_bucket            = module.weather_forecast_app.s3_bucket_name
    cloudfront_id        = module.weather_forecast_app.cloudfront_distribution_id
    monitoring_dashboard = module.weather_forecast_app.cloudwatch_dashboard_url
    budget_name          = module.weather_forecast_app.budget_name
  }
}