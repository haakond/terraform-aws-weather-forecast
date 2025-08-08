# Frontend Module

This module creates the infrastructure for hosting the weather forecast application frontend using AWS S3 and CloudFront.

## Resources Created

- S3 bucket for static website hosting
- CloudFront distribution for global content delivery
- Origin Access Control for secure S3 access
- Security headers policy
- Automated frontend build and deployment

## Features

- **Static Website Hosting**: S3 bucket configured for static website hosting
- **Global CDN**: CloudFront distribution for fast global content delivery
- **Security**: Origin Access Control and security headers
- **Cache Optimization**: 15-minute cache control headers for all static assets
- **Automated Build**: Builds and deploys React application automatically
- **SSL/TLS**: HTTPS redirection and secure content delivery
- **CI/CD Ready**: Robust path handling for different deployment environments

## Usage

```hcl
module "frontend" {
  source = "./modules/frontend"

  name_prefix     = "weather-app-prod"
  environment     = "production"
  api_gateway_url = module.backend.api_gateway_url
  common_tags     = local.common_tags
}
```

## CI/CD Considerations

This module is designed to work in both local development and CI/CD environments. It includes:

### Automatic Path Resolution
The module automatically searches for the frontend directory in multiple locations:
- `${path.root}/${var.frontend_source_path}` (default)
- `${path.root}/frontend`
- `frontend`
- `./frontend`

### Build Process Validation
- Checks for directory existence before attempting build
- Validates package.json and required npm scripts
- Provides detailed error messages for troubleshooting
- Falls back to standard `build` script if `build:optimized` is not available

### Skip Build Option
For CI/CD pipelines where the frontend is built separately:

```hcl
module "frontend" {
  source = "./modules/frontend"

  # ... other variables ...

  skip_frontend_build = true  # Skip the build process
}
```

### Validation Script
Use the included validation script to test your setup:

```bash
./modules/frontend/validate_frontend_build.sh
```

## Variables

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| name_prefix | Prefix for resource names | `string` | n/a | yes |
| environment | Environment name | `string` | n/a | yes |
| common_tags | Common tags to apply to all resources | `map(string)` | n/a | yes |
| api_gateway_url | API Gateway URL for the backend service | `string` | n/a | yes |
| frontend_source_path | Path to the frontend source code directory (relative to Terraform root) | `string` | `"frontend"` | no |
| skip_frontend_build | Skip the frontend build process (useful for CI/CD) | `bool` | `false` | no |
| bucket_versioning_enabled | Enable versioning for the S3 bucket | `bool` | `true` | no |
| lifecycle_rules_enabled | Enable lifecycle rules for the S3 bucket | `bool` | `true` | no |
| cloudfront_price_class | CloudFront price class | `string` | `"PriceClass_100"` | no |

## Outputs

| Name | Description |
|------|-------------|
| s3_bucket_name | Name of the S3 bucket |
| s3_bucket_arn | ARN of the S3 bucket |
| cloudfront_distribution_id | ID of the CloudFront distribution |
| cloudfront_distribution_domain | Domain name of the CloudFront distribution |
| website_url | URL of the deployed website |

## Frontend Build Process

The module automatically builds and deploys the React frontend application. The build process:

1. **Path Resolution**: Automatically finds the frontend directory
2. **Validation**: Checks for required files and directories
3. **Dependencies**: Installs npm dependencies with `npm ci`
4. **Configuration**: Creates configuration file with API endpoint
5. **Build**: Builds the React application with optimization
6. **Upload**: Uploads files to S3 with appropriate cache headers
7. **Invalidation**: Creates CloudFront invalidation for immediate updates

### Cache Control

All static assets are configured with 15-minute cache control headers (`max-age=900`) as required by the application specifications.

## Troubleshooting

### Common CI/CD Issues

1. **Frontend directory not found**
   - Ensure the frontend directory exists in your repository
   - Check the `frontend_source_path` variable
   - Use the validation script to test path resolution

2. **package.json not found**
   - Verify the frontend directory structure
   - Ensure package.json exists in the frontend directory

3. **npm build fails**
   - Check that all required dependencies are in package.json
   - Verify build scripts are properly configured
   - Consider using `skip_frontend_build = true` for external build processes

4. **Permission errors**
   - Ensure the CI/CD runner has write permissions
   - Check that npm and node are properly installed

### Debug Commands

```bash
# Validate frontend setup
./modules/frontend/validate_frontend_build.sh

# Check Terraform path resolution
terraform console
> local.frontend_path
> local.build_path

# Test npm build manually
cd frontend
npm ci
npm run build:optimized || npm run build
```

## Requirements

- Node.js and npm installed on the machine running Terraform
- Frontend source code in the specified directory
- React application with build scripts configured
- AWS CLI configured (for CloudFront invalidation)