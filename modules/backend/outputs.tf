# Backend Module Outputs

output "api_gateway_url" {
  description = "API Gateway endpoint URL"
  value       = "https://${aws_api_gateway_rest_api.weather_api.id}.execute-api.${data.aws_region.current.id}.amazonaws.com/${aws_api_gateway_stage.weather_api.stage_name}"
}

output "lambda_function_name" {
  description = "Lambda function name"
  value       = aws_lambda_function.weather_api.function_name
}

output "dynamodb_table_name" {
  description = "DynamoDB table name for weather cache"
  value       = aws_dynamodb_table.weather_cache.name
}

output "dynamodb_table_arn" {
  description = "DynamoDB table ARN for weather cache"
  value       = aws_dynamodb_table.weather_cache.arn
}

output "lambda_role_arn" {
  description = "IAM role ARN for Lambda function"
  value       = aws_iam_role.lambda_dynamodb_role.arn
}

output "lambda_function_arn" {
  description = "Lambda function ARN"
  value       = aws_lambda_function.weather_api.arn
}

output "lambda_function_invoke_arn" {
  description = "Lambda function invoke ARN for API Gateway integration"
  value       = aws_lambda_function.weather_api.invoke_arn
}

output "lambda_alias_arn" {
  description = "Lambda function alias ARN"
  value       = aws_lambda_alias.weather_api_live.arn
}

output "lambda_alias_invoke_arn" {
  description = "Lambda function alias invoke ARN for API Gateway integration"
  value       = aws_lambda_alias.weather_api_live.invoke_arn
}

output "cloudwatch_log_group_name" {
  description = "CloudWatch log group name for Lambda function"
  value       = aws_cloudwatch_log_group.lambda_logs.name
}

output "cloudwatch_log_group_arn" {
  description = "CloudWatch log group ARN for Lambda function"
  value       = aws_cloudwatch_log_group.lambda_logs.arn
}

# API Gateway Outputs

output "api_gateway_id" {
  description = "API Gateway REST API ID"
  value       = aws_api_gateway_rest_api.weather_api.id
}

output "api_gateway_arn" {
  description = "API Gateway REST API ARN"
  value       = aws_api_gateway_rest_api.weather_api.arn
}

output "api_gateway_execution_arn" {
  description = "API Gateway execution ARN"
  value       = aws_api_gateway_rest_api.weather_api.execution_arn
}

output "api_gateway_stage_name" {
  description = "API Gateway stage name"
  value       = aws_api_gateway_stage.weather_api.stage_name
}

output "api_gateway_weather_endpoint" {
  description = "API Gateway weather endpoint URL"
  value       = "https://${aws_api_gateway_rest_api.weather_api.id}.execute-api.${data.aws_region.current.id}.amazonaws.com/${aws_api_gateway_stage.weather_api.stage_name}/weather"
}

output "api_gateway_health_endpoint" {
  description = "API Gateway health endpoint URL"
  value       = "https://${aws_api_gateway_rest_api.weather_api.id}.execute-api.${data.aws_region.current.id}.amazonaws.com/${aws_api_gateway_stage.weather_api.stage_name}/health"
}

output "api_gateway_log_group_name" {
  description = "API Gateway CloudWatch log group name"
  value       = aws_cloudwatch_log_group.api_gateway_logs.name
}

output "api_gateway_log_group_arn" {
  description = "API Gateway CloudWatch log group ARN"
  value       = aws_cloudwatch_log_group.api_gateway_logs.arn
}

output "api_gateway_usage_plan_id" {
  description = "API Gateway usage plan ID"
  value       = aws_api_gateway_usage_plan.weather_api.id
}