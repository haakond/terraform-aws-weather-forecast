# Monitoring Module Variables

variable "name_prefix" {
  description = "Prefix for resource names"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "budget_limit" {
  description = "Monthly budget limit in USD"
  type        = number
}

variable "common_tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
}

# Backend resource identifiers for monitoring
variable "lambda_function_name" {
  description = "Lambda function name to monitor"
  type        = string
  default     = ""
}

variable "api_gateway_id" {
  description = "API Gateway ID to monitor"
  type        = string
  default     = ""
}

variable "api_gateway_stage_name" {
  description = "API Gateway stage name to monitor"
  type        = string
  default     = ""
}

variable "dynamodb_table_name" {
  description = "DynamoDB table name to monitor"
  type        = string
  default     = ""
}

variable "cloudwatch_log_group_name" {
  description = "Lambda CloudWatch log group name"
  type        = string
  default     = ""
}

variable "api_gateway_log_group_name" {
  description = "API Gateway CloudWatch log group name"
  type        = string
  default     = ""
}

# CloudWatch Synthetics variables
variable "cloudfront_distribution_domain" {
  description = "CloudFront distribution domain for end-to-end testing"
  type        = string
  default     = ""
}

variable "api_gateway_url" {
  description = "API Gateway URL for end-to-end testing"
  type        = string
  default     = ""
}