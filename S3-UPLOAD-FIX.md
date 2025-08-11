# S3 Upload Dependency Fix

## Problem Description

The original issue was that `aws_s3_object.frontend_files` was not uploading files to S3 because of a fundamental Terraform evaluation timing problem:

1. **Plan-time evaluation**: The `for_each = local.build_files` was evaluated during `terraform plan`
2. **Build directory missing**: At plan time, the build directory didn't exist yet
3. **Empty file set**: `fileset(local.build_path, "**/*")` returned an empty set
4. **No S3 objects created**: With an empty `for_each`, no S3 objects were planned or created

## Root Cause

```hcl
# PROBLEMATIC APPROACH - Evaluated at plan time
locals {
  build_files = try(fileset(local.build_path, "**/*"), toset([]))
}

resource "aws_s3_object" "frontend_files" {
  for_each = local.build_files  # Empty set at plan time!
  # ...
}
```

The issue was that `depends_on` doesn't affect when Terraform evaluates `for_each` expressions. Even though the S3 object resource had `depends_on = [null_resource.frontend_build]`, the `for_each` was still evaluated during the plan phase before any resources were created.

## Solution: Post-Build File List Generation

The fix introduces a new resource that generates the file list AFTER the build completes:

### New Dependency Chain

```
aws_s3_bucket.website
         ↓
null_resource.frontend_build (builds React app)
         ↓
null_resource.build_verification (verifies build)
         ↓
null_resource.generate_file_list (creates file list)
         ↓
data.local_file.build_file_list (reads file list)
         ↓
aws_s3_object.frontend_files (uploads files)
```

### Key Components

#### 1. File List Generation Resource
```hcl
resource "null_resource" "generate_file_list" {
  provisioner "local-exec" {
    command = <<-EOT
      cd "${local.build_path}"
      find . -type f -not -name '.terraform-file-list.txt' | sed 's|^\./||' > .terraform-file-list.txt
    EOT
  }
  depends_on = [null_resource.build_verification]
}
```

#### 2. File List Data Source
```hcl
data "local_file" "build_file_list" {
  filename = "${local.build_path}/.terraform-file-list.txt"
  depends_on = [null_resource.generate_file_list]
}
```

#### 3. S3 Upload with Dynamic File List
```hcl
resource "aws_s3_object" "frontend_files" {
  for_each = toset(split("\n", trimspace(data.local_file.build_file_list.content)))
  # ...
  depends_on = [
    aws_s3_bucket.website,
    null_resource.generate_file_list,
    data.local_file.build_file_list
  ]
}
```

## Why This Works

1. **Proper sequencing**: File list is generated AFTER build completes
2. **Concrete dependencies**: Each step depends on the previous completing
3. **Dynamic evaluation**: `data.local_file` is evaluated after the file exists
4. **Accurate file enumeration**: Uses `find` command to get actual files

## Benefits

- ✅ **Eliminates race conditions**: Files are guaranteed to exist before upload
- ✅ **Accurate file counting**: Gets actual build output, not plan-time guesses
- ✅ **Better debugging**: File list is visible and can be inspected
- ✅ **Reliable CI/CD**: Works consistently across different environments
- ✅ **Proper error handling**: Fails fast if build doesn't produce files

## Testing

### Local Testing
```bash
# Test the complete build process
./scripts/test-frontend-build.sh
```

### Terraform Outputs
```bash
# Check file count after deployment
terraform output frontend_build_file_count

# Check file list location
terraform output frontend_file_list_path
```

### Manual Verification
```bash
# Check the generated file list
cat path/to/build/.terraform-file-list.txt

# Verify S3 contents match
aws s3 ls s3://your-bucket-name --recursive
```

## Migration Notes

### What Changed
- Added `local` provider requirement in `versions.tf`
- Removed `local.build_files` and `local.build_file_count` from locals
- Added `null_resource.generate_file_list` and `data.local_file.build_file_list`
- Updated `aws_s3_object.frontend_files` to use dynamic file list
- Updated outputs to use new file counting method

### Backward Compatibility
- All existing outputs still work
- No changes to module interface
- Same build process and verification steps
- Additional debugging capabilities added

## Troubleshooting

### Common Issues

1. **File list not generated**
   - Check that build verification completed successfully
   - Verify build directory exists and contains files

2. **Empty file list**
   - Check build process logs for errors
   - Verify `index.html` and other expected files exist

3. **S3 upload still fails**
   - Check file permissions in build directory
   - Verify AWS credentials and S3 bucket access

### Debug Commands
```bash
# Check if file list was generated
ls -la path/to/build/.terraform-file-list.txt

# Check file list contents
cat path/to/build/.terraform-file-list.txt

# Count files manually
find path/to/build -type f | wc -l
```

This fix ensures reliable S3 uploads by properly sequencing the build, file enumeration, and upload processes.
