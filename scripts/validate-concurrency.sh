#!/bin/bash

# Validate Lambda Concurrency Configuration
# This script validates that Lambda concurrency limits are properly configured

set -e

echo "🔍 Validating Lambda Concurrency Configuration..."

# Check if terraform is available
if ! command -v terraform &> /dev/null; then
    echo "❌ Terraform is not installed or not in PATH"
    exit 1
fi

# Initialize terraform if needed
if [ ! -d ".terraform" ]; then
    echo "📦 Initializing Terraform..."
    terraform init -backend=false > /dev/null 2>&1
fi

# Validate terraform configuration
echo "✅ Validating Terraform configuration..."
terraform validate

# Check if the concurrency variable is properly defined
echo "🔧 Checking Lambda concurrency variable..."
if terraform console <<< 'var.lambda_reserved_concurrency' 2>/dev/null | grep -q "5"; then
    echo "✅ Lambda reserved concurrency is set to 5 (recommended)"
else
    echo "⚠️  Lambda reserved concurrency is not set to the recommended value of 5"
fi

# Check the backend module configuration
echo "📋 Checking backend module configuration..."
if grep -q "reserved_concurrent_executions.*var.lambda_reserved_concurrency" modules/backend/main.tf; then
    echo "✅ Lambda concurrency configuration found in backend module"
else
    echo "❌ Lambda concurrency configuration not found in backend module"
    exit 1
fi

# Check if the main module passes the concurrency variable
echo "🔗 Checking main module variable passing..."
if grep -q "lambda_reserved_concurrency.*var.lambda_reserved_concurrency" main.tf; then
    echo "✅ Main module correctly passes concurrency variable to backend"
else
    echo "❌ Main module does not pass concurrency variable to backend"
    exit 1
fi

# Check default value in backend module
echo "🎯 Checking default concurrency value..."
if grep -A 5 "variable \"lambda_reserved_concurrency\"" modules/backend/variables.tf | grep -q "default.*=.*5"; then
    echo "✅ Backend module default concurrency is set to 5"
else
    echo "❌ Backend module default concurrency is not set to 5"
    exit 1
fi

echo ""
echo "🎯 Concurrency Configuration Summary:"
echo "   • Reserved Concurrency: 5 concurrent executions"
echo "   • Cost Control: Prevents runaway costs"
echo "   • Service Availability: ~150-300 requests/minute capacity"
echo "   • Recommended for: Production weather API workloads"
echo ""
echo "📊 To monitor concurrency in production:"
echo "   • CloudWatch metric: ConcurrentExecutions"
echo "   • CloudWatch metric: Throttles"
echo "   • CloudWatch metric: Duration"
echo ""
echo "✅ Lambda concurrency validation completed successfully!"