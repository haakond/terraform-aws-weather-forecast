# CI/CD Usage Guide

## Using the Weather Forecast Module in CI/CD Pipelines

When using this Terraform module as a submodule in CI/CD environments, the frontend build process automatically handles path resolution and common npm issues.

### Common CI/CD Issues and Solutions

#### 1. npm Lock File Synchronization Issues

**Error:** `npm ci can only install packages when your package.json and package-lock.json are in sync`

**Solution:** The module automatically detects this issue and:
1. Attempts `npm ci` first (preferred for CI/CD)
2. Falls back to cleaning and regenerating lock files if sync issues are detected
3. Uses `npm install` to create a fresh `package-lock.json`

#### 2. TypeScript Version Conflicts

**Error:** `Invalid: lock file's typescript@5.9.2 does not satisfy typescript@4.9.5`

**Solution:** The module handles version conflicts by:
1. Detecting version mismatch errors
2. Cleaning npm cache and node_modules
3. Reinstalling dependencies with compatible versions

#### 3. Frontend Directory Not Found

**Error:** `Frontend directory not found at: frontend`

**Solution:** The module searches multiple locations automatically:
1. User-specified path from Terraform root
2. Default frontend directory at root
3. Module-relative paths (for submodule usage)
4. Common CI/CD locations in `.terraform/modules/`

### Path Resolution

The module automatically searches for the frontend directory in the following order:

1. `${path.root}/${var.frontend_source_path}` - User-specified path from Terraform root
2. `${path.root}/frontend` - Default frontend directory at root
3. `${path.module}/${var.frontend_source_path}` - User-specified path from module location
4. `${path.module}/frontend` - Default frontend directory in module
5. `${path.module}/../frontend` - Frontend one level up from module
6. `${path.module}/../../frontend` - Frontend two levels up from module
7. `frontend` - Relative to current working directory
8. `./frontend` - Explicit relative path

### Build Process and File Upload

The module implements a robust build-to-upload pipeline:

1. **Frontend Build** (`null_resource.frontend_build`)
   - Installs dependencies and builds the React application
   - Includes comprehensive error handling for npm issues
   - Verifies build output and essential files

2. **Build Verification** (`null_resource.build_verification`)
   - Waits for build stability (5 seconds total)
   - Verifies critical files exist (index.html, etc.)
   - Counts and validates build output
   - Ensures files are ready for S3 upload

3. **S3 File Upload** (`aws_s3_object.frontend_files`)
   - Depends on build verification completion
   - Uploads all files from the build directory
   - Sets appropriate content types and cache headers

#### Build Verification Process

```bash
# The module automatically performs these checks:
echo "=== Build Verification for S3 Upload ==="
# Wait for build stability
sleep 3
# Verify build directory exists
# Verify index.html exists
# Count files and ensure content exists
# Additional stability wait
sleep 2
echo "✓ Build verification completed - files ready for S3 upload"
```

### Testing the Build Process

Use the included test script to verify the build process locally:

```bash
# Test the frontend build process
./scripts/test-frontend-build.sh
```

This script simulates the exact build process used by Terraform and helps identify issues before deployment.

### Pre-Deployment Validation

Use the included validation script to check for issues before deployment:

```bash
# Run frontend validation
./scripts/validate-frontend.sh
```

This script checks for:
- Frontend directory location
- Node.js and npm versions
- package.json validity
- Lock file synchronization
- Required dependencies
- Build script availability

### CI/CD Configuration Examples

#### GitHub Actions

```yaml
name: Deploy Weather Forecast App
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v2
        with:
          terraform_version: 1.5.0

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
          cache: 'npm'
          cache-dependency-path: '**/package-lock.json'

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: eu-west-1

      - name: Validate Frontend (Optional)
        run: ./scripts/validate-frontend.sh

      - name: Terraform Init
        run: terraform init

      - name: Terraform Plan
        run: terraform plan -var-file="environments/prod.tfvars"

      - name: Terraform Apply
        run: terraform apply -auto-approve -var-file="environments/prod.tfvars"
```

#### GitLab CI

```yaml
stages:
  - validate
  - deploy

variables:
  NODE_VERSION: "18"

validate:
  stage: validate
  image: node:${NODE_VERSION}
  script:
    - ./scripts/validate-frontend.sh
  only:
    - main

deploy:
  stage: deploy
  image: hashicorp/terraform:1.5.0
  before_script:
    - apk add --no-cache nodejs npm
    - terraform init
  script:
    - terraform plan -var-file="environments/prod.tfvars"
    - terraform apply -auto-approve -var-file="environments/prod.tfvars"
  only:
    - main
```

#### Jenkins Pipeline

