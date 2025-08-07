#!/bin/bash

# Basic validation script for frontend module
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

echo "Frontend module validation completed successfully!"