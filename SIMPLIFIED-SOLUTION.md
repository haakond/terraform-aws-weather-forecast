# Simplified S3 Upload Solution

## Problem Solved

The original issue was a "known after apply" error with `for_each` in the `aws_s3_object` resource:

```
Error: Invalid for_each argument
for_each = toset(split("\n", trimspace(data.local_file.build_file_list.content)))
│ data.local_file.build_file_list.content is a string, known only after apply
```

## Root Cause

Terraform couldn't evaluate the `for_each` expression during the plan phase because the file content was only available after the build completed.

## Simple Solution

Replace the complex file enumeration approach with a single `aws s3 sync` command:

### Before (Complex)
```hcl
# Multiple resources with complex dependencies
null_resource.generate_file_list
  ↓
data.local_file.build_file_list  
  ↓
aws_s3_object.frontend_files (for_each with file list)
```

### After (Simple)
```hcl
# Single upload resource
resource "null_resource" "frontend_upload" {
  provisioner "local-exec" {
    command = <<-EOT
      aws s3 sync "${local.build_path}" "s3://${aws_s3_bucket.website.id}/" \
        --delete \
        --cache-control "public, max-age=900"
    EOT
  }
  depends_on = [null_resource.build_verification]
}
```

## Key Benefits

### 1. **Eliminates Terraform Complexity**
- ✅ No `for_each` dependencies
- ✅ No "known after apply" issues
- ✅ No file enumeration at plan time
- ✅ Simple, linear dependency chain

### 2. **Better Performance**
- ✅ `aws s3 sync` is optimized for bulk uploads
- ✅ Parallel uploads handled automatically
- ✅ Only uploads changed files (incremental sync)
- ✅ Automatic content type detection

### 3. **Automatic Cleanup**
- ✅ `--delete` removes old files automatically
- ✅ No orphaned files in S3
- ✅ Clean deployments every time

### 4. **Simpler Debugging**
- ✅ Single upload command to troubleshoot
- ✅ Clear success/failure indicators
- ✅ Standard AWS CLI error messages

## Final Architecture

```
aws_s3_bucket.website
         ↓
null_resource.frontend_build (builds React app)
         ↓
null_resource.build_verification (verifies build)
         ↓
null_resource.frontend_upload (aws s3 sync)
         ↓
null_resource.frontend_invalidation (CloudFront)
```

## Upload Process

```bash
# What happens during upload:
1. Verify build directory exists
2. Count files to upload  
3. Run: aws s3 sync ./build s3://bucket/ --delete --cache-control "public, max-age=900"
4. Verify upload success
5. Trigger CloudFront invalidation
```

## Error Handling

- **Build directory missing**: Clear error message, deployment stops
- **No files to upload**: Clear error message, deployment stops  
- **AWS CLI errors**: Standard AWS error messages, Terraform retries
- **Upload verification**: Counts S3 files to confirm success

## Testing

```bash
# Test locally
./scripts/test-frontend-build.sh

# Validate Terraform
terraform validate

# Deploy
terraform apply
```

## Migration Impact

- ✅ **No breaking changes** to module interface
- ✅ **Same functionality** with simpler implementation
- ✅ **Better reliability** in CI/CD environments
- ✅ **Faster deployments** with optimized uploads

This simplified approach solves the original "known after apply" error while providing better performance and reliability.
