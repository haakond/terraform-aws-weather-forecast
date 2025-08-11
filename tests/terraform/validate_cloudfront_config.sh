#!/bin/bash

# CloudFront configuration validation script
set -e

echo "Validating CloudFront price class configuration..."

# Change to frontend module directory
cd ../../modules/frontend

# Initialize Terraform
echo "Initializing Terraform..."
terraform init -backend=false

# Validate configuration
echo "Validating Terraform configuration..."
terraform validate

# Check if price class variable is properly configured
echo "Checking CloudFront price class configuration..."
if grep -q 'price_class.*=.*var.cloudfront_price_class' main.tf; then
    echo "✓ CloudFront price class is properly configured to use variable"
else
    echo "✗ CloudFront price class is not properly configured"
    exit 1
fi

# Check if default price class is PriceClass_100
if grep -q 'default.*=.*"PriceClass_100"' variables.tf; then
    echo "✓ Default CloudFront price class is set to PriceClass_100"
else
    echo "✗ Default CloudFront price class is not set to PriceClass_100"
    exit 1
fi

# Check if HTTP methods are restricted
if grep -q 'allowed_methods.*=.*\["GET", "HEAD", "OPTIONS"\]' main.tf; then
    echo "✓ CloudFront HTTP methods are properly restricted to GET, HEAD, OPTIONS"
else
    echo "✗ CloudFront HTTP methods are not properly restricted"
    exit 1
fi

# Check if query string forwarding is enabled for caching optimization
if grep -q 'query_string.*=.*true' main.tf; then
    echo "✓ CloudFront query parameter caching is enabled"
else
    echo "✗ CloudFront query parameter caching is not enabled"
    exit 1
fi

# Check if default TTL is set to 900 seconds
if grep -q 'default_ttl.*=.*900' main.tf; then
    echo "✓ CloudFront default TTL is set to 900 seconds (15 minutes)"
else
    echo "✗ CloudFront default TTL is not set to 900 seconds"
    exit 1
fi

echo "✓ All CloudFront configuration validations passed!"
echo "CloudFront distribution is configured with:"
echo "  - Price class 100 for Europe and US coverage"
echo "  - Restricted HTTP methods (GET, HEAD, OPTIONS)"
echo "  - Query parameter-based caching enabled"
echo "  - Default TTL of 900 seconds (15 minutes)"