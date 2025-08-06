# Backend Module Variables

variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "service_name" {
  description = "Name of the service for tagging"
  type        = string
  default     = "weather-forecast-app"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "prod"
}

variable "company_website" {
  description = "Company website for User-Agent header"
  type        = string
  default     = "hedrange.com"
}

variable "log_retention_days" {
  description = "CloudWatch log retention period in days"
  type        = number
  default     = 180
}

variable "common_tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default     = {}
}

variable "lambda_memory_size" {
  description = "Memory size for Lambda function in MB"
  type        = number
  default     = 512

  validation {
    condition     = var.lambda_memory_size >= 128 && var.lambda_memory_size <= 10240
    error_message = "Lambda memory size must be between 128 MB and 10,240 MB."
  }
}

variable "lambda_reserved_concurrency" {
  description = "Reserved concurrency for Lambda function to prevent runaway costs"
  type        = number
  default     = 10

  validation {
    condition     = var.lambda_reserved_concurrency >= -1
    error_message = "Lambda reserved concurrency must be -1 (unreserved) or a positive number."
  }
}

variable "log_level" {
  description = "Log level for Lambda function"
  type        = string
  default     = "INFO"

  validation {
    condition     = contains(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], var.log_level)
    error_message = "Log level must be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL."
  }
}

variable "vpc_config" {
  description = "VPC configuration for Lambda function (optional)"
  type = object({
    subnet_ids         = list(string)
    security_group_ids = list(string)
  })
  default = null
}

variable "dlq_target_arn" {
  description = "Dead letter queue target ARN for failed Lambda invocations"
  type        = string
  default     = null
}

# API Gateway Configuration Variables

variable "api_stage_name" {
  description = "API Gateway stage name"
  type        = string
  default     = "prod"

  validation {
    condition     = can(regex("^[a-zA-Z0-9_-]+$", var.api_stage_name))
    error_message = "API stage name must contain only alphanumeric characters, hyphens, and underscores."
  }
}

variable "api_throttling_rate_limit" {
  description = "API Gateway throttling rate limit (requests per second)"
  type        = number
  default     = 100

  validation {
    condition     = var.api_throttling_rate_limit > 0
    error_message = "API throttling rate limit must be greater than 0."
  }
}

variable "api_throttling_burst_limit" {
  description = "API Gateway throttling burst limit"
  type        = number
  default     = 200

  validation {
    condition     = var.api_throttling_burst_limit > 0
    error_message = "API throttling burst limit must be greater than 0."
  }
}

variable "api_quota_limit" {
  description = "API Gateway daily quota limit"
  type        = number
  default     = 10000

  validation {
    condition     = var.api_quota_limit > 0
    error_message = "API quota limit must be greater than 0."
  }
}