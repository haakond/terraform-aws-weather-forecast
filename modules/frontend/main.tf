# Frontend Module - S3 and CloudFront
# This module handles the static website hosting infrastructure and frontend deployment

# Random suffix for unique bucket naming
resource "random_string" "bucket_suffix" {
  length  = 8
  special = false
  upper   = false
}

# S3 bucket for static website hosting
resource "aws_s3_bucket" "website" {
  bucket = "${var.name_prefix}-frontend-${random_string.bucket_suffix.result}"

  tags = merge(var.common_tags, {
    Name = "${var.name_prefix}-frontend-bucket"
  })
}

# S3 bucket versioning configuration
resource "aws_s3_bucket_versioning" "website" {
  bucket = aws_s3_bucket.website.id
  versioning_configuration {
    status = "Enabled"
  }
}

# S3 bucket server-side encryption configuration
resource "aws_s3_bucket_server_side_encryption_configuration" "website" {
  bucket = aws_s3_bucket.website.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = true
  }
}

# S3 bucket public access block (initially restrictive, will be modified for CloudFront)
resource "aws_s3_bucket_public_access_block" "website" {
  bucket = aws_s3_bucket.website.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# S3 bucket lifecycle configuration
resource "aws_s3_bucket_lifecycle_configuration" "website" {
  bucket = aws_s3_bucket.website.id

  rule {
    id     = "delete_old_versions"
    status = "Enabled"

    filter {
      prefix = ""
    }

    noncurrent_version_expiration {
      noncurrent_days = 30
    }

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }

  rule {
    id     = "transition_to_ia"
    status = "Enabled"

    filter {
      prefix = ""
    }

    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }

    transition {
      days          = 90
      storage_class = "GLACIER"
    }
  }
}

# Origin Access Control for CloudFront
resource "aws_cloudfront_origin_access_control" "website" {
  name                              = "${var.name_prefix}-frontend-oac"
  description                       = "Origin Access Control for ${var.name_prefix} frontend"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

# S3 bucket policy to allow CloudFront access
resource "aws_s3_bucket_policy" "website" {
  bucket = aws_s3_bucket.website.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowCloudFrontServicePrincipal"
        Effect = "Allow"
        Principal = {
          Service = "cloudfront.amazonaws.com"
        }
        Action   = "s3:GetObject"
        Resource = "${aws_s3_bucket.website.arn}/*"
        Condition = {
          StringEquals = {
            "AWS:SourceArn" = aws_cloudfront_distribution.website.arn
          }
        }
      }
    ]
  })

  depends_on = [aws_cloudfront_distribution.website]
}
# CloudFront response headers policy for security
resource "aws_cloudfront_response_headers_policy" "security_headers" {
  name    = "${var.name_prefix}-security-headers"
  comment = "Security headers policy for ${var.name_prefix}"

  security_headers_config {
    strict_transport_security {
      access_control_max_age_sec = 31536000
      include_subdomains         = true
      override                   = true
    }

    content_type_options {
      override = true
    }

    frame_options {
      frame_option = "DENY"
      override     = true
    }

    referrer_policy {
      referrer_policy = "strict-origin-when-cross-origin"
      override        = true
    }
  }

  custom_headers_config {
    items {
      header   = "X-Permitted-Cross-Domain-Policies"
      value    = "none"
      override = true
    }
  }
}

# CloudFront distribution for static website
resource "aws_cloudfront_distribution" "website" {
  origin {
    domain_name              = aws_s3_bucket.website.bucket_regional_domain_name
    origin_access_control_id = aws_cloudfront_origin_access_control.website.id
    origin_id                = "S3-${aws_s3_bucket.website.bucket}"
  }

  enabled             = true
  is_ipv6_enabled     = true
  default_root_object = "index.html"
  comment             = "${var.name_prefix} weather forecast app"

  # Cache behavior for the default path
  default_cache_behavior {
    allowed_methods        = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "S3-${aws_s3_bucket.website.bucket}"
    compress               = true
    viewer_protocol_policy = "redirect-to-https"

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }

    min_ttl     = 0
    default_ttl = 3600  # 1 hour
    max_ttl     = 86400 # 24 hours

    # Security headers
    response_headers_policy_id = aws_cloudfront_response_headers_policy.security_headers.id
  }

  # Cache behavior for static assets (CSS, JS, images)
  ordered_cache_behavior {
    path_pattern           = "/static/*"
    allowed_methods        = ["GET", "HEAD", "OPTIONS"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "S3-${aws_s3_bucket.website.bucket}"
    compress               = true
    viewer_protocol_policy = "redirect-to-https"

    forwarded_values {
      query_string = false
      headers      = ["Origin"]
      cookies {
        forward = "none"
      }
    }

    min_ttl     = 0
    default_ttl = 86400    # 24 hours
    max_ttl     = 31536000 # 1 year

    # Security headers
    response_headers_policy_id = aws_cloudfront_response_headers_policy.security_headers.id
  }

  # Geographic restrictions
  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  # SSL certificate configuration
  viewer_certificate {
    cloudfront_default_certificate = true
  }

  # Custom error pages
  custom_error_response {
    error_code         = 404
    response_code      = 200
    response_page_path = "/index.html"
  }

  custom_error_response {
    error_code         = 403
    response_code      = 200
    response_page_path = "/index.html"
  }

  tags = merge(var.common_tags, {
    Name = "${var.name_prefix}-frontend-distribution"
  })
}

