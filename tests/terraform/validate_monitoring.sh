#!/bin/bash

# Validation script for monitoring module
# This script validates that the monitoring module is properly configured

set -e

echo "🔍 Validating monitoring module configuration..."

# Check if monitoring module files exist
if [ ! -f "../../modules/monitoring/main.tf" ]; then
    echo "❌ Monitoring module main.tf not found"
    exit 1
fi

if [ ! -f "../../modules/monitoring/variables.tf" ]; then
    echo "❌ Monitoring module variables.tf not found"
    exit 1
fi

if [ ! -f "../../modules/monitoring/outputs.tf" ]; then
    echo "❌ Monitoring module outputs.tf not found"
    exit 1
fi

echo "✅ Monitoring module files exist"

# Run terraform validate on the monitoring module
echo "🔧 Running terraform validate on monitoring module..."
cd ../../modules/monitoring
terraform init -backend=false > /dev/null 2>&1
terraform validate

if [ $? -eq 0 ]; then
    echo "✅ Monitoring module validation passed"
else
    echo "❌ Monitoring module validation failed"
    exit 1
fi

cd ../../tests/terraform

# Run the monitoring tests
echo "🧪 Running monitoring module tests..."
terraform test -filter=monitoring_cloudwatch.tftest.hcl
terraform test -filter=monitoring_budget.tftest.hcl

echo "✅ All monitoring module validations passed!"
echo ""
echo "📊 Monitoring Features Implemented:"
echo "  - CloudWatch Dashboard with Lambda, API Gateway, and DynamoDB metrics"
echo "  - CloudWatch Alarms for Lambda errors, API Gateway 5XX errors, and DynamoDB throttling"
echo "  - Custom metric filters for weather API success rates"
echo "  - Log retention policies (180 days)"
echo "  - AWS Budget with Service tag filter"
echo "  - Cost monitoring dashboard with usage metrics"
echo "  - Budget alerts at 80% actual and 100% forecasted thresholds"