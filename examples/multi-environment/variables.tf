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

variable "company_website" {
  description = "Company website for User-Agent header"
  type        = string
  default     = "mycompany.com"
}