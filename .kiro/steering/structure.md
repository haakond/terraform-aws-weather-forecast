# Project Structure

This document outlines the organization and folder structure conventions for the project.

## Current Structure
```
.
├── .kiro/              # Kiro AI assistant configuration
│   └── steering/       # AI guidance documents
├── .vscode/            # VSCode workspace settings
│   └── settings.json   # Editor configuration
```

## Planned Structure
- Terraform code and structure is based on community best practices from https://www.terraform-best-practices.com/

## Conventions
- Use lowercase with hyphens for directory names when possible
- Keep configuration files in appropriate directories (.vscode, .kiro, etc.)
- Maintain clear separation between source code, tests, and documentation
- Follow language-specific conventions once tech stack is chosen

## File Naming
- Use consistent naming conventions across the project
- Follow language/framework specific patterns
- Keep file names descriptive but concise

## Organization Principles
- Group related functionality together
- Maintain flat structure where possible to avoid deep nesting
- Use clear, descriptive names for directories and files
- Keep configuration and tooling files at appropriate levels
- Separation of concern between application and infrastructure content.