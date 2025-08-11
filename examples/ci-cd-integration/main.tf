# CI/CD Integration Example
# This example shows how to use the weather forecast app module in CI/CD environments

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
    awscc = {
      source  = "hashicorp/awscc"
      version = "~> 0.70"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

provider "awscc" {
  region = var.aws_region
}

# Example 1: Standard deployment with automatic frontend build
module "weather_app_with_build" {
  source = "../../"

  project_name                          = "${var.project_name}-with-build"
  environment                           = var.environment
  aws_region                            = var.aws_region
  weather_service_identification_domain = var.weather_service_identification_domain
  cities_config                         = var.cities_config
  budget_limit                          = var.budget_limit
  log_retention_days                    = var.log_retention_days
}

# Example 2: CI/CD deployment where frontend is built separately
module "weather_app_cicd" {
  source = "../../"

  project_name                          = "${var.project_name}-cicd"
  environment                           = var.environment
  aws_region                            = var.aws_region
  weather_service_identification_domain = var.weather_service_identification_domain
  cities_config                         = var.cities_config
  budget_limit                          = var.budget_limit
  log_retention_days                    = var.log_retention_days

  # Override frontend module configuration for CI/CD
  frontend_config = {
    skip_frontend_build  = true # Frontend is built in CI/CD pipeline
    frontend_source_path = "frontend"
  }
}

# Example 3: Custom frontend path (useful when frontend is in a different location)
module "weather_app_custom_path" {
  source = "../../"

  project_name                          = "${var.project_name}-custom"
  environment                           = var.environment
  aws_region                            = var.aws_region
  weather_service_identification_domain = var.weather_service_identification_domain
  cities_config                         = var.cities_config
  budget_limit                          = var.budget_limit
  log_retention_days                    = var.log_retention_days

  # Override frontend module configuration for custom path
  frontend_config = {
    frontend_source_path = "web-app/frontend" # Custom path
    skip_frontend_build  = false
  }
}