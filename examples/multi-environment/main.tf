# Multi-Environment Weather Forecast App Deployment Example
# This example shows how to deploy multiple environments (dev, staging, prod)

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

  default_tags {
    tags = {
      Project   = var.project_name
      ManagedBy = "terraform"
    }
  }
}

# Local values for environment-specific configuration
locals {
  environments = {
    dev = {
      budget_limit       = 25
      log_retention_days = 30
    }
    staging = {
      budget_limit       = 50
      log_retention_days = 90
    }
    prod = {
      budget_limit       = 100
      log_retention_days = 180
    }
  }
}

# Development Environment
module "weather_forecast_app_dev" {
  source = "../../"

  project_name       = var.project_name
  environment        = "dev"
  aws_region         = var.aws_region
  company_website    = var.company_website
  budget_limit       = local.environments.dev.budget_limit
  log_retention_days = local.environments.dev.log_retention_days
}

# Staging Environment
module "weather_forecast_app_staging" {
  source = "../../"

  project_name       = var.project_name
  environment        = "staging"
  aws_region         = var.aws_region
  company_website    = var.company_website
  budget_limit       = local.environments.staging.budget_limit
  log_retention_days = local.environments.staging.log_retention_days
}

# Production Environment
module "weather_forecast_app_prod" {
  source = "../../"

  project_name       = var.project_name
  environment        = "prod"
  aws_region         = var.aws_region
  company_website    = var.company_website
  budget_limit       = local.environments.prod.budget_limit
  log_retention_days = local.environments.prod.log_retention_days
}

# Output information for all environments
output "environments" {
  description = "Information for all deployed environments"
  value = {
    dev = {
      website_url     = "https://${module.weather_forecast_app_dev.cloudfront_distribution_domain}"
      api_url         = module.weather_forecast_app_dev.api_gateway_url
      dashboard_url   = module.weather_forecast_app_dev.cloudwatch_dashboard_url
      lambda_function = module.weather_forecast_app_dev.lambda_function_name
      budget_limit    = local.environments.dev.budget_limit
    }
    staging = {
      website_url     = "https://${module.weather_forecast_app_staging.cloudfront_distribution_domain}"
      api_url         = module.weather_forecast_app_staging.api_gateway_url
      dashboard_url   = module.weather_forecast_app_staging.cloudwatch_dashboard_url
      lambda_function = module.weather_forecast_app_staging.lambda_function_name
      budget_limit    = local.environments.staging.budget_limit
    }
    prod = {
      website_url     = "https://${module.weather_forecast_app_prod.cloudfront_distribution_domain}"
      api_url         = module.weather_forecast_app_prod.api_gateway_url
      dashboard_url   = module.weather_forecast_app_prod.cloudwatch_dashboard_url
      lambda_function = module.weather_forecast_app_prod.lambda_function_name
      budget_limit    = local.environments.prod.budget_limit
    }
  }
}

output "deployment_summary" {
  description = "Summary of all environment deployments"
  value = {
    total_environments = 3
    aws_region         = var.aws_region
    project_name       = var.project_name
    total_budget       = local.environments.dev.budget_limit + local.environments.staging.budget_limit + local.environments.prod.budget_limit
    deployment_time    = timestamp()
  }
}