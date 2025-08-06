# Weather Forecast App - Output Definitions

output "cloudfront_distribution_domain" {
  description = "CloudFront distribution domain name"
  value       = try(module.frontend.cloudfront_distribution_domain, null)
}

output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID"
  value       = try(module.frontend.cloudfront_distribution_id, null)
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

output "cloudwatch_dashboard_url" {
  description = "CloudWatch dashboard URL"
  value       = try(module.monitoring.dashboard_url, null)
}

output "budget_name" {
  description = "AWS Budget name for cost monitoring"
  value       = try(module.monitoring.budget_name, null)
}