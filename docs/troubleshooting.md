# Troubleshooting Guide

## TL;DR

**Quick Diagnostics:**
```bash
# Check application health
curl -f $(terraform output -raw cloudfront_distribution_domain)
curl -f $(terraform output -raw api_gateway_url)/health

# Check AWS resources
aws lambda get-function --function-name $(terraform output -raw lambda_function_name)
aws dynamodb describe-table --table-name $(terraform output -raw dynamodb_table_name)
```

## Common Issues

### Deployment Issues

#### Issue: Terraform Init Fails
**Symptoms:**
- `terraform init` command fails
- Provider download errors
- Lock file conflicts

**Solutions:**
```bash
# Clear Terraform cache and reinitialize
rm -rf .terraform .terraform.lock.hcl
terraform init

# Force provider reinstallation
terraform init -upgrade

# Fix lock file conflicts
terraform providers lock -platform=darwin_arm64 -platform=linux_amd64
```

#### Issue: AWS Permissions Denied
**Symptoms:**
- `AccessDenied` errors during terraform apply
- `UnauthorizedOperation` exceptions
- IAM permission errors

**Solutions:**
```bash
# Verify AWS credentials
aws sts get-caller-identity

# Check specific permissions
aws iam simulate-principal-policy \
  --policy-source-arn $(aws sts get-caller-identity --query Arn --output text) \
  --action-names lambda:CreateFunction,s3:CreateBucket,dynamodb:CreateTable \
  --resource-arns "*"

# Use different AWS profile
export AWS_PROFILE=your-profile-name
```

**Required IAM Permissions:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "lambda:*",
        "apigateway:*",
        "dynamodb:*",
        "s3:*",
        "cloudfront:*",
        "cloudwatch:*",
        "logs:*",
        "iam:CreateRole",
        "iam:AttachRolePolicy",
        "iam:PassRole",
        "budgets:*"
      ],
      "Resource": "*"
    }
  ]
}
```

#### Issue: Resource Already Exists
**Symptoms:**
- `AlreadyExistsException` errors
- Resource name conflicts
- Terraform state inconsistencies

**Solutions:**
```bash
# Import existing resource
terraform import aws_s3_bucket.frontend_bucket existing-bucket-name

# Use unique resource names
terraform apply -var="project_name=unique-project-name-$(date +%s)"

# Remove conflicting resources (if safe)
aws s3 rb s3://conflicting-bucket-name --force
```

### Lambda Function Issues

#### Issue: Function Timeout
**Symptoms:**
- Lambda functions timing out after 30 seconds
- `Task timed out after 30.00 seconds` in logs
- High duration metrics in CloudWatch

**Solutions:**
```bash
# Check current timeout setting
aws lambda get-function-configuration \
  --function-name $(terraform output -raw lambda_function_name) \
  --query Timeout

# Increase timeout in Terraform configuration
# In modules/backend/main.tf:
timeout = 60  # Increase from 30 to 60 seconds

# Apply changes
terraform apply
```

**Debugging Steps:**
```bash
# Check function logs
aws logs filter-log-events \
  --log-group-name /aws/lambda/$(terraform output -raw lambda_function_name) \
  --start-time $(date -d '1 hour ago' +%s)000 \
  --filter-pattern 'Task timed out'
```

#### Issue: Memory Limit Exceeded
**Symptoms:**
- `Runtime.OutOfMemory` errors
- Function crashes during execution
- High memory usage in CloudWatch

**Solutions:**
```bash
# Check current memory setting
aws lambda get-function-configuration \
  --function-name $(terraform output -raw lambda_function_name) \
  --query MemorySize

# Increase memory in Terraform configuration
# In modules/backend/main.tf:
memory_size = 1024  # Increase from 512 to 1024 MB

# Apply changes
terraform apply
```

#### Issue: Cold Start Performance
**Symptoms:**
- First request takes significantly longer
- Intermittent high latency
- Lambda initialization timeouts

**Solutions:**
```bash
# Enable provisioned concurrency (costs more)
aws lambda put-provisioned-concurrency-config \
  --function-name $(terraform output -raw lambda_function_name) \
  --qualifier '$LATEST' \
  --provisioned-concurrency-config ProvisionedConcurrencyConfigs=1

# Optimize package size
du -sh lambda_deployment.zip
# Should be < 50MB for better cold start performance

# Use Lambda layers for common dependencies
# Implement in modules/backend/main.tf
```

### API Gateway Issues

#### Issue: CORS Errors
**Symptoms:**
- Browser console shows CORS errors
- `Access-Control-Allow-Origin` header missing
- Preflight OPTIONS requests failing

**Solutions:**
```bash
# Check CORS configuration
aws apigateway get-resource \
  --rest-api-id $(terraform output -raw api_gateway_url | cut -d'/' -f3 | cut -d'.' -f1) \
  --resource-id root

# Test CORS headers
curl -H "Origin: https://example.com" \
  -H "Access-Control-Request-Method: GET" \
  -H "Access-Control-Request-Headers: X-Requested-With" \
  -X OPTIONS \
  $(terraform output -raw api_gateway_url)/weather
