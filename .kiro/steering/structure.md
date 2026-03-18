---
inclusion: auto
name: project-structure
description: Project directory layout, file organization conventions, and root Terraform file roles. Use when creating new files, organizing code, or understanding where things live.
---

# Project Structure

## Layout
```
.
├── src/                # Python Lambda application code
├── tests/              # Unit and integration tests
│   ├── unit/           # Python unit tests
│   └── terraform/      # Terraform HCL-based tests
├── modules/            # Terraform modules
│   ├── backend/        # Lambda, API Gateway, DynamoDB
│   ├── frontend/       # S3, CloudFront
│   └── monitoring/     # CloudWatch, Synthetics
├── frontend/           # React frontend application
├── docs/               # Markdown documentation
├── examples/           # Terraform module usage examples
├── environments/       # Environment-specific tfvars
├── .kiro/              # Kiro configuration, agents, and steering
└── .vscode/            # Editor settings
```

## Root Terraform Files
- `main.tf` — Module calls (backend, frontend, monitoring)
- `locals.tf` — Local values (name_prefix, common_tags)
- `variables.tf` / `outputs.tf` — Root variables and outputs

## Conventions
- Lowercase with hyphens for directories (e.g., `my-module/`)
- Separate application code from infrastructure code
- Flat structure preferred over deep nesting
- Config files at appropriate levels (.vscode, .kiro at root)
