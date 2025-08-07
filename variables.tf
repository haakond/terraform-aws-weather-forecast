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
  default     = "example.com"

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
      id      = "oslo"
      name    = "Oslo"
      country = "Norway"
      coordinates = {
        latitude  = 59.9139
        longitude = 10.7522
      }
    },
    {
      id      = "paris"
      name    = "Paris"
      country = "France"
      coordinates = {
        latitude  = 48.8566
        longitude = 2.3522
      }
    },
    {
      id      = "london"
      name    = "London"
      country = "United Kingdom"
      coordinates = {
        latitude  = 51.5074
        longitude = -0.1278
      }
    },
    {
      id      = "barcelona"
      name    = "Barcelona"
      country = "Spain"
      coordinates = {
        latitude  = 41.3851
        longitude = 2.1734
      }
    }
  ]

  validation {
    condition     = length(var.cities_config) > 0 && length(var.cities_config) <= 10
    error_message = "Cities configuration must contain between 1 and 10 cities."
  }

  validation {
    condition = alltrue([
      for city in var.cities_config :
      city.coordinates.latitude >= -90 && city.coordinates.latitude <= 90
    ])
    error_message = "All city latitudes must be between -90 and 90 degrees."
  }

  validation {
    condition = alltrue([
      for city in var.cities_config :
      city.coordinates.longitude >= -180 && city.coordinates.longitude <= 180
    ])
    error_message = "All city longitudes must be between -180 and 180 degrees."
  }

  validation {
    condition     = length(distinct([for city in var.cities_config : city.id])) == length(var.cities_config)
    error_message = "All city IDs must be unique."
  }
}