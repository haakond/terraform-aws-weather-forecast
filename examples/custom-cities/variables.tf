# Variables for Custom Cities Example

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "weather-forecast-custom-cities"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "demo"
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
  default     = 30
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
      id      = "reykjavik"
      name    = "Reykjavik"
      country = "Iceland"
      coordinates = {
        latitude  = 64.1466
        longitude = -21.9426
      }
    },
    {
      id      = "stockholm"
      name    = "Stockholm"
      country = "Sweden"
      coordinates = {
        latitude  = 59.3293
        longitude = 18.0686
      }
    },
    {
      id      = "copenhagen"
      name    = "Copenhagen"
      country = "Denmark"
      coordinates = {
        latitude  = 55.6761
        longitude = 12.5683
      }
    },
    {
      id      = "helsinki"
      name    = "Helsinki"
      country = "Finland"
      coordinates = {
        latitude  = 60.1699
        longitude = 24.9384
      }
    },
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