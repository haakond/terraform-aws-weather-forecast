# Variables for Production Deployment Example

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "weather-forecast-app"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "prod"
}

variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "eu-west-1"
}

variable "weather_service_identification_domain" {
  description = "Domain name used to identify this weather service in HTTP User-Agent headers when making requests to the Norwegian Meteorological Institute API"
  type        = string
  default     = "mycompany.com"
}

variable "budget_limit" {
  description = "Monthly budget limit in USD for production"
  type        = number
  default     = 100
}

variable "log_retention_days" {
  description = "CloudWatch log retention period in days"
  type        = number
  default     = 180
}

variable "owner" {
  description = "Owner of the resources"
  type        = string
  default     = "DevOps Team"
}

variable "cost_center" {
  description = "Cost center for billing"
  type        = string
  default     = "Engineering"
}

variable "alert_email" {
  description = "Email address for production alerts (optional)"
  type        = string
  default     = ""
}