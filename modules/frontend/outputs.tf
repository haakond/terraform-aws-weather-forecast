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
  description = "Number of files in the frontend build directory"
  value       = length(split("\n", trimspace(try(data.local_file.build_file_list.content, ""))))
}

output "frontend_build_path" {
  description = "Path to the frontend build directory"
  value       = local.build_path
}

output "frontend_file_list_path" {
  description = "Path to the generated file list for debugging"
  value       = "${local.build_path}/.terraform-file-list.txt"
}

output "cloudfront_distribution_arn" {
  description = "CloudFront distribution ARN"
  value       = aws_cloudfront_distribution.website.arn
}

output "website_url" {
  description = "Website URL"
  value       = "https://${aws_cloudfront_distribution.website.domain_name}"
}