# Custom Configuration Weather Forecast App Deployment Example
# This example shows advanced customization options for the weather forecast application

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
      Owner       = var.owner
      CostCenter  = var.cost_center
      Compliance  = var.compliance_level
      ManagedBy   = "terraform"
    }
  }
}

# Deploy the weather forecast app with custom configuration
module "weather_forecast_app" {
  source = "../../"

  project_name                          = var.project_name
  environment                           = var.environment
  aws_region                            = var.aws_region
  weather_service_identification_domain = var.weather_service_identification_domain
  cities_config                         = var.cities_config
  budget_limit                          = var.budget_limit
  log_retention_days                    = var.log_retention_days
}

# Custom VPC for enhanced security (optional)
resource "aws_vpc" "custom" {
  count = var.use_custom_vpc ? 1 : 0

  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name        = "${var.project_name}-${var.environment}-vpc"
    Service     = "weather-forecast-app"
    Environment = var.environment
  }
}

# Private subnets for Lambda functions (if using custom VPC)
resource "aws_subnet" "private" {
  count = var.use_custom_vpc ? length(var.private_subnet_cidrs) : 0

  vpc_id            = aws_vpc.custom[0].id
  cidr_block        = var.private_subnet_cidrs[count.index]
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = {
    Name        = "${var.project_name}-${var.environment}-private-${count.index + 1}"
    Service     = "weather-forecast-app"
    Environment = var.environment
    Type        = "private"
  }
}

# Custom security group for Lambda functions
resource "aws_security_group" "lambda_custom" {
  count = var.use_custom_vpc ? 1 : 0

  name_prefix = "${var.project_name}-${var.environment}-lambda-"
  vpc_id      = aws_vpc.custom[0].id
  description = "Security group for Weather Forecast App Lambda functions"

  # Outbound HTTPS for weather API calls
  egress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTPS outbound for weather API"
  }

  # Outbound HTTP for potential redirects
  egress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTP outbound for redirects"
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-lambda-sg"
    Service     = "weather-forecast-app"
    Environment = var.environment
  }
}

# Custom CloudWatch log group with KMS encryption
resource "aws_kms_key" "logs" {
  count = var.enable_log_encryption ? 1 : 0

  description             = "KMS key for Weather Forecast App log encryption"
  deletion_window_in_days = 7

  tags = {
    Name        = "${var.project_name}-${var.environment}-logs-key"
    Service     = "weather-forecast-app"
    Environment = var.environment
  }
}

resource "aws_kms_alias" "logs" {
  count = var.enable_log_encryption ? 1 : 0

  name          = "alias/${var.project_name}-${var.environment}-logs"
  target_key_id = aws_kms_key.logs[0].key_id
}

# Custom Route 53 hosted zone (if using custom domain)
resource "aws_route53_zone" "custom" {
  count = var.custom_domain != "" ? 1 : 0

  name = var.custom_domain

  tags = {
    Name        = "${var.project_name}-${var.environment}-zone"
    Service     = "weather-forecast-app"
    Environment = var.environment
  }
}

# ACM certificate for custom domain
resource "aws_acm_certificate" "custom" {
  count = var.custom_domain != "" ? 1 : 0

  domain_name       = var.custom_domain
  validation_method = "DNS"

  subject_alternative_names = [
    "www.${var.custom_domain}"
  ]

  lifecycle {
    create_before_destroy = true
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-cert"
    Service     = "weather-forecast-app"
    Environment = var.environment
  }
}

# Data sources
data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_caller_identity" "current" {}

data "aws_region" "current" {}

# Outputs with custom configuration information
output "deployment_info" {
  description = "Custom deployment configuration information"
  value = {
    # Standard outputs
    website_url              = "https://${module.weather_forecast_app.cloudfront_distribution_domain}"
    api_url                  = module.weather_forecast_app.api_gateway_url
    cloudwatch_dashboard_url = module.weather_forecast_app.cloudwatch_dashboard_url

    # Custom configuration outputs
    custom_domain         = var.custom_domain
    use_custom_vpc        = var.use_custom_vpc
    enable_log_encryption = var.enable_log_encryption
    compliance_level      = var.compliance_level

    # Resource identifiers
    lambda_function_name = module.weather_forecast_app.lambda_function_name
    dynamodb_table_name  = module.weather_forecast_app.dynamodb_table_name
    s3_bucket_name       = module.weather_forecast_app.s3_bucket_name

    # Custom resources (if created)
    vpc_id          = var.use_custom_vpc ? aws_vpc.custom[0].id : null
    kms_key_id      = var.enable_log_encryption ? aws_kms_key.logs[0].id : null
    route53_zone_id = var.custom_domain != "" ? aws_route53_zone.custom[0].zone_id : null

    # Operational info
    aws_region      = var.aws_region
    environment     = var.environment
    deployment_time = timestamp()
  }
}

output "custom_domain_setup" {
  description = "Custom domain setup instructions"
  value = var.custom_domain != "" ? {
    domain_name        = var.custom_domain
    certificate_arn    = aws_acm_certificate.custom[0].arn
    zone_id            = aws_route53_zone.custom[0].zone_id
    nameservers        = aws_route53_zone.custom[0].name_servers
    setup_instructions = "Update your domain registrar to use the provided nameservers"
  } : null
}

output "security_configuration" {
  description = "Security configuration details"
  value = {
    log_encryption_enabled = var.enable_log_encryption
    kms_key_arn            = var.enable_log_encryption ? aws_kms_key.logs[0].arn : null
    custom_vpc_enabled     = var.use_custom_vpc
    vpc_id                 = var.use_custom_vpc ? aws_vpc.custom[0].id : null
    compliance_level       = var.compliance_level
  }
}