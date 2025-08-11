# Simplified Frontend Build and Upload Dependency Chain

This document explains the simplified dependency chain that ensures proper sequencing of frontend build and S3 upload operations.

## Dependency Flow

```
aws_s3_bucket.website
         ↓
null_resource.frontend_build
         ↓
null_resource.build_verification
         ↓
null_resource.frontend_upload
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

### 4. `null_resource.frontend_upload`
- **Purpose**: Uploads all built files to S3 using AWS CLI
- **Dependencies**:
  - `aws_s3_bucket.website`
  - `null_resource.build_verification`
- **Actions**:
  - Verifies build directory exists and contains files
  - Uses `aws s3 sync` to upload all files
  - Sets cache control headers (15-minute caching)
  - Deletes old files not in current build (`--delete`)
  - Verifies upload success by counting S3 files
- **Duration**: ~30 seconds to 2 minutes (depending on file count)

### 5. `null_resource.frontend_invalidation`
- **Purpose**: Invalidates CloudFront cache after upload
- **Dependencies**: `null_resource.frontend_upload`
- **Actions**:
  - Creates CloudFront invalidation for all paths (`/*`)
  - Ensures fresh content is served immediately
- **Duration**: ~10-30 seconds

## Key Advantages of Simplified Approach

### 1. **No "Known After Apply" Issues**
- Uses `aws s3 sync` instead of individual `aws_s3_object` resources
- No need to enumerate files at plan time
- Eliminates complex `for_each` dependencies

### 2. **Simpler Dependency Chain**
- Only 4 resources instead of 6+
- Clear, linear dependency flow
- Easier to understand and debug

### 3. **Better Performance**
- `aws s3 sync` is optimized for bulk uploads
- Automatic content type detection by AWS CLI
- Parallel uploads handled by AWS CLI

### 4. **Automatic Cleanup**
- `--delete` flag removes old files automatically
- No need to manage individual file lifecycles
- Keeps S3 bucket clean

## Timing and Stability

### Built-in Delays
- **Post-build verification**: 5 seconds in `frontend_build`
- **Pre-upload stability**: 3 seconds in `build_verification`
- **Final stability check**: 2 seconds in `build_verification`
- **Total minimum delay**: ~10 seconds between build completion and S3 upload

### Upload Process
```bash
# The upload process:
1. Verify build directory exists
2. Count files to upload
3. Use aws s3 sync to upload all files
4. Set cache-control headers
5. Verify upload by counting S3 files
6. Trigger CloudFront invalidation
```

## Error Handling

### Build Failures
- **npm dependency issues**: Automatic fallback to clean install
- **Build script failures**: Process exits with error code
- **Missing build output**: Verification fails and stops deployment

### Upload Failures
- **Missing build directory**: Upload fails with clear error message
- **No files to upload**: Upload fails if build directory is empty
- **AWS CLI errors**: Terraform will retry failed uploads
- **Verification failures**: Upload fails if S3 count doesn't match

## Monitoring and Debugging

### Log Output
```
=== Uploading frontend files to S3 ===
Build path: /path/to/build
S3 bucket: my-bucket-name
Found 42 files to upload
Uploading files to S3...
✓ Successfully uploaded 42 files to S3
S3 bucket now contains 42 files
✓ Frontend upload completed successfully
```

### Key Outputs
- `frontend_build_path`: Path to build directory
- File counts shown in upload logs
- S3 verification confirms successful upload

## Testing

### Local Testing
```bash
# Test the complete build process
./scripts/test-frontend-build.sh
```

### Manual Verification
```bash
# Check S3 contents
aws s3 ls s3://your-bucket-name --recursive

# Count files
aws s3 ls s3://your-bucket-name --recursive | wc -l
```

This simplified approach eliminates the complex file enumeration issues while providing reliable, fast uploads to S3.
