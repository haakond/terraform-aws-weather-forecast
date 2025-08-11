# Frontend Module Outputs

output "cloudfront_distribution_domain" {
  description = "CloudFront distribution domain name"
  value       = aws_cloudfront_distribution.website.domain_name
}

output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID"
  value       = aws_cloudfront_distribution.website.id
}

output "s3_bucket_name" {
  description = "S3 bucket name"
  value       = aws_s3_bucket.website.bucket
}

output "s3_bucket_arn" {
  description = "S3 bucket ARN"
  value       = aws_s3_bucket.website.arn
}

output "frontend_build_file_count" {
  description = "Number of files in the frontend build directory (check build logs for actual count)"
  value       = "See upload logs for file count"
}

output "frontend_build_path" {
  description = "Path to the frontend build directory"
  value       = local.build_path
}

output "cloudfront_distribution_arn" {
  description = "CloudFront distribution ARN"
  value       = aws_cloudfront_distribution.website.arn
}

output "website_url" {
  description = "Website URL"
  value       = "https://${aws_cloudfront_distribution.website.domain_name}"
}

output "cloudfront_price_class" {
  description = "CloudFront price class used for cost optimization"
  value       = var.cloudfront_price_class
}