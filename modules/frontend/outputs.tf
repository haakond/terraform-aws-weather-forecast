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

output "cloudfront_distribution_arn" {
  description = "CloudFront distribution ARN"
  value       = aws_cloudfront_distribution.website.arn
}

output "website_url" {
  description = "Website URL"
  value       = "https://${aws_cloudfront_distribution.website.domain_name}"
}