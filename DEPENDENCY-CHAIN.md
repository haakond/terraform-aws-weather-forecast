# Frontend Build and Upload Dependency Chain

This document explains the dependency chain that ensures proper sequencing of frontend build and S3 upload operations.

## Dependency Flow

```
aws_s3_bucket.website
         ↓
null_resource.frontend_build
         ↓
null_resource.build_verification
         ↓
null_resource.generate_file_list
         ↓
data.local_file.build_file_list
         ↓
aws_s3_object.frontend_files
         ↓
null_resource.frontend_invalidation
```

## Resource Details

### 1. `aws_s3_bucket.website`
- **Purpose**: Creates the S3 bucket for static website hosting
- **Dependencies**: None (base resource)
- **Next**: Required before build process starts

### 2. `null_resource.frontend_build`
- **Purpose**: Builds the React frontend application
- **Dependencies**: `aws_s3_bucket.website`
- **Actions**:
  - Resolves frontend directory path
  - Installs npm dependencies (with error handling)
  - Builds React application
  - Verifies build directory creation
  - Performs initial file verification
- **Duration**: ~2-5 minutes (depending on dependencies)

### 3. `null_resource.build_verification`
- **Purpose**: Ensures build is complete and files are ready for upload
- **Dependencies**: `null_resource.frontend_build`
- **Actions**:
  - Waits 3 seconds for build stability
  - Verifies build directory exists
  - Checks for critical files (index.html)
  - Counts total files
  - Additional 2-second stability wait
- **Duration**: ~5 seconds
- **Triggers**: Re-runs when build changes

### 4. `null_resource.generate_file_list`
- **Purpose**: Generates a list of all files to be uploaded to S3
- **Dependencies**: `null_resource.build_verification`
- **Actions**:
  - Scans build directory for all files
  - Creates `.terraform-file-list.txt` with relative file paths
  - Excludes the file list itself from the list
  - Provides debug output showing file count
- **Duration**: ~2-5 seconds
- **Output**: `.terraform-file-list.txt` in build directory

### 5. `data.local_file.build_file_list`
- **Purpose**: Reads the generated file list for Terraform processing
- **Dependencies**: `null_resource.generate_file_list`
- **Actions**:
  - Reads the content of `.terraform-file-list.txt`
  - Makes file list available to other resources
- **Duration**: Instantaneous

### 6. `aws_s3_object.frontend_files`
- **Purpose**: Uploads all built files to S3
- **Dependencies**:
  - `aws_s3_bucket.website`
  - `null_resource.generate_file_list`
  - `data.local_file.build_file_list`
- **Actions**:
  - Uses file list from data source for `for_each`
  - Uploads each file with appropriate content type
  - Sets cache control headers
  - Generates ETags for cache invalidation
- **Duration**: ~30 seconds to 2 minutes (depending on file count)

### 7. `null_resource.frontend_invalidation`
- **Purpose**: Invalidates CloudFront cache after upload
- **Dependencies**: `aws_s3_object.frontend_files`
- **Actions**:
  - Creates CloudFront invalidation for all paths (`/*`)
  - Ensures fresh content is served immediately
- **Duration**: ~10-30 seconds

## Timing and Stability

### Built-in Delays
- **Post-build verification**: 5 seconds in `frontend_build`
- **Pre-upload stability**: 3 seconds in `build_verification`
- **Final stability check**: 2 seconds in `build_verification`
- **File list generation**: ~2-5 seconds in `generate_file_list`
- **Total minimum delay**: ~12-15 seconds between build completion and S3 upload

### Why These Delays Are Necessary
1. **File system consistency**: Ensures all build files are written to disk
2. **Process completion**: Allows npm build process to fully complete
3. **CI/CD reliability**: Accounts for slower CI/CD environments
4. **Race condition prevention**: Prevents S3 upload from starting before files are ready
5. **File list accuracy**: Ensures complete file enumeration before upload

### Key Innovation: File List Generation
The critical fix is the addition of `null_resource.generate_file_list` which:
- **Solves the timing issue**: Generates file list AFTER build completes
- **Provides accurate enumeration**: Uses `find` command to list all files
- **Enables proper dependencies**: Creates a concrete dependency chain
- **Prevents empty uploads**: Ensures files exist before S3 upload begins

## Error Handling

### Build Failures
- **npm dependency issues**: Automatic fallback to clean install
- **Build script failures**: Process exits with error code
- **Missing build output**: Verification fails and stops deployment

### Upload Failures
- **Missing files**: `fileset()` function handles missing directories gracefully
- **File access issues**: Terraform will retry failed uploads
- **Partial uploads**: Each file is uploaded independently

### Recovery Mechanisms
- **Automatic retries**: Terraform handles transient failures
- **Clean state**: Each deployment starts with fresh verification
- **Detailed logging**: Comprehensive debug output for troubleshooting

## Monitoring and Debugging

### Key Outputs
- `frontend_build_file_count`: Number of files built
- `frontend_build_path`: Path to build directory
- `cloudfront_distribution_id`: For manual cache invalidation if needed

### Log Indicators
- `✓ Build verification completed`: Build is ready for upload
- `✓ Frontend dependencies installed`: npm issues resolved
- `Build contains X files`: File count verification
- `Frontend build verification completed successfully`: All checks passed

### Common Issues
1. **Zero files uploaded**: Build verification failed or build directory empty
2. **Partial uploads**: File permissions or timeout issues
3. **Cache not invalidated**: CloudFront invalidation failed

## Testing

### Local Testing
```bash
# Test build process locally
./scripts/test-frontend-build.sh

# Validate configuration
./scripts/validate-frontend.sh
```

### CI/CD Validation
```bash
# Check outputs after deployment
terraform output frontend_build_file_count
terraform output frontend_build_path

# Verify S3 contents
aws s3 ls s3://your-bucket-name --recursive
```

This dependency chain ensures reliable, consistent frontend deployments across all environments.
