# Variables for Basic Deployment Example

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "weather-forecast-app"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
}

variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "eu-west-1"
}

variable "company_website" {
  description = "Company website for User-Agent header"
  type        = string
  default     = "example.com"
}

variable "budget_limit" {
  description = "Monthly budget limit in USD"
  type        = number
  default     = 25
}