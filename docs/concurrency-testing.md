# Lambda Concurrency Testing Guide

This guide explains how to test and validate the Lambda concurrency limits configured for the weather forecast application.

## Overview

The weather forecast application is configured with **5 concurrent executions** for the Lambda function to balance cost control with service availability. This document provides guidance on testing these limits.

## Configuration Validation

### Automated Validation

Use the provided validation script to check the concurrency configuration:

```bash
./scripts/validate-concurrency.sh
```

This script validates:
- ✅ Terraform configuration syntax
- ✅ Lambda concurrency variable is set to 5
- ✅ Backend module configuration
- ✅ Main module variable passing
- ✅ Default values are correct

### Manual Validation

Check the configuration manually:

```bash
# Check main variable definition
grep -A 10 "lambda_reserved_concurrency" variables.tf

# Check backend module variable
grep -A 10 "lambda_reserved_concurrency" modules/backend/variables.tf

# Check Lambda resource configuration
grep -A 5 "reserved_concurrent_executions" modules/backend/main.tf
```

## Load Testing (Post-Deployment)

### Prerequisites

- Deployed weather forecast application
- AWS CLI configured
- `curl` or similar HTTP client
- Optional: `ab` (Apache Bench) for load testing

### Basic Concurrency Test

1. **Single Request Test**:
```bash
# Test single request (should always work)
curl -X GET "https://your-api-gateway-url/weather"
```

2. **Multiple Concurrent Requests**:
```bash
# Test 3 concurrent requests (should work fine)
for i in {1..3}; do
  curl -X GET "https://your-api-gateway-url/weather" &
done
wait
```

3. **Stress Test (Trigger Throttling)**:
```bash
# Test 10 concurrent requests (may trigger throttling)
for i in {1..10}; do
  curl -X GET "https://your-api-gateway-url/weather" &
done
wait
```

### Load Testing with Apache Bench

```bash
# Install Apache Bench (if not available)
# macOS: brew install httpd
# Ubuntu: sudo apt-get install apache2-utils

# Test with 10 concurrent requests, 50 total requests
ab -n 50 -c 10 https://your-api-gateway-url/weather

# Expected results:
# - First 5 requests: Fast response (within concurrency limit)
# - Remaining requests: May be throttled or queued
```

### Expected Behavior

| Concurrent Requests | Expected Behavior | Response Time | HTTP Status |
|-------------------|------------------|---------------|-------------|
| 1-5 | Normal processing | 200-2000ms | 200 OK |
| 6-10 | Some throttling | 2000-5000ms | 200 OK or 429 |
| 10+ | Significant throttling | 5000ms+ | 429 Too Many Requests |

## Monitoring Concurrency

### CloudWatch Metrics

Monitor these key metrics in the AWS Console:

1. **ConcurrentExecutions**:
   - Shows current concurrent Lambda executions
   - Should not exceed 5 for extended periods

2. **Throttles**:
   - Number of throttled invocations
   - Should be 0 under normal load
   - Spikes indicate traffic exceeding concurrency limit

3. **Duration**:
   - Function execution time
   - May increase during high concurrency

4. **Errors**:
   - Function errors
   - May increase if throttling causes timeouts

### CloudWatch Alarms

The application includes pre-configured alarms:

- **High Throttling**: Alerts when throttles > 1% of invocations
- **High Duration**: Alerts when average duration > 10 seconds
- **High Error Rate**: Alerts when error rate > 5%

### AWS CLI Monitoring

```bash
# Get current concurrent executions
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name ConcurrentExecutions \
  --dimensions Name=FunctionName,Value=weather-forecast-app-weather-api \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Maximum

# Get throttle count
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Throttles \
  --dimensions Name=FunctionName,Value=weather-forecast-app-weather-api \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum
```

## Adjusting Concurrency Limits

### When to Increase Concurrency

Consider increasing from 5 to 10 concurrent executions if:

- Consistent throttling errors (>1% of requests)
- Response times consistently >2 seconds
- Business growth requires higher capacity
- Multiple geographic regions accessing the service

### When to Decrease Concurrency

Consider decreasing to 1-3 concurrent executions if:

- Actual usage is consistently <50% of capacity
- Cost optimization is priority over peak performance
- Development/staging environments
- Very predictable, low-volume traffic

### How to Adjust

1. **Update the variable**:
```hcl
# In terraform.tfvars or variables
lambda_reserved_concurrency = 10  # Increase to 10
```

2. **Apply the change**:
```bash
terraform plan
terraform apply
```

3. **Monitor the impact**:
- Watch CloudWatch metrics for 24-48 hours
- Verify cost impact in AWS Cost Explorer
- Check application performance

## Cost Impact of Concurrency

### Cost Calculation

| Concurrency | Max Monthly Cost* | Use Case |
|-------------|------------------|----------|
| 1 | $0.50 | Development |
| 5 | $2-5 | **Production (Recommended)** |
| 10 | $5-10 | High Traffic |
| Unreserved | $10-100+ | Enterprise (Risk) |

*Assumes continuous usage at maximum concurrency

### Cost Monitoring

- **AWS Budget**: Set to $50/month with alerts at 80%
- **Cost Explorer**: Filter by Service=weather-forecast-app tag
- **CloudWatch Dashboard**: Real-time cost tracking

## Troubleshooting

### Common Issues

1. **429 Too Many Requests**:
   - **Cause**: Requests exceeding concurrency limit
   - **Solution**: Implement client-side retry with exponential backoff
   - **Long-term**: Consider increasing concurrency limit

2. **Slow Response Times**:
   - **Cause**: Lambda cold starts or external API delays
   - **Solution**: Monitor Duration metric, optimize code
   - **Long-term**: Consider provisioned concurrency (increases cost)

3. **High Costs**:
   - **Cause**: Concurrency set too high or traffic spikes
   - **Solution**: Review actual usage, adjust concurrency
   - **Prevention**: Monitor cost alerts and usage patterns

### Debugging Commands

```bash
# Check current Lambda configuration
aws lambda get-function-configuration \
  --function-name weather-forecast-app-weather-api \
  --query 'ReservedConcurrencyConfig'

# List recent invocations
aws logs filter-log-events \
  --log-group-name /aws/lambda/weather-forecast-app-weather-api \
  --start-time $(date -d '1 hour ago' +%s)000 \
  --filter-pattern "REPORT"
```

## Best Practices

1. **Start Conservative**: Begin with 5 concurrent executions
2. **Monitor Actively**: Watch metrics for first week after deployment
3. **Test Regularly**: Perform load tests during maintenance windows
4. **Document Changes**: Record concurrency adjustments and reasons
5. **Cost Awareness**: Always consider cost impact of concurrency changes
6. **Gradual Scaling**: Increase concurrency gradually (5 → 10 → 15)

## Conclusion

The 5 concurrent execution limit provides an optimal balance between:
- **Cost Control**: Prevents runaway costs
- **Service Availability**: Handles typical weather app traffic
- **Performance**: Maintains sub-2-second response times
- **Monitoring**: Easy to track and understand

Regular monitoring and testing ensure the concurrency limits continue to meet application requirements while maintaining cost efficiency.