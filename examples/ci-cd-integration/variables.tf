# CI/CD Integration Example Variables

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "weather-forecast-cicd"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "staging"
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "eu-west-1"
}

variable "weather_service_identification_domain" {
  description = "Domain for weather service identification"
  type        = string
  default     = "example.com"
}

variable "cities_config" {
  description = "Configuration for cities to display weather for"
  type = list(object({
    id      = string
    name    = string
    country = string
    coordinates = object({
      lat = number
      lon = number
    })
  }))
  default = [
    {
      id      = "oslo"
      name    = "Oslo"
      country = "Norway"
      coordinates = {
        lat = 59.9139
        lon = 10.7522
      }
    },
    {
      id      = "paris"
      name    = "Paris"
      country = "France"
      coordinates = {
        lat = 48.8566
        lon = 2.3522
      }
    },
    {
      id      = "london"
      name    = "London"
      country = "United Kingdom"
      coordinates = {
        lat = 51.5074
        lon = -0.1278
      }
    },
    {
      id      = "barcelona"
      name    = "Barcelona"
      country = "Spain"
      coordinates = {
        lat = 41.3851
        lon = 2.1734
      }
    }
  ]
}

variable "budget_limit" {
  description = "Budget limit for cost monitoring"
  type        = number
  default     = 50
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 180
}