```

**Fix in Terraform:**
```hcl
# Ensure CORS is properly configured in modules/backend/main.tf
resource "aws_api_gateway_method" "options" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.weather.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}
```

#### Issue: API Gateway 5xx Errors
**Symptoms:**
- High 5xx error rate in CloudWatch
- Internal server errors
- Lambda integration failures

**Solutions:**
```bash
# Check API Gateway logs
aws logs filter-log-events \
  --log-group-name API-Gateway-Execution-Logs_$(terraform output -raw api_gateway_url | cut -d'/' -f3 | cut -d'.' -f1)/prod \
  --start-time $(date -d '1 hour ago' +%s)000 \
  --filter-pattern '5xx'

# Check Lambda function errors
aws logs filter-log-events \
  --log-group-name /aws/lambda/$(terraform output -raw lambda_function_name) \
  --start-time $(date -d '1 hour ago' +%s)000 \
  --filter-pattern 'ERROR'
```

### DynamoDB Issues

#### Issue: Throttling Errors
**Symptoms:**
- `ProvisionedThroughputExceededException` errors
- High throttling metrics in CloudWatch
- Slow API responses

**Solutions:**
```bash
# Check current capacity settings
aws dynamodb describe-table \
  --table-name $(terraform output -raw dynamodb_table_name) \
  --query 'Table.BillingModeSummary'

# Switch to on-demand billing (recommended)
# In modules/backend/main.tf:
billing_mode = "PAY_PER_REQUEST"

# Or increase provisioned capacity
read_capacity  = 10  # Increase from 5
write_capacity = 10  # Increase from 5
```

#### Issue: Item Not Found Errors
**Symptoms:**
- Cache misses when items should exist
- Inconsistent data retrieval
- TTL expiration issues

**Solutions:**
```bash
# Check item TTL settings
aws dynamodb scan \
  --table-name $(terraform output -raw dynamodb_table_name) \
  --select ALL_ATTRIBUTES \
  --limit 5

# Verify TTL configuration
aws dynamodb describe-time-to-live \
  --table-name $(terraform output -raw dynamodb_table_name)

# Check for expired items
aws dynamodb scan \
  --table-name $(terraform output -raw dynamodb_table_name) \
  --filter-expression "attribute_exists(#ttl) AND #ttl < :now" \
  --expression-attribute-names '{"#ttl": "ttl"}' \
  --expression-attribute-values '{":now": {"N": "'$(date +%s)'"}}'
```

### Frontend Issues

#### Issue: CloudFront Distribution Not Working
**Symptoms:**
- 404 errors when accessing the website
- CloudFront returns default error page
- S3 bucket not accessible

**Solutions:**
```bash
# Check CloudFront distribution status
aws cloudfront get-distribution \
  --id $(terraform output -raw cloudfront_distribution_id) \
  --query 'Distribution.Status'

# Check S3 bucket contents
aws s3 ls s3://$(terraform output -raw s3_bucket_name)/

# Test S3 bucket directly
curl -f https://$(terraform output -raw s3_bucket_name).s3.amazonaws.com/index.html
```

#### Issue: Stale Content in CloudFront
**Symptoms:**
- Old version of website still showing
- Changes not reflected after deployment
- Cached error pages

**Solutions:**
```bash
# Create CloudFront invalidation
aws cloudfront create-invalidation \
  --distribution-id $(terraform output -raw cloudfront_distribution_id) \
  --paths "/*"

# Check invalidation status
aws cloudfront list-invalidations \
  --distribution-id $(terraform output -raw cloudfront_distribution_id)
```

### External API Issues

#### Issue: Weather API Rate Limiting
**Symptoms:**
- 429 Too Many Requests errors
- Weather data not updating
- High error rates from external API

**Solutions:**
```bash
# Check weather API response
curl -H "User-Agent: weather-forecast-app/1.0 (+https://example.com)" \
  "https://api.met.no/weatherapi/locationforecast/2.0/compact?lat=59.9139&lon=10.7522"

# Verify User-Agent header configuration
aws lambda get-function-configuration \
  --function-name $(terraform output -raw lambda_function_name) \
  --query 'Environment.Variables.COMPANY_WEBSITE'

# Check cache hit rate to reduce API calls
aws logs filter-log-events \
  --log-group-name /aws/lambda/$(terraform output -raw lambda_function_name) \
  --start-time $(date -d '1 hour ago' +%s)000 \
  --filter-pattern 'Cache hit'
```

## Performance Issues

### High Latency
**Symptoms:**
- API responses > 5 seconds
- Slow page load times
- High CloudWatch latency metrics

**Diagnostic Steps:**
```bash
# Test API response time
time curl $(terraform output -raw api_gateway_url)/weather

