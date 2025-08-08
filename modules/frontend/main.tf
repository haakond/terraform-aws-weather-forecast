# Frontend Module - S3 and CloudFront
# This module handles the static website hosting infrastructure and frontend deployment

# Local values for path resolution
locals {
  # Try to find the correct frontend path
  possible_frontend_paths = [
    "${path.root}/${var.frontend_source_path}",
    "${path.root}/frontend",
    "frontend",
    "./frontend"
  ]

  # Find the first path that contains package.json
  frontend_path = try(
    [for p in local.possible_frontend_paths : p if fileexists("${p}/package.json")][0],
    var.frontend_source_path
  )

  # Build directory path
  build_path = "${local.frontend_path}/build"
}

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

  # Cache behavior for the default path (HTML files)
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

    # 15-minute caching for HTML files
    min_ttl     = 0
    default_ttl = 900 # 15 minutes
    max_ttl     = 900 # 15 minutes

    # Security headers
    response_headers_policy_id = aws_cloudfront_response_headers_policy.security_headers.id
  }

  # Cache behavior for static assets (CSS, JS, images) - 15-minute caching
  ordered_cache_behavior {
    path_pattern           = "/static/*"
    allowed_methods        = ["GET", "HEAD", "OPTIONS"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "S3-${aws_s3_bucket.website.bucket}"
    compress               = true
    viewer_protocol_policy = "redirect-to-https"

    forwarded_values {
      query_string = false
      headers      = ["Cache-Control"] # Forward Cache-Control headers from S3
      cookies {
        forward = "none"
      }
    }

    # 15-minute caching for static assets
    min_ttl     = 0
    default_ttl = 900 # 15 minutes
    max_ttl     = 900 # 15 minutes

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
    # Monitor key frontend files for changes (use resolved path)
    package_json = try(filemd5("${local.frontend_path}/package.json"), "missing")
    app_js       = try(filemd5("${local.frontend_path}/src/App.js"), "missing")
    index_js     = try(filemd5("${local.frontend_path}/src/index.js"), "missing")
    # Add a timestamp to force rebuild on terraform apply
    timestamp = timestamp()
  }

  # Build the React application with improved path handling for CI/CD
  provisioner "local-exec" {
    command = <<-EOT
      set -e  # Exit on any error

      # Use the resolved frontend path
      FRONTEND_PATH="${local.frontend_path}"

      echo "Using frontend directory: $FRONTEND_PATH"
      echo "Current working directory: $(pwd)"

      # Check if frontend directory exists
      if [ ! -d "$FRONTEND_PATH" ]; then
        echo "ERROR: Frontend directory not found at: $FRONTEND_PATH"
        echo "Available directories in current location:"
        ls -la . || echo "Cannot list current directory"
        if [ -d "${path.root}" ]; then
          echo "Available directories in root:"
          ls -la "${path.root}" || echo "Cannot list root directory"
        fi
        exit 1
      fi

      # Check if package.json exists
      if [ ! -f "$FRONTEND_PATH/package.json" ]; then
        echo "ERROR: package.json not found in $FRONTEND_PATH"
        echo "Contents of frontend directory:"
        ls -la "$FRONTEND_PATH" || echo "Cannot list frontend directory"
        exit 1
      fi

      # Change to frontend directory
      cd "$FRONTEND_PATH"
      echo "Changed to directory: $(pwd)"

      # Install dependencies
      echo "Installing frontend dependencies..."
      npm ci --silent

      # Ensure public directory exists
      mkdir -p public

      # Create frontend configuration
      echo "Creating frontend configuration..."
      cat > public/config.js << EOF
window.APP_CONFIG = {
  API_BASE_URL: '${var.api_gateway_url}',
  ENVIRONMENT: '${var.environment}'
};
EOF

      # Check if build script exists
      if ! npm run --silent 2>/dev/null | grep -q "build:optimized"; then
        echo "WARNING: build:optimized script not found, using standard build"
        npm run build
      else
        echo "Building React application with cache optimization..."
        npm run build:optimized
      fi

      echo "Frontend build completed successfully"

      # Verify build directory was created
      if [ ! -d "build" ]; then
        echo "ERROR: Build directory was not created"
        exit 1
      fi

      echo "Build directory contents:"
      ls -la build/ || echo "Cannot list build directory"
    EOT
  }

  # Ensure the build runs before S3 upload
  depends_on = [aws_s3_bucket.website]
}

# Upload the built frontend files to S3
resource "aws_s3_object" "frontend_files" {
  # Get all files from the resolved build directory
  for_each = try(fileset(local.build_path, "**/*"), toset([]))

  bucket = aws_s3_bucket.website.id
  key    = each.value
  source = "${local.build_path}/${each.value}"

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

  # Set cache control headers for 15-minute caching (900 seconds)
  cache_control = lookup({
    # HTML files should have short cache to allow quick updates
    "html" = "public, max-age=900, must-revalidate"
    # CSS and JS files with hashes can be cached longer but respect 15-minute requirement for consistency
    "css" = "public, max-age=900"
    "js"  = "public, max-age=900"
    # JSON config files should have short cache
    "json" = "public, max-age=900, must-revalidate"
    # Images and other assets
    "png"  = "public, max-age=900"
    "jpg"  = "public, max-age=900"
    "jpeg" = "public, max-age=900"
    "gif"  = "public, max-age=900"
    "svg"  = "public, max-age=900"
    "ico"  = "public, max-age=900"
    # Font files
    "woff"  = "public, max-age=900"
    "woff2" = "public, max-age=900"
    "ttf"   = "public, max-age=900"
    "eot"   = "public, max-age=900"
  }, split(".", each.value)[length(split(".", each.value)) - 1], "public, max-age=900")

  # Generate ETag for cache invalidation
  etag = try(filemd5("${local.build_path}/${each.value}"), "missing")

  # Ensure files are uploaded after build completes
  depends_on = [
    aws_s3_bucket.website,
    null_resource.frontend_build
  ]

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