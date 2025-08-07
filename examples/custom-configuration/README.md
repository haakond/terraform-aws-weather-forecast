# Custom Configuration Example

This example demonstrates advanced customization options for the Weather Forecast App, including custom domains, VPC configuration, enhanced security, and compliance features.

## Advanced Features

- ✅ Custom domain name with Route 53 and ACM certificate
- ✅ Custom VPC with private subnets for enhanced security
- ✅ KMS encryption for CloudWatch logs
- ✅ Enhanced compliance and security configurations
- ✅ Advanced Lambda and API Gateway settings
- ✅ Custom tagging strategy for governance
- ✅ Flexible CloudFront price class selection

## Configuration Options

### Security Levels

| Level | Features | Use Case |
|-------|----------|----------|
| **Basic** | Standard AWS security | Development and testing |
| **Enhanced** | KMS encryption, custom VPC | Staging and production |
| **Strict** | Full compliance, audit logging | Regulated industries |

### Custom Cities Configuration

Customize the cities displayed in the weather forecast:
```hcl
cities_config = [
  {
    id      = "tokyo"
    name    = "Tokyo"
    country = "Japan"
    coordinates = {
      latitude  = 35.6762
      longitude = 139.6503
    }
  },
  {
    id      = "new-york"
    name    = "New York"
    country = "United States"
    coordinates = {
      latitude  = 40.7128
      longitude = -74.0060
    }
  }
  # Add more cities as needed (up to 10 cities supported)
]
```

Features:
- Support for 1-10 cities
- Precise GPS coordinates required
- Unique city IDs for caching
- Automatic validation of coordinates

### Custom Domain Setup

Enable custom domain by setting:
```hcl
custom_domain = "weather.mycompany.com"
```

This creates:
- Route 53 hosted zone
- ACM SSL certificate
- CloudFront custom domain configuration

### VPC Configuration

Enable custom VPC for enhanced security:
```hcl
use_custom_vpc = true
vpc_cidr = "10.0.0.0/16"
private_subnet_cidrs = ["10.0.1.0/24", "10.0.2.0/24"]
```

Benefits:
- Lambda functions in private subnets
- Custom security groups
- Network-level isolation
- Enhanced monitoring and logging

## Usage

1. **Configure your customizations**:
   Create a `terraform.tfvars` file:
   ```hcl
   # Basic configuration
   project_name    = "weather-forecast-app"
   environment     = "custom"
   aws_region      = "eu-west-1"
   company_website = "mycompany.com"

   # Custom domain
   custom_domain = "weather.mycompany.com"

   # Enhanced security
   use_custom_vpc        = true
   enable_log_encryption = true
   compliance_level      = "enhanced"

   # Performance tuning
   lambda_memory_size           = 1024
   lambda_reserved_concurrency  = 20
   api_throttling_rate_limit    = 200
   cloudfront_price_class       = "PriceClass_200"

   # Governance
   owner       = "Platform Team"
   cost_center = "Engineering"
   ```

2. **Deploy with custom configuration**:
   ```bash
   cp -r examples/custom-configuration my-custom-weather-app
   cd my-custom-weather-app
   terraform init
   terraform plan
   terraform apply
   ```

## Custom Domain Setup Process

1. **Deploy the infrastructure**:
   ```bash
   terraform apply
   ```

2. **Update your domain registrar**:
   Use the nameservers from the output:
   ```bash
   terraform output custom_domain_setup
   ```

3. **Verify certificate validation**:
   The ACM certificate will be automatically validated via DNS.

4. **Access your custom domain**:
   Your application will be available at `https://weather.mycompany.com`

## Security Enhancements

### KMS Encryption
When `enable_log_encryption = true`:
- CloudWatch logs encrypted with customer-managed KMS key
- Key rotation enabled automatically
- Separate key per environment

### Custom VPC Benefits
- **Network Isolation**: Lambda functions in private subnets
- **Security Groups**: Fine-grained network access control
- **VPC Flow Logs**: Network traffic monitoring
- **NAT Gateway**: Secure outbound internet access

### Compliance Features
- **Enhanced Tagging**: Comprehensive resource tagging
- **Audit Logging**: Detailed CloudTrail integration
- **Access Controls**: Least privilege IAM policies
- **Encryption**: Data encrypted in transit and at rest

## Performance Tuning

### Lambda Optimization
```hcl
lambda_memory_size          = 1024  # Higher memory for better performance
lambda_reserved_concurrency = 20    # Prevent cold starts
```

### API Gateway Tuning
```hcl
api_throttling_rate_limit  = 200  # Higher rate limit
api_throttling_burst_limit = 400  # Handle traffic spikes
```

### CloudFront Optimization
```hcl
cloudfront_price_class = "PriceClass_200"  # Better global performance
```

## Cost Implications

### Custom Domain
- **Route 53 Hosted Zone**: $0.50/month
- **ACM Certificate**: Free
- **Additional DNS queries**: ~$0.40/million queries

### Custom VPC
- **NAT Gateway**: ~$45/month per AZ
- **VPC Endpoints**: ~$7/month per endpoint
- **Data Processing**: $0.045/GB

### KMS Encryption
- **Key Usage**: $1/month per key
- **API Requests**: $0.03/10,000 requests

### Enhanced Performance
- **Higher Lambda Memory**: Proportional cost increase
- **Reserved Concurrency**: No additional cost
- **CloudFront Price Class 200**: ~20% cost increase

## Monitoring and Compliance

### Enhanced Monitoring
- Custom CloudWatch dashboards
- Detailed performance metrics
- Security event monitoring
- Cost optimization insights

### Compliance Reporting
- Resource inventory with tags
- Security configuration reports
- Access audit trails
- Cost allocation reports

## Operational Procedures

### Custom Domain Management
1. **Certificate Renewal**: Automatic via ACM
2. **DNS Changes**: Update Route 53 records
3. **Domain Transfer**: Update nameservers

### VPC Management
1. **Security Group Updates**: Modify access rules
2. **Subnet Management**: Add/remove subnets as needed
3. **NAT Gateway**: Monitor costs and usage

### Security Operations
1. **Key Rotation**: Automatic KMS key rotation
2. **Access Reviews**: Regular IAM policy audits
3. **Compliance Checks**: Automated security scanning

## Troubleshooting

### Custom Domain Issues
```bash
# Check certificate status
aws acm describe-certificate --certificate-arn <cert-arn>

# Verify DNS propagation
dig weather.mycompany.com

# Check CloudFront distribution
aws cloudfront get-distribution --id <distribution-id>
```

### VPC Connectivity Issues
```bash
# Check VPC configuration
aws ec2 describe-vpcs --vpc-ids <vpc-id>

# Verify security groups
aws ec2 describe-security-groups --group-ids <sg-id>

# Test Lambda connectivity
aws lambda invoke --function-name <function-name> test-output.json
```

### Performance Issues
```bash
# Monitor Lambda metrics
aws logs filter-log-events --log-group-name <log-group>

# Check API Gateway metrics
aws apigateway get-usage --usage-plan-id <plan-id>

# Analyze CloudFront performance
aws cloudfront get-distribution-config --id <distribution-id>
```

## Clean Up

```bash
# Remove custom domain first (if configured)
terraform destroy -target=aws_route53_zone.custom
terraform destroy -target=aws_acm_certificate.custom

# Then destroy remaining resources
terraform destroy
```

## Next Steps

- Implement WAF for additional security
- Set up cross-region disaster recovery
- Configure advanced monitoring with X-Ray
- Implement blue-green deployment strategy
- Set up automated security scanning