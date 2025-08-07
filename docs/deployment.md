# Deployment Guide

## TL;DR

```bash
# Quick deployment
git clone <repository>
cd terraform-aws-weather-forecast
terraform init
terraform apply -var="project_name=my-weather-app"
```

## Prerequisites

### Required Tools
- **Terraform** >= 1.0 ([Installation Guide](https://learn.hashicorp.com/tutorials/terraform/install-cli))
- **AWS CLI** >= 2.0 ([Installation Guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html))
- **Python** 3.13+ with pyenv ([Installation Guide](https://github.com/pyenv/pyenv#installation))
- **Node.js** >= 18 (for frontend development) ([Installation Guide](https://nodejs.org/))
- **Git** for version control

### AWS Permissions

Your AWS credentials need the following permissions:
- **Lambda**: Create and manage functions
- **API Gateway**: Create and manage REST APIs
- **DynamoDB**: Create and manage tables
- **S3**: Create and manage buckets
- **CloudFront**: Create and manage distributions
- **CloudWatch**: Create dashboards and alarms
- **IAM**: Create roles and policies
- **AWS Budgets**: Create budget alerts

### AWS CLI Configuration

Configure AWS CLI with your credentials:
```bash
# Option 1: AWS SSO (Recommended)
aws configure sso

# Option 2: Access Keys
aws configure

# Option 3: Environment Variables
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_DEFAULT_REGION="eu-west-1"
```

Verify your configuration:
```bash
aws sts get-caller-identity
```

## Deployment Steps

### Step 1: Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd terraform-aws-weather-forecast

# Set up Python virtual environment
pyenv install 3.13.3
pyenv virtualenv 3.13.3 weather-forecast-app
pyenv local weather-forecast-app

# Install Python dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install
```

### Step 2: Configure Variables

Create a `terraform.tfvars` file:
```hcl
# terraform.tfvars
project_name    = "my-weather-app"
environment     = "dev"
aws_region      = "eu-west-1"
company_website = "mycompany.com"
budget_limit    = 50
```

### Step 3: Initialize Terraform

```bash
# Initialize Terraform
terraform init

# Validate configuration
terraform validate

# Format code
terraform fmt
```

### Step 4: Plan Deployment

```bash
# Review what will be created
terraform plan

# Save plan for review
terraform plan -out=tfplan
```

### Step 5: Deploy Infrastructure

```bash
# Apply the configuration
terraform apply

# Or apply saved plan
terraform apply tfplan
```

### Step 6: Verify Deployment

After deployment, Terraform will output important URLs:
```bash
# Test the application
curl -f $(terraform output -raw cloudfront_distribution_domain)

# Test the API health endpoint
curl -f $(terraform output -raw api_gateway_url)/health

# View monitoring dashboard
echo "Dashboard: $(terraform output -raw cloudwatch_dashboard_url)"
```

## Environment Configuration

### Development Environment

Create `environments/dev.tfvars`:
```hcl
project_name     = "weather-app-dev"
environment      = "dev"
aws_region       = "eu-west-1"
company_website  = "mycompany.com"
budget_limit     = 25
log_retention_days = 30
```

Deploy:
```bash
terraform workspace new dev
terraform workspace select dev
terraform plan -var-file="environments/dev.tfvars"
terraform apply -var-file="environments/dev.tfvars"
```

### Staging Environment

Create `environments/staging.tfvars`:
```hcl
project_name     = "weather-app-staging"
environment      = "staging"
aws_region       = "eu-west-1"
company_website  = "mycompany.com"
budget_limit     = 50
log_retention_days = 90
```

Deploy:
```bash
terraform workspace new staging
terraform workspace select staging
terraform plan -var-file="environments/staging.tfvars"
terraform apply -var-file="environments/staging.tfvars"
```

### Production Environment

Create `environments/prod.tfvars`:
```hcl
project_name     = "weather-app-prod"
environment      = "prod"
aws_region       = "eu-west-1"
company_website  = "mycompany.com"
budget_limit     = 100
log_retention_days = 180
```

Deploy:
```bash
terraform workspace new prod
terraform workspace select prod
terraform plan -var-file="environments/prod.tfvars"
terraform apply -var-file="environments/prod.tfvars"
```

## Advanced Deployment Options

### Multi-Region Deployment

Deploy to multiple regions for disaster recovery:

```bash
# Primary region (eu-west-1)
terraform apply -var="aws_region=eu-west-1" -var="project_name=weather-app-primary"

# Secondary region (eu-central-1)
terraform apply -var="aws_region=eu-central-1" -var="project_name=weather-app-secondary"
```

### Custom Domain Configuration

To use a custom domain:

1. **Register domain** in Route 53 or external provider
2. **Create SSL certificate** in AWS Certificate Manager
3. **Configure CloudFront** with custom domain

```hcl
# Add to terraform.tfvars
custom_domain_name = "weather.mycompany.com"
certificate_arn    = "arn:aws:acm:us-east-1:123456789012:certificate/12345678-1234-1234-1234-123456789012"
```

### Blue-Green Deployment

For zero-downtime deployments:

```bash
# Deploy to blue environment
terraform workspace select blue
terraform apply -var="environment=blue"

# Test blue environment
curl -f $(terraform output -raw cloudfront_distribution_domain)

# Switch traffic to blue (update DNS)
# Deploy to green environment
terraform workspace select green
terraform apply -var="environment=green"
```

## Testing Deployment

### Automated Tests

Run the complete test suite:
```bash
# Run all tests
make test

# Run specific test types
make test-python    # Python unit tests
make test-tf        # Terraform tests
make test-integration # Integration tests
```

### Manual Testing

1. **Frontend Test**:
   ```bash
   # Visit the CloudFront URL
   open "https://$(terraform output -raw cloudfront_distribution_domain)"
   ```

2. **API Test**:
   ```bash
   # Test health endpoint
   curl $(terraform output -raw api_gateway_url)/health

   # Test weather endpoint
   curl $(terraform output -raw api_gateway_url)/weather
   ```

3. **Monitoring Test**:
   ```bash
   # Check CloudWatch dashboard
   open "$(terraform output -raw cloudwatch_dashboard_url)"
   ```

## Post-Deployment Tasks

### 1. Configure Monitoring

- Set up SNS notifications for critical alarms
- Configure additional CloudWatch dashboards
- Set up log aggregation and analysis

### 2. Security Hardening

- Review IAM permissions and apply least privilege
- Enable AWS Config for compliance monitoring
- Set up AWS Security Hub for security findings

### 3. Performance Optimization

- Monitor Lambda cold starts and optimize memory
- Review API Gateway caching settings
- Optimize DynamoDB read/write patterns

### 4. Backup and Recovery

- Verify DynamoDB point-in-time recovery is enabled
- Test disaster recovery procedures
- Document recovery time objectives (RTO) and recovery point objectives (RPO)

## Updating Deployment

### Application Updates

```bash
# Update application code
git pull origin main

# Plan and apply changes
terraform plan
terraform apply
```

### Infrastructure Updates

```bash
# Update Terraform providers
terraform init -upgrade

# Review and apply provider updates
terraform plan
terraform apply
```

### Dependency Updates

```bash
# Update Python dependencies
pip install -r requirements.txt --upgrade
pip freeze > requirements.txt

# Update Node.js dependencies (if applicable)
npm update

# Update Terraform modules
terraform get -update
```

## Rollback Procedures

### Application Rollback

```bash
# Rollback to previous version
git checkout <previous-commit>
terraform apply

# Or use Terraform state
terraform apply -target=module.backend -var-file=previous.tfvars
```

### Infrastructure Rollback

```bash
# Rollback using Terraform state
terraform state pull > backup.tfstate
terraform apply -var-file=previous.tfvars

# Or restore from backup
terraform state push backup.tfstate
```

## Clean Up

### Remove Single Environment

```bash
# Select environment
terraform workspace select dev

# Destroy resources
terraform destroy -var-file="environments/dev.tfvars"

# Delete workspace
terraform workspace select default
terraform workspace delete dev
```

### Complete Cleanup

```bash
# Destroy all environments
for env in dev staging prod; do
  terraform workspace select $env
  terraform destroy -var-file="environments/${env}.tfvars"
  terraform workspace select default
  terraform workspace delete $env
done

# Clean up local files
rm -rf .terraform
rm terraform.tfstate*
rm tfplan
```

## Troubleshooting

### Common Issues

#### 1. Terraform Init Fails
```bash
# Clear Terraform cache
rm -rf .terraform
terraform init
```

#### 2. AWS Permissions Error
```bash
# Verify AWS credentials
aws sts get-caller-identity

# Check required permissions
aws iam simulate-principal-policy \
  --policy-source-arn $(aws sts get-caller-identity --query Arn --output text) \
  --action-names lambda:CreateFunction \
  --resource-arns "*"
```

#### 3. Resource Already Exists
```bash
# Import existing resource
terraform import aws_s3_bucket.example bucket-name

# Or use different resource names
terraform apply -var="project_name=unique-name"
```

#### 4. Lambda Deployment Package Too Large
```bash
# Check package size
du -sh lambda_deployment.zip

# Optimize dependencies
pip install --target ./package -r requirements.txt --no-deps
```

### Getting Help

1. **Check logs**: Review CloudWatch logs for detailed error messages
2. **Terraform debug**: Run with `TF_LOG=DEBUG terraform apply`
3. **AWS support**: Create support case for AWS-specific issues
4. **Community**: Check GitHub issues and discussions

For more troubleshooting information, see [troubleshooting.md](troubleshooting.md).

---

**Next Steps**: After successful deployment, review the [operational runbooks](operational-runbooks.md) for ongoing maintenance procedures.