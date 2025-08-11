#!/bin/bash

# Frontend module validation script
set -e

echo "Validating frontend module..."

# Change to frontend module directory
cd ../../modules/frontend

# Initialize Terraform
echo "Initializing Terraform..."
terraform init -backend=false

# Validate configuration
echo "Validating Terraform configuration..."
terraform validate

# Format check
echo "Checking Terraform formatting..."
terraform fmt -check

echo "Frontend module Terraform validation completed successfully!"

# Also run frontend unit tests if frontend directory exists
if [ -d "../../frontend" ]; then
    echo "Running frontend unit tests..."
    cd ../../frontend

    # Install dependencies if needed
    if [ ! -d "node_modules" ]; then
        echo "Installing frontend dependencies..."
        npm ci --silent
    fi

    # Run tests in non-interactive mode
    echo "Running frontend tests in non-interactive mode..."
    npm test

    echo "Frontend unit tests completed successfully!"
else
    echo "Frontend directory not found, skipping frontend unit tests"
fi