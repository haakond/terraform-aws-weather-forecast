#!/bin/bash

# Frontend validation script for CI/CD environments
# This script helps identify and fix common npm issues before running Terraform

set -e

echo "=== Frontend Validation Script ==="

# Find frontend directory
FRONTEND_DIRS=(
    "frontend"
    "./frontend"
    "modules/frontend/frontend"
    ".terraform/modules/*/frontend"
)

FRONTEND_PATH=""
for dir in "${FRONTEND_DIRS[@]}"; do
    if [ -d "$dir" ] && [ -f "$dir/package.json" ]; then
        FRONTEND_PATH="$dir"
        echo "✓ Found frontend directory: $FRONTEND_PATH"
        break
    fi
done

if [ -z "$FRONTEND_PATH" ]; then
    echo "❌ Frontend directory not found"
    echo "Searched in:"
    for dir in "${FRONTEND_DIRS[@]}"; do
        echo "  - $dir"
    done
    exit 1
fi

cd "$FRONTEND_PATH"

echo "=== Environment Information ==="
echo "Node.js version: $(node --version)"
echo "npm version: $(npm --version)"
echo "Current directory: $(pwd)"

echo "=== Package.json Validation ==="
if [ ! -f "package.json" ]; then
    echo "❌ package.json not found"
    exit 1
fi

echo "✓ package.json found"

# Check for required dependencies
if ! grep -q '"react"' package.json; then
    echo "❌ React dependency not found in package.json"
    exit 1
fi

if ! grep -q '"react-scripts"' package.json; then
    echo "❌ react-scripts dependency not found in package.json"
    exit 1
fi

echo "✓ Required dependencies found in package.json"

echo "=== Lock File Validation ==="
if [ -f "package-lock.json" ]; then
    echo "✓ package-lock.json found"

    # Test npm ci
    echo "Testing npm ci..."
    if npm ci --dry-run >/dev/null 2>&1; then
        echo "✓ npm ci validation passed"
    else
        echo "⚠ npm ci validation failed"
        echo "This may cause issues during Terraform deployment"
        echo "Consider running: rm -rf node_modules package-lock.json && npm install"
    fi
else
    echo "⚠ package-lock.json not found"
    echo "Will use npm install during deployment"
fi

echo "=== Build Script Validation ==="
if npm run --silent 2>/dev/null | grep -q "build"; then
    echo "✓ Build script found"
else
    echo "❌ Build script not found in package.json"
    exit 1
fi

echo "=== Validation Complete ==="
echo "Frontend directory is ready for Terraform deployment"
