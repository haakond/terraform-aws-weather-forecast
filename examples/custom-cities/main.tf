# Custom Cities Weather Forecast App Example
# This example shows how to customize the cities displayed in the weather forecast

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
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

# Deploy the weather forecast app with custom cities
module "weather_forecast_app" {
  source = "../../"

  project_name                          = var.project_name
  environment                           = var.environment
  aws_region                            = var.aws_region
  weather_service_identification_domain = var.weather_service_identification_domain
  cities_config                         = var.cities_config
  budget_limit                          = var.budget_limit
}

# Outputs
output "website_url" {
  description = "Weather forecast website URL"
  value       = "https://${module.weather_forecast_app.cloudfront_distribution_domain}"
}

output "api_url" {
  description = "Weather API endpoint URL"
  value       = module.weather_forecast_app.api_gateway_url
}

output "configured_cities" {
  description = "List of cities configured for weather forecasts"
  value = [
    for city in var.cities_config : {
      id      = city.id
      name    = city.name
      country = city.country
    }
  ]
}

output "deployment_info" {
  description = "Deployment information"
  value = {
    project_name    = var.project_name
    environment     = var.environment
    aws_region      = var.aws_region
    cities_count    = length(var.cities_config)
    deployment_time = timestamp()
  }
}