# CI/CD Integration Example

This example demonstrates how to deploy the weather forecast application in CI/CD environments with different configuration options to resolve common deployment path issues.

## Overview

The weather forecast application can be deployed in various CI/CD scenarios:

1. **Standard deployment** - Terraform builds the frontend automatically
2. **CI/CD deployment** - Frontend is built separately in the CI/CD pipeline
3. **Custom path deployment** - Frontend source is in a non-standard location

## Common CI/CD Issues Addressed

This example specifically addresses the following CI/CD deployment issues:

- **Path resolution problems**: Frontend directory not found at expected location
- **Working directory differences**: CI/CD environments have different directory structures
- **Build process failures**: npm commands fail due to missing directories or files
- **Permission issues**: CI/CD runners lack proper permissions for build processes

## Usage

### Standard Deployment

```bash
terraform init
terraform plan -var="project_name=my-weather-app"
terraform apply
```

### CI/CD Deployment (Recommended for CI/CD)

For environments where the frontend is built as part of the CI/CD pipeline:

```bash
# Build frontend separately in CI/CD
cd ../../frontend
npm ci
npm run build:optimized

# Deploy with skip_frontend_build = true
cd ../examples/ci-cd-integration
terraform apply -var="project_name=my-weather-app" -target="module.weather_app_cicd"
```

### Custom Path Deployment

For projects where the frontend is in a different directory:

```bash
terraform apply -var="project_name=my-weather-app" -target="module.weather_app_custom_path"
```

## Configuration Options

### Frontend Configuration

The `frontend_config` variable allows customization of the frontend deployment:

```hcl
frontend_config = {
  frontend_source_path = "path/to/frontend"  # Path to frontend directory
  skip_frontend_build  = false               # Whether to skip the build process
}
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `project_name` | Name of the project | `weather-forecast-cicd` |
| `environment` | Environment name | `staging` |
| `aws_region` | AWS region | `eu-west-1` |

## CI/CD Pipeline Integration

### GitHub Actions Example

```yaml
name: Deploy Weather App

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Build Frontend
        run: |
          cd frontend
          npm ci
          npm run build:optimized

      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v2

      - name: Deploy Infrastructure
        run: |
          terraform init
          terraform apply -auto-approve \
            -var="frontend_config={skip_frontend_build=true,frontend_source_path=\"frontend\"}"
```

### GitLab CI Example

```yaml
stages:
  - build
  - deploy

build-frontend:
  stage: build
  image: node:18
  script:
    - cd frontend
    - npm ci
    - npm run build:optimized
  artifacts:
    paths:
      - frontend/build/

deploy-infrastructure:
  stage: deploy
  image: hashicorp/terraform:latest
  script:
    - terraform init
    - terraform apply -auto-approve
      -var="frontend_config={skip_frontend_build=true,frontend_source_path=\"frontend\"}"
  dependencies:
    - build-frontend
```

### Azure DevOps Example

```yaml
trigger:
- main

pool:
  vmImage: 'ubuntu-latest'

stages:
- stage: Build
  jobs:
  - job: BuildFrontend
    steps:
    - task: NodeTool@0
      inputs:
        versionSpec: '18.x'
    - script: |
        cd frontend
        npm ci
        npm run build:optimized
      displayName: 'Build Frontend'
    - task: PublishBuildArtifacts@1
      inputs:
        pathToPublish: 'frontend/build'
        artifactName: 'frontend-build'

- stage: Deploy
  jobs:
  - job: DeployInfrastructure
    steps:
    - task: TerraformInstaller@0
      inputs:
        terraformVersion: 'latest'
    - script: |
        terraform init
        terraform apply -auto-approve \
          -var="frontend_config={skip_frontend_build=true,frontend_source_path=\"frontend\"}"
      displayName: 'Deploy Infrastructure'
```

## Troubleshooting

### Common Issues and Solutions

1. **Frontend build fails in CI/CD**
   ```bash
   # Solution: Skip the build in Terraform
   frontend_config = {
     skip_frontend_build = true
   }
   ```

2. **Path not found errors**
   ```bash
   # Solution: Use validation script to find correct path
   ./modules/frontend/validate_frontend_build.sh

   # Or specify custom path
   frontend_config = {
     frontend_source_path = "path/to/your/frontend"
   }
   ```

3. **Permission errors**
   ```bash
   # Ensure CI/CD runner has proper permissions
   chmod +x scripts/*

   # Check AWS credentials
   aws sts get-caller-identity
   ```

4. **npm command not found**
   ```bash
   # Install Node.js in CI/CD pipeline
   # GitHub Actions
   - uses: actions/setup-node@v3
     with:
       node-version: '18'

   # GitLab CI
   image: node:18

   # Azure DevOps
   - task: NodeTool@0
     inputs:
       versionSpec: '18.x'
   ```

### Debug Commands

```bash
# Validate frontend setup
./modules/frontend/validate_frontend_build.sh

# Test Terraform configuration
terraform validate
terraform plan

# Check current working directory and files
pwd
ls -la
ls -la frontend/ || echo "Frontend directory not found"

# Test npm commands
cd frontend && npm run 2>&1 | grep build

# Check AWS credentials
aws sts get-caller-identity
```

### Error Messages and Solutions

| Error Message | Solution |
|---------------|----------|
| `cd: can't cd to ./frontend` | Set correct `frontend_source_path` or use `skip_frontend_build = true` |
| `cannot create public/config.js: Directory nonexistent` | Ensure frontend directory exists and has proper structure |
| `npm error path .../package.json` | Verify package.json exists in the correct location |
| `npm error code ENOENT` | Install Node.js and npm in CI/CD environment |

## Best Practices for CI/CD

1. **Always validate frontend setup first**:
   ```bash
   ./modules/frontend/validate_frontend_build.sh
   ```

2. **Use separate build and deploy stages**:
   - Build frontend in dedicated CI/CD stage
   - Set `skip_frontend_build = true` in Terraform

3. **Handle different environments**:
   ```hcl
   frontend_config = {
     skip_frontend_build = var.environment == "production" ? true : false
   }
   ```

4. **Cache dependencies**:
   ```yaml
   # GitHub Actions
   - uses: actions/cache@v3
     with:
       path: ~/.npm
       key: ${{ runner.os }}-node-${{ hashFiles('**/package-lock.json') }}
   ```

5. **Use artifacts for build outputs**:
   - Store build artifacts between CI/CD stages
   - Ensure build directory is available for Terraform