```groovy
pipeline {
    agent any

    tools {
        nodejs '18'
        terraform '1.5.0'
    }

    stages {
        stage('Validate Frontend') {
            steps {
                sh './scripts/validate-frontend.sh'
            }
        }

        stage('Deploy') {
            steps {
                sh 'terraform init'
                sh 'terraform plan -var-file="environments/prod.tfvars"'
                sh 'terraform apply -auto-approve -var-file="environments/prod.tfvars"'
            }
        }
    }
}
```

### Module Usage in Parent Repository

```hcl
module "weather_forecast_app" {
  source = "git::https://github.com/your-org/terraform-aws-weather-forecast.git?ref=v1.0.0"

  project_name = "my-weather-app"
  environment  = "production"
  aws_region   = "eu-west-1"

  # The module will automatically find the frontend directory
  # No need to specify frontend_source_path unless using a custom location
}
```

### Advanced Configuration

#### Custom Frontend Path

```hcl
module "weather_forecast_app" {
  source = "git::https://github.com/your-org/terraform-aws-weather-forecast.git?ref=v1.0.0"

  project_name = "my-weather-app"
  environment  = "production"
  aws_region   = "eu-west-1"

  frontend_config = {
    frontend_source_path = "custom/frontend/path"
  }
}
```

#### Environment-Specific Configuration

```hcl
# environments/prod.tfvars
project_name = "weather-app-prod"
environment  = "production"
aws_region   = "eu-west-1"

frontend_config = {
  frontend_source_path = "frontend"
}

budget_limit = 100
log_retention_days = 365
```

### Troubleshooting

#### Common Issues and Solutions

1. **npm ci fails with sync error**
   - The module automatically handles this by regenerating lock files
   - Manual fix: `rm -rf node_modules package-lock.json && npm install`

2. **TypeScript version conflicts**
   - The module cleans and reinstalls dependencies
   - Manual fix: `npm cache clean --force && rm -rf node_modules && npm install`

3. **Frontend directory not found**
   - Check the debug output in Terraform logs
   - Verify the frontend directory contains `package.json`
   - Use the validation script: `./scripts/validate-frontend.sh`

4. **Node.js version compatibility**
   - Ensure Node.js 16+ is available in CI environment
   - Use specific Node.js versions in CI configuration

#### Debug Output

The build process includes comprehensive debugging information:

```
=== Frontend Build Debug Information ===
Resolved frontend path: /path/to/frontend
Current working directory: /runner/work/project
Terraform path.root: /runner/work/project
Terraform path.module: /runner/work/project/.terraform/modules/weather_forecast
Frontend source path variable: frontend

=== Installing frontend dependencies ===
Node.js version: v18.17.0
npm version: 9.6.7
✓ npm ci completed successfully
✓ Frontend dependencies installed and verified successfully

=== Build Verification for S3 Upload ===
Verifying build at: /path/to/frontend/build
Build contains 42 files
✓ Build verification completed - files ready for S3 upload
```

#### Debugging Build and Upload Issues

**1. Check Terraform Outputs**
```bash
# After deployment, check build information
terraform output frontend_build_file_count
terraform output frontend_build_path
```

**2. Build Process Issues**
- **Build directory not created**: Check Node.js version and build script
- **No files in build**: Verify React build process completed successfully
- **index.html missing**: Check for build errors in the logs

**3. S3 Upload Issues**
- **Files not uploaded**: Verify build verification completed successfully
- **Partial upload**: Check for file permission issues or large file timeouts
- **Wrong content types**: Verify file extensions are recognized

**4. Timing Issues**
The module includes built-in delays:
- 5 seconds after build completion
- 3 seconds for build stability check
- 2 seconds final stability wait

If you still experience timing issues, the delays can be increased by modifying the sleep commands in the build verification script.

#### Emergency Recovery

If all automated fixes fail, the module includes an emergency clean install function:

1. Cleans npm cache completely
2. Removes all node_modules and lock files
3. Performs fresh `npm install`
4. Verifies critical dependencies are present

### Best Practices

1. **Use specific Node.js versions** in CI/CD configurations
2. **Cache node_modules** when possible to speed up builds
3. **Run validation script** before deployment in CI/CD pipelines
4. **Monitor build logs** for early detection of dependency issues
5. **Keep dependencies updated** to avoid version conflicts

### Performance Optimization

- **Enable npm caching** in CI/CD environments
- **Use `npm ci`** for faster, reliable installs in CI
- **Minimize dependency updates** during production deployments
- **Pre-validate frontend** in separate CI stage

This comprehensive approach ensures reliable frontend builds across different CI/CD environments and handles the most common npm-related issues automatically.
