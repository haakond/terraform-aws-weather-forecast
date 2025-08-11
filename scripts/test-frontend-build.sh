#!/bin/bash

# Test script to verify frontend build process locally
# This simulates what happens during Terraform deployment

set -e

echo "=== Frontend Build Test Script ==="

# Find frontend directory (same logic as Terraform module)
FRONTEND_DIRS=(
    "frontend"
    "./frontend"
    "modules/frontend/frontend"
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
    exit 1
fi

cd "$FRONTEND_PATH"

echo "=== Simulating Terraform Build Process ==="

# Clean previous build
echo "Cleaning previous build..."
rm -rf build node_modules package-lock.json 2>/dev/null || true

# Install dependencies (same logic as Terraform module)
echo "Installing dependencies..."
if npm install --no-audit --no-fund --silent; then
    echo "✓ Dependencies installed successfully"
else
    echo "❌ Failed to install dependencies"
    exit 1
fi

# Create public directory and config
mkdir -p public
cat > public/config.js << EOF
window.APP_CONFIG = {
  API_BASE_URL: 'https://api.example.com',
  ENVIRONMENT: 'test'
};
EOF

# Build the application
echo "Building application..."
if npm run build; then
    echo "✓ Build completed successfully"
else
    echo "❌ Build failed"
    exit 1
fi

# Verify build output (same as Terraform module)
echo "=== Build Verification ==="

if [ ! -d "build" ]; then
    echo "❌ Build directory not created"
    exit 1
fi

if [ ! -f "build/index.html" ]; then
    echo "❌ index.html not found in build directory"
    exit 1
fi

# Count files
file_count=$(find build -type f | wc -l)
echo "✓ Build contains $file_count files"

if [ "$file_count" -eq 0 ]; then
    echo "❌ No files found in build directory"
    exit 1
fi

# Show build contents
echo "=== Build Directory Contents ==="
ls -la build/

if [ -d "build/static" ]; then
    echo "=== Static Assets ==="
    find build/static -type f | head -10
    static_count=$(find build/static -type f | wc -l)
    echo "Static files: $static_count"
fi

# Test upload simulation (without actually uploading to S3)
echo "=== Testing Upload Simulation ==="
cd build
echo "Files that would be uploaded to S3:"
find . -type f | head -10
upload_file_count=$(find . -type f | wc -l)
echo "Total files for upload: $upload_file_count"

cd ..

echo "=== Test Summary ==="
echo "✓ Frontend directory found: $FRONTEND_PATH"
echo "✓ Dependencies installed successfully"
echo "✓ Build completed successfully"
echo "✓ Build verification passed"
echo "✓ Total files in build: $file_count"
echo "✓ Files ready for S3 upload: $upload_file_count"
echo ""
echo "🎉 Frontend build test completed successfully!"
echo "The simplified upload process will use 'aws s3 sync' to upload all files."
