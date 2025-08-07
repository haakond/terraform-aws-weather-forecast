# Weather Forecast App - Monitoring and Observability

## Overview

The weather forecast application includes comprehensive monitoring and observability features implemented through AWS CloudWatch and AWS Budgets. This document outlines the monitoring capabilities and how to use them.

## CloudWatch Dashboard

### Main Dashboard Features

The main CloudWatch dashboard (`{name_prefix}-dashboard`) provides real-time visibility into:

#### Lambda Function Metrics
- **Duration**: Function execution time
- **Errors**: Number of function errors
- **Invocations**: Total function invocations
- **Throttles**: Function throttling events

#### API Gateway Metrics
- **4XX Errors**: Client-side errors
- **5XX Errors**: Server-side errors
- **Request Count**: Total API requests
- **Latency**: API response times

#### DynamoDB Metrics
- **Read Capacity**: Consumed read capacity units
- **Write Capacity**: Consumed write capacity units
- **Throttled Requests**: Database throttling events
- **Latency**: Database operation latency for GetItem and PutItem operations

#### Recent Lambda Errors
- Real-time log query showing the last 20 ERROR-level log entries
- Helps with quick troubleshooting and error identification

## CloudWatch Alarms

### Critical Alarms

The monitoring system includes the following alarms:

1. **Lambda Error Rate** (`{name_prefix}-lambda-error-rate`)
   - Triggers when Lambda errors exceed 5 in a 10-minute period
   - Monitors function reliability

2. **Lambda Duration** (`{name_prefix}-lambda-duration`)
   - Triggers when average execution time exceeds 25 seconds
   - Helps prevent timeout issues (Lambda timeout is 30s)

3. **API Gateway 5XX Errors** (`{name_prefix}-api-gateway-5xx-errors`)
   - Triggers when server errors exceed 5 in a 10-minute period
   - Monitors API reliability

4. **API Gateway Latency** (`{name_prefix}-api-gateway-latency`)
   - Triggers when average latency exceeds 5 seconds
   - Ensures responsive user experience

5. **DynamoDB Throttling** (`{name_prefix}-dynamodb-throttling`)
   - Triggers on any throttling events
   - Monitors database performance

### Custom Metrics

#### Weather API Success Rate
- **Success Metric**: Tracks successful weather data retrievals
- **Failure Metric**: Tracks failed weather data retrievals
- **Success Rate Alarm**: Triggers when success rate drops below 80%

## Cost Monitoring

### AWS Budget

The system includes an AWS Budget (`{name_prefix}-budget`) with:

- **Monthly Limit**: Configurable budget limit (default based on `budget_limit` variable)
- **Service Filter**: Filters costs by `Service:weather-forecast-app` tag
- **Alert Thresholds**:
  - 80% of budget (actual spend)
  - 100% of budget (forecasted spend)

### Cost Dashboard

The cost monitoring dashboard (`{name_prefix}-cost-dashboard`) includes:

#### Service-Level Cost Breakdown
- Overall estimated charges
- Service-specific costs for:
  - Amazon S3
  - AWS Lambda
  - Amazon API Gateway
  - Amazon DynamoDB
  - Amazon CloudFront

#### Usage Metrics (Cost Drivers)
- Lambda invocations
- API Gateway requests
- DynamoDB read/write operations

#### Cost Optimization Tips
Built-in guidance for the top 3 cost items:
1. **API Gateway Requests** - Implement client-side caching
2. **Lambda Invocations & Duration** - Optimize memory and execution time
3. **DynamoDB Operations** - Efficient caching strategies

## Log Retention

All CloudWatch log groups are configured with:
- **Retention Period**: 180 days
- **Automatic Cleanup**: Logs older than 180 days are automatically deleted

## Accessing Monitoring

### Dashboard URLs
- **Main Dashboard**: Available in Terraform output `dashboard_url`
- **Cost Dashboard**: Available in Terraform output `cost_dashboard_url`

### AWS Console Navigation
1. Navigate to CloudWatch in the AWS Console
2. Select "Dashboards" from the left menu
3. Find dashboards with your project prefix

### Alarm Management
- All alarms are listed in the CloudWatch Alarms section
- Alarm names follow the pattern: `{name_prefix}-{alarm-type}`

## Troubleshooting

### Common Issues

1. **High Lambda Duration**
   - Check function memory allocation
   - Review external API response times
   - Optimize code execution paths

2. **API Gateway 5XX Errors**
   - Check Lambda function errors
   - Verify DynamoDB connectivity
   - Review external API availability

3. **DynamoDB Throttling**
   - Consider switching to on-demand billing
   - Review read/write patterns
   - Implement exponential backoff

### Log Analysis

Use CloudWatch Logs Insights with these sample queries:

```sql
# Find all errors in the last hour
fields @timestamp, @message
| filter @message like /ERROR/
| sort @timestamp desc
| limit 20

# Analyze API response times
fields @timestamp, @duration
| filter @type = "REPORT"
| stats avg(@duration), max(@duration), min(@duration) by bin(5m)

# Track weather API success/failure rates
fields @timestamp, @message
| filter @message like /Weather data retrieved/ or @message like /Failed to retrieve weather/
| stats count() by @message
```

## Monitoring Best Practices

1. **Regular Review**: Check dashboards weekly for trends
2. **Alarm Tuning**: Adjust thresholds based on actual usage patterns
3. **Cost Monitoring**: Review monthly costs and optimize high-cost items
4. **Log Analysis**: Use CloudWatch Logs Insights for detailed troubleshooting
5. **Performance Optimization**: Monitor Lambda duration and API latency trends

## Integration with CI/CD

The monitoring infrastructure is fully defined in Terraform and can be:
- Version controlled alongside application code
- Deployed automatically in CI/CD pipelines
- Customized per environment (staging, production)
- Tested using the included Terraform test files

## Terraform Outputs

The monitoring module provides these outputs:
- `dashboard_url`: Main CloudWatch dashboard URL
- `cost_dashboard_url`: Cost monitoring dashboard URL
- `budget_name`: AWS Budget name
- `budget_arn`: AWS Budget ARN
- `alarm_names`: List of all CloudWatch alarm names