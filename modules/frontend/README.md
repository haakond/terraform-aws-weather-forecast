# Frontend Module

This module creates the infrastructure for hosting a static website using Amazon S3 and CloudFront.

## Features

- **S3 Static Website Hosting**: Secure S3 bucket with versioning and lifecycle policies
- **CloudFront CDN**: Global content delivery with caching and compression
- **Security Headers**: Comprehensive security headers policy including HSTS, frame options, and content type options
- **HTTPS Enforcement**: Automatic HTTP to HTTPS redirection
- **SPA Support**: Custom error pages for single-page application routing
- **Origin Access Control**: Secure access to S3 bucket using CloudFront OAC

## Architecture

```
Internet → CloudFront Distribution → S3 Bucket (Static Website)
```

## Resources Created

### S3 Resources
- `aws_s3_bucket.website` - Main bucket for static website hosting
- `aws_s3_bucket_versioning.website` - Enables versioning for the bucket
- `aws_s3_bucket_server_side_encryption_configuration.website` - AES256 encryption
- `aws_s3_bucket_public_access_block.website` - Blocks all public access
- `aws_s3_bucket_lifecycle_configuration.website` - Lifecycle rules for cost optimization
- `aws_s3_bucket_policy.website` - Allows CloudFront access via OAC

### CloudFront Resources
- `aws_cloudfront_origin_access_control.website` - OAC for secure S3 access
- `aws_cloudfront_response_headers_policy.security_headers` - Security headers policy
- `aws_cloudfront_distribution.website` - CDN distribution with caching rules

### Supporting Resources
- `random_string.bucket_suffix` - Ensures unique bucket naming

## Configuration

### Cache Behaviors

1. **Default Behavior** (`/*`)
   - TTL: 1 hour default, 24 hours max
   - Compression enabled
   - Security headers applied
   - HTTPS redirect

2. **Static Assets** (`/static/*`)
   - TTL: 24 hours default, 1 year max
   - Optimized for static content caching
   - Security headers applied
   - HTTPS redirect

### Security Features

- **HSTS**: 1 year max age with subdomain inclusion
- **Frame Options**: DENY to prevent clickjacking
- **Content Type Options**: Prevents MIME type sniffing
- **Referrer Policy**: Strict origin when cross-origin
- **Custom Headers**: X-Permitted-Cross-Domain-Policies set to none

### Lifecycle Management

- **Version Cleanup**: Non-current versions deleted after 30 days
- **Multipart Upload Cleanup**: Incomplete uploads cleaned after 7 days
- **Storage Transitions**:
  - Standard to Standard-IA after 30 days
  - Standard-IA to Glacier after 90 days

## Usage

```hcl
module "frontend" {
  source = "./modules/frontend"

  name_prefix = "my-app-prod"
  environment = "production"
  common_tags = {
    Service     = "my-application"
    Environment = "production"
    ManagedBy   = "terraform"
  }
}
```

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| name_prefix | Prefix for resource names | `string` | n/a | yes |
| environment | Environment name | `string` | n/a | yes |
| common_tags | Common tags to apply to all resources | `map(string)` | n/a | yes |
| bucket_versioning_enabled | Enable versioning for the S3 bucket | `bool` | `true` | no |
| lifecycle_rules_enabled | Enable lifecycle rules for the S3 bucket | `bool` | `true` | no |
| cloudfront_price_class | CloudFront price class | `string` | `"PriceClass_100"` | no |

## Outputs

| Name | Description |
|------|-------------|
| cloudfront_distribution_domain | CloudFront distribution domain name |
| cloudfront_distribution_id | CloudFront distribution ID |
| s3_bucket_name | S3 bucket name |
| s3_bucket_arn | S3 bucket ARN |
| cloudfront_distribution_arn | CloudFront distribution ARN |
| website_url | Complete website URL (https://) |

## Testing

Run the validation script to test the module:

```bash
cd tests/terraform
./validate_frontend.sh
```

Or run specific test files:

```bash
terraform test -filter=frontend_s3.tftest.hcl
terraform test -filter=frontend_cloudfront.tftest.hcl
```

## Deployment

After deploying this module, you can upload your static website files to the S3 bucket and they will be served through CloudFront with global caching and security headers.

### Upload Files

```bash
aws s3 sync ./build/ s3://$(terraform output -raw s3_bucket_name)/
```

### Invalidate Cache

```bash
aws cloudfront create-invalidation \
  --distribution-id $(terraform output -raw cloudfront_distribution_id) \
  --paths "/*"
```

## Cost Optimization

- Lifecycle rules automatically transition objects to cheaper storage classes
- CloudFront caching reduces S3 requests
- Price class can be adjusted based on global reach requirements
- Old versions are automatically cleaned up to reduce storage costs

## Security Considerations

- S3 bucket is not publicly accessible (all public access blocked)
- Access only through CloudFront using Origin Access Control
- Security headers protect against common web vulnerabilities
- HTTPS is enforced for all connections
- Server-side encryption enabled for all objects