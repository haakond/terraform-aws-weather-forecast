# Basic Deployment Example

This example demonstrates the simplest way to deploy the Weather Forecast App with default settings.

## What This Example Deploys

- Weather forecast web application for 4 European cities
- Serverless backend (Lambda + API Gateway + DynamoDB)
- Static frontend (S3 + CloudFront)
- Basic monitoring and cost alerts

## Usage

1. **Clone or copy this example**:
   ```bash
   cp -r examples/basic-deployment my-weather-app
   cd my-weather-app
   ```

2. **Initialize Terraform**:
   ```bash
   terraform init
   ```

3. **Review the plan**:
   ```bash
   terraform plan
   ```

4. **Deploy the application**:
   ```bash
   terraform apply
   ```

5. **Access your application**:
   The website URL will be displayed in the output after deployment.

## Customization

You can customize the deployment by modifying the variables in `terraform.tfvars`:

```hcl
# terraform.tfvars
project_name    = "my-weather-app"
environment     = "prod"
aws_region      = "eu-central-1"
company_website = "mycompany.com"
budget_limit    = 50
```

## Expected Costs

With default settings, expect monthly costs of approximately:
- **Development usage**: $5-10 USD
- **Light production usage**: $10-25 USD

## What You Get

After deployment, you'll have:
- ✅ Weather forecast website accessible via CloudFront URL
- ✅ REST API for weather data
- ✅ Automatic caching (1-hour TTL)
- ✅ CloudWatch monitoring dashboard
- ✅ Cost monitoring and budget alerts
- ✅ High availability across multiple AZs

## Clean Up

To remove all resources:
```bash
terraform destroy
```

## Next Steps

- Check the [production deployment example](../production-deployment/) for advanced configuration
- Review the [monitoring guide](../../docs/monitoring.md) for operational insights
- See the [troubleshooting guide](../../docs/troubleshooting.md) if you encounter issues