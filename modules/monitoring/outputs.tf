# Monitoring Module Outputs

output "dashboard_url" {
  description = "CloudWatch dashboard URL"
  value       = "https://${data.aws_region.current.id}.console.aws.amazon.com/cloudwatch/home?region=${data.aws_region.current.id}#dashboards:name=${aws_cloudwatch_dashboard.weather_app.dashboard_name}"
}

output "dashboard_name" {
  description = "CloudWatch dashboard name"
  value       = aws_cloudwatch_dashboard.weather_app.dashboard_name
}

output "alarm_names" {
  description = "List of CloudWatch alarm names"
  value = concat([
    aws_cloudwatch_metric_alarm.lambda_error_rate.alarm_name,
    aws_cloudwatch_metric_alarm.lambda_duration.alarm_name,
    aws_cloudwatch_metric_alarm.api_gateway_5xx_errors.alarm_name,
    aws_cloudwatch_metric_alarm.api_gateway_latency.alarm_name,
    aws_cloudwatch_metric_alarm.dynamodb_throttling.alarm_name,
    aws_cloudwatch_metric_alarm.synthetics_canary_failure.alarm_name
    ],
    var.cloudwatch_log_group_name != "" ? [aws_cloudwatch_metric_alarm.weather_api_success_rate[0].alarm_name] : []
  )
}

output "budget_name" {
  description = "AWS Budget name"
  value       = aws_budgets_budget.weather_app_budget.name
}

output "budget_arn" {
  description = "AWS Budget ARN"
  value       = aws_budgets_budget.weather_app_budget.arn
}

output "cost_dashboard_url" {
  description = "Cost monitoring CloudWatch dashboard URL"
  value       = "https://${data.aws_region.current.id}.console.aws.amazon.com/cloudwatch/home?region=${data.aws_region.current.id}#dashboards:name=${aws_cloudwatch_dashboard.cost_monitoring.dashboard_name}"
}

output "cost_dashboard_name" {
  description = "Cost monitoring CloudWatch dashboard name"
  value       = aws_cloudwatch_dashboard.cost_monitoring.dashboard_name
}

# CloudWatch Synthetics outputs
output "synthetics_canary_name" {
  description = "CloudWatch Synthetics canary name"
  value       = aws_synthetics_canary.weather_app_e2e.name
}

output "synthetics_canary_arn" {
  description = "CloudWatch Synthetics canary ARN"
  value       = aws_synthetics_canary.weather_app_e2e.arn
}

output "synthetics_artifacts_bucket" {
  description = "S3 bucket for Synthetics artifacts"
  value       = aws_s3_bucket.synthetics_artifacts.bucket
}