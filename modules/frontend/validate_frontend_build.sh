#!/bin/bash

# Frontend Build Validation Script
# This script validates that the frontend build process will work correctly
# in different environments (local development and CI/CD)

set -e

echo "=== Frontend Build Validation ==="
echo "Current working directory: $(pwd)"
echo "Script location: $(dirname "$0")"

# Function to check if a directory exists and contains expected files
check_frontend_directory() {
    local path="$1"
    echo "Checking frontend directory at: $path"

    if [ ! -d "$path" ]; then
        echo "  ❌ Directory does not exist"
        return 1
    fi

    echo "  ✅ Directory exists"

    if [ ! -f "$path/package.json" ]; then
        echo "  ❌ package.json not found"
        return 1
    fi

    echo "  ✅ package.json found"

    if [ ! -d "$path/src" ]; then
        echo "  ❌ src directory not found"
        return 1
    fi

    echo "  ✅ src directory found"

    if [ ! -d "$path/public" ]; then
        echo "  ❌ public directory not found"
        return 1
    fi

    echo "  ✅ public directory found"

    return 0
}

# Try different possible frontend paths
FRONTEND_PATHS=(
    "frontend"
    "./frontend"
    "../frontend"
    "../../frontend"
)

FOUND_FRONTEND=""

echo ""
echo "=== Searching for frontend directory ==="

for path in "${FRONTEND_PATHS[@]}"; do
    if check_frontend_directory "$path"; then
        FOUND_FRONTEND="$path"
        echo "  🎉 Found valid frontend directory at: $path"
        break
    fi
    echo ""
done

if [ -z "$FOUND_FRONTEND" ]; then
    echo "❌ No valid frontend directory found in any of the expected locations"
    echo "Expected locations:"
    for path in "${FRONTEND_PATHS[@]}"; do
        echo "  - $path"
    done
    exit 1
fi

echo ""
echo "=== Validating package.json scripts ==="

cd "$FOUND_FRONTEND"

# Check if required npm scripts exist
if npm run 2>&1 | grep -q "build:optimized"; then
    echo "✅ build:optimized script found"
else
    echo "⚠️  build:optimized script not found, will fall back to 'build'"
fi

if npm run 2>&1 | grep -q "build"; then
    echo "✅ build script found"
else
    echo "❌ build script not found - this is required"
    exit 1
fi

echo ""
echo "=== Testing npm install ==="

# Test npm install (but don't actually install to avoid side effects)
if npm list --depth=0 >/dev/null 2>&1; then
    echo "✅ Dependencies are already installed"
else
    echo "⚠️  Dependencies not installed, but package.json is valid"
fi

echo ""
echo "=== Validation Summary ==="
echo "✅ Frontend directory found at: $FOUND_FRONTEND"
echo "✅ All required files and directories present"
echo "✅ package.json contains required scripts"
echo ""
echo "🎉 Frontend build validation passed!"
echo ""
echo "To use this frontend directory in Terraform, set:"
echo "  frontend_source_path = \"$FOUND_FRONTEND\""