# Multi-Environment Deployment Example

This example demonstrates how to deploy the Weather Forecast App across multiple environments (development, staging, and production) with environment-specific configurations.

## What This Example Deploys

Three complete environments:
- **Development**: Lower budget, shorter log retention
- **Staging**: Medium budget, medium log retention  
- **Production**: Higher budget, extended log retention

Each environment includes:
- Isolated infrastructure stack
- Environment-specific resource naming
- Appropriate budget limits and monitoring
- Independent scaling and configuration

## Environment Configuration

| Environment | Budget Limit | Log Retention | Use Case |
|-------------|-------------|---------------|----------|
| Development | $25/month   | 30 days       | Feature development and testing |
| Staging     | $50/month   | 90 days       | Pre-production validation |
| Production  | $100/month  | 180 days      | Live application |

## Usage

1. **Deploy all environments**:
   ```bash
   cp -r examples/multi-environment my-multi-env-weather-app
   cd my-multi-env-weather-app
   terraform init
   terraform plan
   terraform apply
   ```

2. **Access each environment**:
   After deployment, you'll get URLs for all three environments:
   - Development: `https://dev-xyz.cloudfront.net`
   - Staging: `https://staging-xyz.cloudfront.net`
   - Production: `https://prod-xyz.cloudfront.net`

## Environment-Specific Features

### Development Environment
- **Purpose**: Feature development and initial testing
- **Budget**: $25/month (sufficient for development workloads)
- **Log Retention**: 30 days (shorter retention for cost optimization)
- **Monitoring**: Basic CloudWatch dashboards and alarms

### Staging Environment  
- **Purpose**: Pre-production testing and validation
- **Budget**: $50/month (handles moderate testing loads)
- **Log Retention**: 90 days (extended for troubleshooting)
- **Monitoring**: Enhanced monitoring for production-like testing

### Production Environment
- **Purpose**: Live application serving real users
- **Budget**: $100/month (handles production traffic)
- **Log Retention**: 180 days (compliance and audit requirements)
- **Monitoring**: Comprehensive monitoring and alerting

## Deployment Strategy

### Recommended Workflow
1. **Develop** → Deploy to development environment
2. **Test** → Promote to staging environment
3. **Validate** → Deploy to production environment

### CI/CD Integration
```yaml
# Example GitHub Actions workflow
name: Multi-Environment Deploy
on:
  push:
    branches:
      - develop    # Deploy to dev
      - staging    # Deploy to staging  
      - main       # Deploy to prod

jobs:
  deploy-dev:
    if: github.ref == 'refs/heads/develop'
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to Development
        run: |
          terraform workspace select dev || terraform workspace new dev
          terraform apply -auto-approve

  deploy-staging:
    if: github.ref == 'refs/heads/staging'
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to Staging
        run: |
          terraform workspace select staging || terraform workspace new staging
          terraform apply -auto-approve

  deploy-prod:
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to Production
        run: |
          terraform workspace select prod || terraform workspace new prod
          terraform apply -auto-approve
```

## Cost Management

### Total Monthly Budget
- **Combined Budget**: $175/month across all environments
- **Cost Allocation**:
  - Development: 14% ($25)
  - Staging: 29% ($50)  
  - Production: 57% ($100)

### Cost Optimization Tips
1. **Development**: Use for short-term testing, destroy when not needed
2. **Staging**: Schedule on/off during business hours
3. **Production**: Monitor usage patterns and optimize accordingly

## Resource Isolation

Each environment has completely isolated resources:
- Separate Lambda functions
- Independent DynamoDB tables
- Isolated S3 buckets and CloudFront distributions
- Environment-specific IAM roles
- Separate CloudWatch dashboards and alarms

## Monitoring Strategy

### Per-Environment Monitoring
- Individual CloudWatch dashboards
- Environment-specific alarms and thresholds
- Separate budget alerts
- Independent log groups

### Cross-Environment Comparison
Use the deployment outputs to compare metrics across environments:
```bash
# Get all environment URLs
terraform output environments
```

## Operational Procedures

### Environment Promotion
1. **Code Changes**: Develop in dev environment
2. **Testing**: Validate in staging environment
3. **Production**: Deploy to production after staging validation

### Troubleshooting
1. **Development Issues**: Check dev environment logs and metrics
2. **Staging Issues**: Compare with dev environment for differences
3. **Production Issues**: Use staging environment for reproduction

### Maintenance
- **Development**: Can be destroyed/recreated frequently
- **Staging**: Maintain for testing and validation
- **Production**: Requires careful change management

## Scaling Individual Environments

Each environment can be scaled independently:

```hcl
# Scale development environment
module "weather_forecast_app_dev" {
  # ... existing configuration

  # Add custom scaling parameters
  lambda_memory_size = 256  # Lower memory for dev
}

# Scale production environment  
module "weather_forecast_app_prod" {
  # ... existing configuration

  # Add custom scaling parameters
  lambda_memory_size = 1024  # Higher memory for prod
}
```

## Clean Up

### Destroy Single Environment
```bash
# Destroy only development
terraform destroy -target=module.weather_forecast_app_dev

# Destroy only staging
terraform destroy -target=module.weather_forecast_app_staging

# Destroy only production
terraform destroy -target=module.weather_forecast_app_prod
```

### Destroy All Environments
```bash
terraform destroy
```

## Next Steps

- Implement environment-specific custom domains
- Set up cross-environment monitoring dashboards
- Configure automated environment promotion pipelines
- Implement blue-green deployment for production