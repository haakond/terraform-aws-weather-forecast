---
inclusion: fileMatch
fileMatchPattern: ["**/*.tf", "**/*.tfvars", "**/*.tftest.hcl"]
---

# Terraform Steering

Terraform-specific patterns, AWS provider v6+ gotchas, testing standards, and deployment troubleshooting from real deployment experiences.

## Core Principles

### Mandatory Delegation
- **NEVER edit `*.tf`, `*.tfvars`, or `*.tftest.hcl` files directly** — always delegate to the `terraform` subagent via `invokeSubAgent`, regardless of how small the change is.

### Infrastructure-as-Code Standards
- Terraform ~> 1.12, AWS provider ~> 6, Archive provider ~> 2
- Leverage community modules from https://github.com/terraform-aws-modules
- Unit test with Terraform's native HCL-based testing framework
- Always run `terraform validate` before considering a task complete
- **CRITICAL**: `terraform apply` is NEVER permitted in any context
- CI/CD pipeline deploys on push to main — treat every push as a production change

### Resource Defaults
- Lambda runtime: Python 3.13
- Lambda timeout: 30 seconds
- CloudWatch logs retention: 180 days

### File Organization
- `provider.tf` — Provider configuration (not in `main.tf`)
- `data.tf` — Data resources (not in `main.tf`)
- `locals.tf` — Local values (not in `main.tf`)
- `terraform.tfvars` — Populated for all default variable values

### Best Practices
- DynamoDB billing mode: `PAY_PER_REQUEST` (`ON_DEMAND` is deprecated in aws provider v6)
- DynamoDB GSI: Use `key_schema` blocks, not `hash_key`/`range_key` (deprecated in v6+)
- Prefer Terraform definitions over external bash scripts

## AWS Provider v6+ Standards

### `data.aws_region.current.name` is deprecated — use `.id`

```hcl
# ✅ Correct
Resource = "arn:aws:s3:::bucket-${data.aws_region.current.id}"
# ❌ Wrong
Resource = "arn:aws:s3:::bucket-${data.aws_region.current.name}"
```

### Lambda reserved environment variables

Never set `AWS_REGION`, `AWS_DEFAULT_REGION`, `AWS_LAMBDA_FUNCTION_NAME` manually. Access in code: `os.environ.get('AWS_REGION')`.

### DynamoDB GSI `key_schema` blocks

```hcl
# ✅ Correct
global_secondary_index {
  name = "my-index"
  key_schema {
    attribute_name = "my_attribute"
    key_type       = "HASH"
  }
  projection_type = "ALL"
}
```

## Terraform Testing Standards

### Critical Restrictions
- `terraform apply` is NEVER permitted — all testing uses `command = plan` only
- Always run `terraform init` before executing tests

### Test File Organization
- Tests in `tests/terraform/` directory
- Naming: `{module_name}_test.tftest.hcl`

### Provider Configuration for Tests

```hcl
provider "aws" {
  alias  = "test"
  region = "eu-north-1"
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_region_validation      = true
  skip_requesting_account_id  = true
  access_key = "test"
  secret_key = "test"
}

provider "archive" { alias = "test" }
provider "random" { alias = "test" }
provider "local" { alias = "test" }
```

### Mock Data Standards
- ARNs: `arn:aws:service:region:123456789012:resource/test-resource`
- Names: `test-weather-forecast-{resource-type}`
- Regions: `eu-north-1` (primary test region)
- Account IDs: `123456789012`

### Common Test Issues

- **`"Module not installed"` error**: Run `terraform init` before tests
- **`"Invalid provider configuration"` error**: Include aliased provider blocks; reference with `providers = { aws = aws.test }`
- **`"No valid credential sources found"` error**: Use test provider config with `skip_credentials_validation = true`
- **`"No value for required variable"` error**: Cross-check `variables.tf` for required variables before running tests

## Deployment Troubleshooting

### S3 CORS — `ExposeHeader` wildcard not supported
List specific headers instead of wildcards in `expose_headers`.

### DynamoDB — unused attributes error
Only define `attribute` blocks for keys used in `hash_key`, `range_key`, or GSI keys.

### CloudFront — `forwarded Header Name *` not allowed by S3
Specify allowed headers explicitly: `["Origin", "Access-Control-Request-Headers", "Access-Control-Request-Method", "Authorization"]`.

### API Gateway stale deployment — `MissingAuthenticationTokenException`
Include all API Gateway components (resources, methods, integrations, CORS) in deployment triggers.

### CloudFront + S3 ACL race condition
Use `depends_on` to ensure ACL is set before CloudFront distribution update.

## Pre-commit for Terraform

Hooks configured with `fail_fast: true`:
- `terraform_fmt` — Code formatting
- `terraform_docs` — README generation (`--sort-by required`)
- `terraform_checkov` — Security scanning (`--quiet`, `--download-external-modules false`)
- `check-merge-conflict`, `trailing-whitespace`, `mixed-line-ending`
