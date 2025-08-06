# Examples

This directory contains examples of how to use the weather forecast Terraform module in different scenarios.

## Basic Usage

### Simple Deployment
```hcl
module "weather_forecast" {
  source = "path/to/weather-forecast-module"

  project_name     = "my-weather-app"
  environment      = "prod"
  aws_region       = "eu-west-1"
  company_website  = "example.com"
}
```

### Custom Configuration
```hcl
module "weather_forecast" {
  source = "path/to/weather-forecast-module"

  project_name        = "weather-forecast"
  environment         = "prod"
  aws_region          = "eu-central-1"
  company_website     = "mycompany.com"
  budget_limit        = 100
  log_retention_days  = 365
}
```

## CI/CD Integration

### GitHub Actions Example
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

      - name: Terraform Init
        run: terraform init

      - name: Terraform Plan
        run: terraform plan -var-file="environments/prod.tfvars"

      - name: Terraform Apply
        run: terraform apply -auto-approve -var-file="environments/prod.tfvars"
```

### AWS CodePipeline Example
```hcl
resource "aws_codepipeline" "weather_forecast_pipeline" {
  name     = "weather-forecast-pipeline"
  role_arn = aws_iam_role.codepipeline_role.arn

  artifact_store {
    location = aws_s3_bucket.codepipeline_artifacts.bucket
    type     = "S3"
  }

  stage {
    name = "Source"
    action {
      name             = "Source"
      category         = "Source"
      owner            = "AWS"
      provider         = "S3"
      version          = "1"
      output_artifacts = ["source_output"]
    }
  }

  stage {
    name = "Deploy"
    action {
      name            = "Deploy"
      category        = "Deploy"
      owner           = "AWS"
      provider        = "CloudFormation"
      version         = "1"
      input_artifacts = ["source_output"]
    }
  }
}
```

## Environment-Specific Configurations

### Development Environment
```hcl
# environments/dev.tfvars
project_name    = "weather-forecast-dev"
environment     = "dev"
aws_region      = "eu-west-1"
budget_limit    = 25
```

### Production Environment
```hcl
# environments/prod.tfvars
project_name       = "weather-forecast-prod"
environment        = "prod"
aws_region         = "eu-west-1"
budget_limit       = 100
log_retention_days = 365
```

## Multi-Region Deployment

For multi-region deployments, create separate Terraform configurations for each region:

```hcl
# eu-west-1 deployment
module "weather_forecast_ireland" {
  source = "path/to/weather-forecast-module"

  project_name = "weather-forecast-ireland"
  environment  = "prod"
  aws_region   = "eu-west-1"
}

# eu-central-1 deployment
module "weather_forecast_frankfurt" {
  source = "path/to/weather-forecast-module"

  project_name = "weather-forecast-frankfurt"
  environment  = "prod"
  aws_region   = "eu-central-1"
}
```