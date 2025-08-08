# Variables for Terraform tests

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "test-weather-app"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "test"
}

variable "weather_service_identification_domain" {
  description = "Domain name used to identify this weather service in HTTP User-Agent headers"
  type        = string
  default     = "test.example.com"
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "eu-west-1"
}

variable "budget_limit" {
  description = "Budget limit in USD"
  type        = number
  default     = 50
}

variable "log_retention_days" {
  description = "Log retention period in days"
  type        = number
  default     = 180
}

variable "cities_config" {
  description = "Configuration for cities"
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
      id      = "oslo"
      name    = "Oslo"
      country = "Norway"
      coordinates = {
        latitude  = 59.9139
        longitude = 10.7522
      }
    }
  ]
}