# Variables for Custom Configuration Deployment Example

# Standard variables
variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "weather-forecast-app"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "custom"
}

variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "eu-west-1"
}

variable "company_website" {
  description = "Company website for User-Agent header"
  type        = string
  default     = "mycompany.com"
}

variable "cities_config" {
  description = "Configuration for cities to display weather forecasts"
  type = list(object({
    id      = string
    name    = string
    country = string
    coordinates = object({
      latitude  = number
      longitude = number
    })
  }))
  default = [
    {
      id      = "tokyo"
      name    = "Tokyo"
      country = "Japan"
      coordinates = {
        latitude  = 35.6762
        longitude = 139.6503
      }
    },
    {
      id      = "new-york"
      name    = "New York"
      country = "United States"
      coordinates = {
        latitude  = 40.7128
        longitude = -74.0060
      }
    },
    {
      id      = "sydney"
      name    = "Sydney"
      country = "Australia"
      coordinates = {
        latitude  = -33.8688
        longitude = 151.2093
      }
    },
    {
      id      = "cape-town"
      name    = "Cape Town"
      country = "South Africa"
      coordinates = {
        latitude  = -33.9249
        longitude = 18.4241
      }
    }
  ]
}

variable "budget_limit" {
  description = "Monthly budget limit in USD"
  type        = number
  default     = 75
}

variable "log_retention_days" {
  description = "CloudWatch log retention period in days"
  type        = number
  default     = 90
}

# Custom configuration variables
variable "owner" {
  description = "Owner of the resources"
  type        = string
  default     = "Platform Team"
}

variable "cost_center" {
  description = "Cost center for billing"
  type        = string
  default     = "Engineering"
}

variable "compliance_level" {
  description = "Compliance level (basic, enhanced, strict)"
  type        = string
  default     = "enhanced"

  validation {
    condition     = contains(["basic", "enhanced", "strict"], var.compliance_level)
    error_message = "Compliance level must be one of: basic, enhanced, strict."
  }
}

# Custom domain configuration
variable "custom_domain" {
  description = "Custom domain name for the application (optional)"
  type        = string
  default     = ""
}

# VPC configuration
variable "use_custom_vpc" {
  description = "Use custom VPC for enhanced security"
  type        = bool
  default     = false
}

variable "vpc_cidr" {
  description = "CIDR block for custom VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

# Security configuration
variable "enable_log_encryption" {
  description = "Enable KMS encryption for CloudWatch logs"
  type        = bool
  default     = false
}

# Advanced Lambda configuration
variable "lambda_memory_size" {
  description = "Memory size for Lambda function in MB"
  type        = number
  default     = 512
}

variable "lambda_timeout" {
  description = "Timeout for Lambda function in seconds"
  type        = number
  default     = 30
}

variable "lambda_reserved_concurrency" {
  description = "Reserved concurrency for Lambda function"
  type        = number
  default     = 10
}

# API Gateway configuration
variable "api_throttling_rate_limit" {
  description = "API Gateway throttling rate limit (requests per second)"
  type        = number
  default     = 100
}

variable "api_throttling_burst_limit" {
  description = "API Gateway throttling burst limit"
  type        = number
  default     = 200
}

# CloudFront configuration
variable "cloudfront_price_class" {
  description = "CloudFront price class"
  type        = string
  default     = "PriceClass_100"
}