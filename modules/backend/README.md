# Backend Module - Lambda Function Configuration

This module creates the AWS Lambda function and related infrastructure for the weather forecast application.

## Resources Created

### Lambda Function
- **aws_lambda_function.weather_api**: Main Lambda function for weather API
  - Runtime: Python 3.11
  - Handler: `lambda_handler.lambda_handler`
  - Timeout: 30 seconds
  - Memory: 512 MB (configurable)
  - X-Ray tracing: Active
  - Reserved concurrency: 10 (configurable)

### CloudWatch Logs
- **aws_cloudwatch_log_group.lambda_logs**: Log group for Lambda function
  - Retention: 180 days (configurable)
  - Name: `/aws/lambda/{project_name}-weather-api`

### Lambda Alias
- **aws_lambda_alias.weather_api_live**: Live alias for blue-green deployments
  - Points to `$LATEST` version
  - Used for API Gateway integration

### IAM Resources
- **aws_iam_role.lambda_dynamodb_role**: IAM role for Lambda execution
- **aws_iam_policy.lambda_dynamodb_policy**: Custom policy for DynamoDB access
- **aws_iam_role_policy_attachment**: Attachments for policies

### Deployment Package
- **data.archive_file.lambda_zip**: Creates deployment package from source code
  - Includes all Python source files from `src/` directory
  - Excludes cache files and test directories

## Environment Variables

The Lambda function is configured with the following environment variables:

- `COMPANY_WEBSITE`: Company website for User-Agent header (configurable)
- `DYNAMODB_TABLE_NAME`: Name of the DynamoDB cache table
- `AWS_REGION`: Current AWS region
- `LOG_LEVEL`: Logging level (INFO, DEBUG, etc.)

## Security Features

### IAM Least Privilege
- Lambda role has minimal permissions for DynamoDB operations
- Specific DynamoDB actions: GetItem, PutItem, UpdateItem, Query
- Conditional access based on specific table attributes
- X-Ray permissions for tracing

### X-Ray Tracing
- Active tracing enabled for performance monitoring
- Distributed tracing across service calls
- Integration with CloudWatch for observability

### VPC Support (Optional)
- Configurable VPC deployment for enhanced security
- Support for private subnets and security groups
- Disabled by default for simplicity

## Configuration Options

### Required Variables
- `project_name`: Name of the project (used in resource naming)

### Optional Variables
- `service_name`: Service name for tagging (default: "weather-forecast-app")
- `environment`: Environment name (default: "prod")
- `company_website`: Company website for User-Agent (default: "example.com")
- `cities_config`: List of cities with coordinates for weather forecasts (defaults to Oslo, Paris, London, Barcelona)
- `log_retention_days`: CloudWatch log retention (default: 180)
- `lambda_memory_size`: Lambda memory in MB (default: 512, range: 128-10240)
- `lambda_reserved_concurrency`: Reserved concurrency (default: 10)
- `log_level`: Logging level (default: "INFO")
- `vpc_config`: VPC configuration object (optional)
- `dlq_target_arn`: Dead letter queue ARN (optional)
- `common_tags`: Additional tags to apply to resources

## Outputs

- `lambda_function_name`: Name of the Lambda function
- `lambda_function_arn`: ARN of the Lambda function
- `lambda_function_invoke_arn`: Invoke ARN for API Gateway integration
- `lambda_alias_arn`: ARN of the live alias
- `lambda_alias_invoke_arn`: Invoke ARN of the live alias
- `cloudwatch_log_group_name`: Name of the CloudWatch log group
- `cloudwatch_log_group_arn`: ARN of the CloudWatch log group
- `lambda_role_arn`: ARN of the Lambda IAM role

## Testing

The module includes comprehensive tests:

### Validation Tests
- Terraform configuration validation
- Format checking
- Resource definition verification
- Variable validation rules

### Test Execution
```bash
# Run validation tests
./tests/terraform/validate_lambda.sh
```

## Dependencies

### External Dependencies
- DynamoDB table (created by this module)
- Source code in `src/` directory
- Python requirements in `requirements.txt`

### Provider Requirements
- AWS Provider >= 5.0
- Archive Provider >= 2.0

## Usage Example

```hcl
module "backend" {
  source = "./modules/backend"

  project_name       = "my-weather-app"
  service_name       = "weather-forecast-app"
  environment        = "prod"
  company_website    = "example.com"
  log_retention_days = 180

  # Optional Lambda configuration
  lambda_memory_size           = 512
  lambda_reserved_concurrency  = 10
  log_level                   = "INFO"

  # Optional VPC configuration
  vpc_config = {
    subnet_ids         = ["subnet-12345", "subnet-67890"]
    security_group_ids = ["sg-abcdef"]
  }

  common_tags = {
    Environment = "prod"
    Owner       = "platform-team"
  }
}
```

## Architecture Integration

This Lambda function integrates with:
- **DynamoDB**: For weather data caching
- **API Gateway**: For HTTP API endpoints (configured in separate task)
- **CloudWatch**: For logging and monitoring
- **X-Ray**: For distributed tracing
- **External API**: Norwegian Meteorological Institute weather API

## Performance Considerations

- **Memory**: 512 MB default provides good balance of performance and cost
- **Timeout**: 30 seconds allows for external API calls with retries
- **Concurrency**: Reserved concurrency prevents runaway costs
- **Cold Start**: Minimal package size for faster cold starts
- **Connection Reuse**: Global variables for connection pooling

## Cost Optimization

- Reserved concurrency limits maximum cost exposure
- Right-sized memory allocation for workload
- Efficient packaging excludes unnecessary files
- CloudWatch log retention balances observability and cost