# Check Lambda duration metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Duration \
  --dimensions Name=FunctionName,Value=$(terraform output -raw lambda_function_name) \
  --start-time $(date -d '1 hour ago' -u +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average,Maximum
```

**Solutions:**
- Increase Lambda memory allocation
- Implement connection pooling
- Optimize database queries
- Add CloudFront caching

### High Error Rates
**Symptoms:**
- Error rate > 5%
- Frequent 5xx responses
- Application unavailability

**Diagnostic Steps:**
```bash
# Check error distribution
aws logs filter-log-events \
  --log-group-name /aws/lambda/$(terraform output -raw lambda_function_name) \
  --start-time $(date -d '1 hour ago' +%s)000 \
  --filter-pattern 'ERROR' | \
  jq '.events[].message' | sort | uniq -c | sort -nr
```

## Cost Issues

### Unexpected High Costs
**Symptoms:**
- Budget alerts triggered
- Higher than expected AWS bill
- Unusual resource usage

**Diagnostic Steps:**
```bash
# Check current month costs
aws ce get-cost-and-usage \
  --time-period Start=$(date +%Y-%m-01),End=$(date +%Y-%m-%d) \
  --granularity MONTHLY \
  --metrics BlendedCost \
  --group-by Type=DIMENSION,Key=SERVICE

# Check resource usage
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=$(terraform output -raw lambda_function_name) \
  --start-time $(date -d '7 days ago' -u +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 86400 \
  --statistics Sum
```

## Monitoring and Debugging

### CloudWatch Logs Analysis

**Common Log Queries:**
```bash
# Find all errors in the last hour
aws logs filter-log-events \
  --log-group-name /aws/lambda/$(terraform output -raw lambda_function_name) \
  --start-time $(date -d '1 hour ago' +%s)000 \
  --filter-pattern 'ERROR'

# Find slow requests (> 5 seconds)
aws logs filter-log-events \
  --log-group-name /aws/lambda/$(terraform output -raw lambda_function_name) \
  --start-time $(date -d '1 hour ago' +%s)000 \
  --filter-pattern '[timestamp, requestId, level="INFO", message="Duration*", duration > 5000]'

# Check cache performance
aws logs filter-log-events \
  --log-group-name /aws/lambda/$(terraform output -raw lambda_function_name) \
  --start-time $(date -d '1 hour ago' +%s)000 \
  --filter-pattern 'Cache'
```

### X-Ray Tracing

**Enable X-Ray tracing:**
```bash
# Check if X-Ray is enabled
aws lambda get-function-configuration \
  --function-name $(terraform output -raw lambda_function_name) \
  --query 'TracingConfig'

# View traces
aws xray get-trace-summaries \
  --time-range-type TimeRangeByStartTime \
  --start-time $(date -d '1 hour ago' +%s) \
  --end-time $(date +%s)
```

### Health Check Scripts

Create a comprehensive health check script:

```bash
#!/bin/bash
# health-check.sh

echo "=== Weather Forecast App Health Check ==="

# Test frontend
echo "Testing frontend..."
if curl -f -s $(terraform output -raw cloudfront_distribution_domain) > /dev/null; then
  echo "✅ Frontend: OK"
else
  echo "❌ Frontend: FAILED"
fi

# Test API health endpoint
echo "Testing API health..."
if curl -f -s $(terraform output -raw api_gateway_url)/health > /dev/null; then
  echo "✅ API Health: OK"
else
  echo "❌ API Health: FAILED"
fi

# Test weather endpoint
echo "Testing weather endpoint..."
if curl -f -s $(terraform output -raw api_gateway_url)/weather > /dev/null; then
  echo "✅ Weather API: OK"
else
  echo "❌ Weather API: FAILED"
fi

# Check Lambda function
echo "Checking Lambda function..."
if aws lambda get-function --function-name $(terraform output -raw lambda_function_name) > /dev/null 2>&1; then
  echo "✅ Lambda Function: OK"
else
  echo "❌ Lambda Function: FAILED"
fi

# Check DynamoDB table
echo "Checking DynamoDB table..."
if aws dynamodb describe-table --table-name $(terraform output -raw dynamodb_table_name) > /dev/null 2>&1; then
  echo "✅ DynamoDB Table: OK"
else
  echo "❌ DynamoDB Table: FAILED"
fi

echo "=== Health Check Complete ==="
```

## Getting Help

### Self-Service Resources

1. **CloudWatch Dashboards**: Check the monitoring dashboard for real-time metrics
2. **AWS Documentation**: Refer to AWS service documentation for specific errors
3. **Terraform Documentation**: Check Terraform provider documentation for configuration issues

### Escalation Path

1. **Level 1**: Check this troubleshooting guide and CloudWatch logs
2. **Level 2**: Review operational runbooks and contact on-call engineer
3. **Level 3**: Escalate to AWS Support (if Enterprise support available)

### Creating Support Tickets

When creating support tickets, include:
- **Error messages**: Exact error text from logs
- **Timestamps**: When the issue occurred
- **Steps to reproduce**: What actions led to the issue
- **Environment details**: AWS region, Terraform version, etc.
- **Impact**: How many users are affected

### Community Resources

- **GitHub Issues**: Check project repository for similar issues
- **AWS Forums**: Search AWS developer forums
- **Stack Overflow**: Search for similar problems and solutions
- **Terraform Community**: Check Terraform community forums

---

**Remember**: Always check CloudWatch logs first - they contain the most detailed information about what's happening in your application.

For operational procedures and maintenance tasks, see [operational-runbooks.md](operational-runbooks.md).