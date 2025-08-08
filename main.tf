# Weather Forecast App - Main Terraform Configuration
# This is the main entry point for the weather forecast application infrastructure

# Configure the AWS Provider
provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Service     = "weather-forecast-app"
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

provider "awscc" {
  region = var.aws_region
}

# Local values for common configurations
locals {
  name_prefix = "${var.project_name}-${var.environment}"

  common_tags = {
    Name        = local.name_prefix
    Service     = "weather-forecast-app"
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

# Module calls - these will be implemented in subsequent tasks
module "backend" {
  source = "./modules/backend"

  project_name                          = var.project_name
  service_name                          = "weather-forecast-app"
  environment                           = var.environment
  weather_service_identification_domain = var.weather_service_identification_domain
  cities_config                         = var.cities_config
  log_retention_days                    = var.log_retention_days
  common_tags                           = local.common_tags
}

module "frontend" {
  source = "./modules/frontend"

  name_prefix          = local.name_prefix
  environment          = var.environment
  common_tags          = local.common_tags
  api_gateway_url      = module.backend.api_gateway_url
  frontend_source_path = var.frontend_config.frontend_source_path
}

module "monitoring" {
  source = "./modules/monitoring"

  name_prefix                    = local.name_prefix
  environment                    = var.environment
  budget_limit                   = var.budget_limit
  common_tags                    = local.common_tags
  lambda_function_name           = module.backend.lambda_function_name
  api_gateway_id                 = module.backend.api_gateway_id
  api_gateway_stage_name         = module.backend.api_gateway_stage_name
  dynamodb_table_name            = module.backend.dynamodb_table_name
  cloudwatch_log_group_name      = module.backend.cloudwatch_log_group_name
  api_gateway_log_group_name     = module.backend.api_gateway_log_group_name
  cloudfront_distribution_domain = module.frontend.cloudfront_distribution_domain
  api_gateway_url                = module.backend.api_gateway_url
}