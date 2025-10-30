# Project Structure

## Layout
```
.
├── src/                # Python Lambda application code
├── tests/              # Unit and integration tests
├── terraform/          # Infrastructure as code (follows terraform-best-practices.com)
├── docs/               # Markdown documentation
├── examples/           # Terraform module usage examples
├── .kiro/              # Kiro configuration and steering
└── .vscode/            # Editor settings
```

## Conventions
- Lowercase with hyphens for directories (e.g., `my-module/`)
- Separate application code from infrastructure code
- Flat structure preferred over deep nesting
- Config files at appropriate levels (.vscode, .kiro at root)