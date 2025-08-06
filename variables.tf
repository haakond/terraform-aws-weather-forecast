# Weather Forecast App - Variable Definitions

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "weather-forecast-app"

  validation {
    condition     = can(regex("^[a-z0-9-]+$", var.project_name))
    error_message = "Project name must contain only lowercase letters, numbers, and hyphens."
  }
}

variable "environment" {
  description = "Environment name (e.g., dev, staging, prod)"
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod."
  }
}

variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "eu-west-1"

  validation {
    condition     = can(regex("^[a-z0-9-]+$", var.aws_region))
    error_message = "AWS region must be a valid region identifier."
  }
}

variable "company_website" {
  description = "Company website for User-Agent header in weather API requests"
  type        = string
  default     = "hedrange.com"

  validation {
    condition     = can(regex("^[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$", var.company_website))
    error_message = "Company website must be a valid domain name."
  }
}

variable "budget_limit" {
  description = "Monthly budget limit in USD for cost monitoring"
  type        = number
  default     = 50

  validation {
    condition     = var.budget_limit > 0
    error_message = "Budget limit must be greater than 0."
  }
}

variable "log_retention_days" {
  description = "CloudWatch log retention period in days"
  type        = number
  default     = 180

  validation {
    condition     = contains([1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653], var.log_retention_days)
    error_message = "Log retention days must be a valid CloudWatch retention period."
  }
}