# Weather Forecast App - Output Definitions

output "cloudfront_distribution_domain" {
  description = "CloudFront distribution domain name"
  value       = try(module.frontend.cloudfront_distribution_domain, null)
}

output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID"
  value       = try(module.frontend.cloudfront_distribution_id, null)
}

output "cloudfront_price_class" {
  description = "CloudFront price class used for cost optimization"
  value       = try(module.frontend.cloudfront_price_class, null)
}

output "api_gateway_url" {
  description = "API Gateway endpoint URL"
  value       = try(module.backend.api_gateway_url, null)
}

output "lambda_function_name" {
  description = "Lambda function name"
  value       = try(module.backend.lambda_function_name, null)
}

output "dynamodb_table_name" {
  description = "DynamoDB table name for weather data caching"
  value       = try(module.backend.dynamodb_table_name, null)
}

output "s3_bucket_name" {
  description = "S3 bucket name for static website hosting"
  value       = try(module.frontend.s3_bucket_name, null)
}

output "s3_bucket_arn" {
  description = "S3 bucket ARN for static website hosting"
  value       = try(module.frontend.s3_bucket_arn, null)
}

output "website_url" {
  description = "Website URL"
  value       = try(module.frontend.website_url, null)
}

output "cloudwatch_dashboard_url" {
  description = "CloudWatch dashboard URL"
  value       = try(module.monitoring.dashboard_url, null)
}

output "budget_name" {
  description = "AWS Budget name for cost monitoring"
  value       = try(module.monitoring.budget_name, null)
}

output "cost_dashboard_url" {
  description = "Cost monitoring CloudWatch dashboard URL"
  value       = try(module.monitoring.cost_dashboard_url, null)
}

output "monitoring_alarm_names" {
  description = "List of CloudWatch alarm names for monitoring"
  value       = try(module.monitoring.alarm_names, [])
}

output "synthetics_canary_name" {
  description = "CloudWatch Synthetics canary name for end-to-end testing"
  value       = try(module.monitoring.synthetics_canary_name, null)
}

output "synthetics_canary_arn" {
  description = "CloudWatch Synthetics canary ARN"
  value       = try(module.monitoring.synthetics_canary_arn, null)
}