# Build the React frontend application
resource "null_resource" "frontend_build" {
  # Trigger rebuild when frontend source files change
  triggers = {
    # Monitor key frontend files for changes
    package_json = filemd5("${path.root}/frontend/package.json")
    app_js       = filemd5("${path.root}/frontend/src/App.js")
    index_js     = filemd5("${path.root}/frontend/src/index.js")
    # Add a timestamp to force rebuild on terraform apply
    timestamp = timestamp()
  }

  # Build the React application
  provisioner "local-exec" {
    command = <<-EOT
      cd ${path.root}/frontend
      echo "Installing frontend dependencies..."
      npm ci --silent

      echo "Creating frontend configuration..."
      cat > public/config.js << EOF
window.APP_CONFIG = {
  API_BASE_URL: '${var.api_gateway_url}',
  ENVIRONMENT: '${var.environment}'
};
EOF

      echo "Building React application..."
      npm run build
      echo "Frontend build completed successfully"
    EOT
  }

  # Ensure the build runs before S3 upload
  depends_on = [aws_s3_bucket.website]
}

# Upload the built frontend files to S3
resource "aws_s3_object" "frontend_files" {
  # Get all files from the build directory
  for_each = fileset("${path.root}/frontend/build", "**/*")

  bucket = aws_s3_bucket.website.id
  key    = each.value
  source = "${path.root}/frontend/build/${each.value}"

  # Set appropriate content type based on file extension
  content_type = lookup({
    "html"  = "text/html"
    "css"   = "text/css"
    "js"    = "application/javascript"
    "json"  = "application/json"
    "png"   = "image/png"
    "jpg"   = "image/jpeg"
    "jpeg"  = "image/jpeg"
    "gif"   = "image/gif"
    "svg"   = "image/svg+xml"
    "ico"   = "image/x-icon"
    "woff"  = "font/woff"
    "woff2" = "font/woff2"
    "ttf"   = "font/ttf"
    "eot"   = "application/vnd.ms-fontobject"
  }, split(".", each.value)[length(split(".", each.value)) - 1], "application/octet-stream")

  # Set cache control headers
  cache_control = lookup({
    "html" = "no-cache, no-store, must-revalidate"
    "css"  = "public, max-age=31536000, immutable"
    "js"   = "public, max-age=31536000, immutable"
    "json" = "no-cache, no-store, must-revalidate"
  }, split(".", each.value)[length(split(".", each.value)) - 1], "public, max-age=86400")

  # Generate ETag for cache invalidation
  etag = filemd5("${path.root}/frontend/build/${each.value}")

  # Ensure files are uploaded after build completes
  depends_on = [null_resource.frontend_build]

  tags = merge(var.common_tags, {
    Name = "${var.name_prefix}-frontend-file-${each.value}"
  })
}

# Create CloudFront invalidation after file upload
resource "null_resource" "frontend_invalidation" {
  # Trigger invalidation when files change
  triggers = {
    # Use a hash of all uploaded files to detect changes
    files_hash = md5(join("", [for file in aws_s3_object.frontend_files : file.etag]))
  }

  provisioner "local-exec" {
    command = <<-EOT
      echo "Creating CloudFront invalidation..."
      aws cloudfront create-invalidation \
        --distribution-id ${aws_cloudfront_distribution.website.id} \
        --paths "/*" \
        --output text
      echo "CloudFront invalidation created successfully"
    EOT
  }

  depends_on = [aws_s3_object.frontend_files]
}