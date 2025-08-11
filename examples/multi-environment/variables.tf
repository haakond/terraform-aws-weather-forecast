# Variables for Multi-Environment Deployment Example

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "weather-forecast-app"
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