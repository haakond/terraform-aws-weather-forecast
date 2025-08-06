#!/bin/bash

# Basic validation script for API Gateway configuration
# This script validates the Terraform configuration without requiring AWS credentials

set -e

echo "=== API Gateway Configuration Validation ==="

# Change to the backend module directory
cd "$(dirname "$0")/../../modules/backend"

echo "1. Validating Terraform configuration..."
terraform validate

echo "2. Checking Terraform formatting..."
terraform fmt -check

echo "3. Running basic plan check (without AWS credentials)..."
# This will fail due to missing credentials but will validate the configuration syntax
terraform plan -input=false -var="project_name=test-weather-app" -var="service_name=weather-forecast-app" 2>&1 | grep -E "(Error:|Warning:|Success)" || true

echo "4. Checking for required API Gateway resources..."
# Verify that the main.tf file contains the required API Gateway resources
required_resources=(
    "aws_api_gateway_rest_api"
    "aws_api_gateway_deployment"
    "aws_api_gateway_stage"
    "aws_api_gateway_resource"
    "aws_api_gateway_method"
    "aws_api_gateway_integration"
    "aws_api_gateway_method_response"
    "aws_api_gateway_integration_response"
    "aws_api_gateway_usage_plan"
    "aws_lambda_permission"
)

for resource in "${required_resources[@]}"; do
    if grep -q "$resource" main.tf; then
        echo "✓ Found $resource"
    else
        echo "✗ Missing $resource"
        exit 1
    fi
done

echo "5. Checking for CORS configuration..."
if grep -q "Access-Control-Allow-Origin" main.tf; then
    echo "✓ CORS headers configured"
else
    echo "✗ CORS headers missing"
    exit 1
fi

echo "6. Checking for throttling configuration..."
if grep -q "throttling_rate_limit" main.tf; then
    echo "✓ Throttling configuration found"
else
    echo "✗ Throttling configuration missing"
    exit 1
fi

echo "7. Checking for CloudWatch logging..."
if grep -q "aws_cloudwatch_log_group.*api_gateway" main.tf; then
    echo "✓ API Gateway logging configured"
else
    echo "✗ API Gateway logging missing"
    exit 1
fi

echo ""
echo "=== API Gateway Configuration Validation Complete ==="
echo "✓ All required resources and configurations are present"
echo "✓ Terraform configuration is valid and properly formatted"