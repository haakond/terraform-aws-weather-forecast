#!/bin/bash

# Basic validation script for Lambda configuration
# This script validates the Terraform configuration without requiring AWS credentials

set -e

echo "=== Validating Lambda Terraform Configuration ==="

# Change to backend module directory
cd "$(dirname "$0")/../../modules/backend"

# Initialize Terraform
echo "Initializing Terraform..."
terraform init -backend=false

# Validate configuration
echo "Validating Terraform configuration..."
terraform validate

# Format check
echo "Checking Terraform formatting..."
terraform fmt -check=true -diff=true

echo "=== Validation completed successfully ==="

# Test that required resources are defined by checking the configuration files
echo "=== Testing resource definitions ==="

# Check that Lambda function resource exists in main.tf
if grep -q 'resource "aws_lambda_function" "weather_api"' main.tf; then
    echo "✓ Lambda function resource is defined"
else
    echo "✗ Lambda function resource is missing"
    exit 1
fi

# Check that CloudWatch log group exists
if grep -q 'resource "aws_cloudwatch_log_group" "lambda_logs"' main.tf; then
    echo "✓ CloudWatch log group resource is defined"
else
    echo "✗ CloudWatch log group resource is missing"
    exit 1
fi

# Check that Lambda alias exists
if grep -q 'resource "aws_lambda_alias" "weather_api_live"' main.tf; then
    echo "✓ Lambda alias resource is defined"
else
    echo "✗ Lambda alias resource is missing"
    exit 1
fi

# Check that X-Ray tracing is configured
if grep -q 'tracing_config' main.tf; then
    echo "✓ X-Ray tracing configuration is present"
else
    echo "✗ X-Ray tracing configuration is missing"
    exit 1
fi

# Check that environment variables are configured
if grep -q 'COMPANY_WEBSITE' main.tf; then
    echo "✓ Environment variables are configured"
else
    echo "✗ Environment variables are missing"
    exit 1
fi

# Check that IAM role is properly configured
if grep -q 'aws_iam_role.lambda_dynamodb_role.arn' main.tf; then
    echo "✓ IAM role is properly referenced"
else
    echo "✗ IAM role reference is missing"
    exit 1
fi

# Check that DynamoDB table is referenced
if grep -q 'aws_dynamodb_table.weather_cache.name' main.tf; then
    echo "✓ DynamoDB table is properly referenced"
else
    echo "✗ DynamoDB table reference is missing"
    exit 1
fi

# Check that outputs are defined
if grep -q 'lambda_function_name' outputs.tf; then
    echo "✓ Lambda function outputs are defined"
else
    echo "✗ Lambda function outputs are missing"
    exit 1
fi

# Check that variables are defined with validation
if grep -q 'lambda_memory_size' variables.tf && grep -q 'validation' variables.tf; then
    echo "✓ Lambda variables with validation are defined"
else
    echo "✗ Lambda variables with validation are missing"
    exit 1
fi

echo "=== All resource definition tests passed ==="
echo "=== Lambda configuration validation completed successfully ==="