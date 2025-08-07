# Weather Forecast App - Usage Examples

This directory contains examples of how to use the Weather Forecast App Terraform module in different scenarios.

## TL;DR

The Weather Forecast App is a serverless web application that displays tomorrow's weather forecast for four European cities (Oslo, Paris, London, Barcelona). It's built with AWS serverless services and deployed using Terraform.

### Quick Start

```hcl
module "weather_forecast_app" {
  source = "path/to/weather-forecast-app"

  project_name    = "my-weather-app"
  environment     = "prod"
  aws_region      = "eu-west-1"
  company_website = "mycompany.com"
  budget_limit    = 50
}
```

## Available Examples

- [**basic-deployment**](./basic-deployment/) - Simple deployment with default settings
- [**production-deployment**](./production-deployment/) - Production-ready deployment with custom configuration
- [**multi-environment**](./multi-environment/) - Deploy multiple environments (dev, staging, prod)
- [**custom-cities**](./custom-cities/) - Customize the cities displayed in weather forecasts
- [**custom-configuration**](./custom-configuration/) - Advanced configuration with custom settings

## Module Outputs

After deployment, the module provides several useful outputs:

```hcl
# Access the deployed application
output "website_url" {
  value = module.weather_forecast_app.cloudfront_distribution_domain
}

# API endpoint for direct access
output "api_url" {
  value = module.weather_forecast_app.api_gateway_url
}

# Monitoring dashboard
output "dashboard_url" {
  value = module.weather_forecast_app.cloudwatch_dashboard_url
}
```

## Prerequisites

- Terraform >= 1.0
- AWS CLI configured with appropriate permissions
- AWS account with sufficient permissions to create:
  - Lambda functions
  - API Gateway
  - DynamoDB tables
  - S3 buckets
  - CloudFront distributions
  - CloudWatch resources
  - IAM roles and policies

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
      - uses: hashicorp/setup-terraform@v2
        with:
          terraform_version: 1.5.0

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: eu-west-1

      - name: Terraform Init
        run: terraform init

      - name: Terraform Plan
        run: terraform plan

      - name: Terraform Apply
        run: terraform apply -auto-approve
```

### GitLab CI Example

```yaml
stages:
  - validate
  - plan
  - deploy

variables:
  TF_ROOT: ${CI_PROJECT_DIR}
  TF_ADDRESS: ${CI_API_V4_URL}/projects/${CI_PROJECT_ID}/terraform/state/weather-app

terraform:validate:
  stage: validate
  script:
    - terraform init
    - terraform validate
    - terraform fmt -check

terraform:plan:
  stage: plan
  script:
    - terraform init
    - terraform plan -out=plan.tfplan
  artifacts:
    paths:
      - plan.tfplan

terraform:apply:
  stage: deploy
  script:
    - terraform init
    - terraform apply plan.tfplan
  only:
    - main
```

## Environment Variables

The following environment variables can be used to configure the deployment:

| Variable | Description | Default |
|----------|-------------|---------|
| `TF_VAR_project_name` | Project name | `weather-forecast-app` |
| `TF_VAR_environment` | Environment name | `dev` |
| `TF_VAR_aws_region` | AWS region | `eu-west-1` |
| `TF_VAR_company_website` | Company website for User-Agent | `example.com` |
| `TF_VAR_budget_limit` | Monthly budget limit in USD | `50` |

## Cost Considerations

- **Lambda**: Pay per request and execution time
- **API Gateway**: Pay per API call
- **DynamoDB**: On-demand billing for read/write requests
- **S3**: Storage and request costs
- **CloudFront**: Data transfer and request costs
- **CloudWatch**: Log storage and custom metrics

Typical monthly cost for low-traffic usage: $5-15 USD

## Support

For issues and questions:
1. Check the [troubleshooting guide](../docs/troubleshooting.md)
2. Review the [architecture documentation](../docs/architecture.md)
3. Check CloudWatch logs and monitoring dashboard