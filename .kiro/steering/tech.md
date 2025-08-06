# Technology Stack

This document outlines the technical foundation and tooling for the project.

## CI/CD
- CI/CD is out of scope of this Terraform module.

## Application Tech Stack
- Python3, Boto3, Jinja templating etc.
- Unit testing of core functionality
- Basic testing of Terraform code
- Provide /health endpoint for REST APIs
- Python operations should take place in a virtual environment where optimal Python version is installed with pyenv


## Testing
- Testing should be executed in a virtual environments, to avoid conflicts with global system package versions.
- When local testing is complete, temporary virtual environments and files shall be cleaned up

## Infrastructure Tech Stack
- Terraform for Infrastructure-as-Code
- Terraform providers aws and awscc, if necessary
- Leverage community modules from https://github.com/terraform-aws-modules as relevant
- AWS Serverless architecture options are preferred for minimal operational overhead
- Terraform code is unit tested Terraform's native testing framework, HCL-based tests.
- The AWS infrastructure is Well-Architected
- Resources are tagged with Name (specific the the resource) and Service (Common, name of the solution)

## Security
- The AWS infrastructure is secure as per the latest CIS AWS Security Hub control standard
- IAM resources respect the principle of least privilege

## Observability
- For serverless components, AWS X-Ray is leveraged for tracing
- Logs are directed to AWS CloudWatch Logs. CloudWatch Logs groups have a retention period of 180 days.
- A solution specific AWS Cloudwatch Dashboard which includes relevant CloudWatch metrics for reliability, performance and cost, in addition to a list over the last failing requests

### Pre-commit for Terraform
- Pre-commit is installed and leveraged for validation and formatting.
  - terraform_fmt
  - terraform_docs in main README.md
  - check-merge-conflict
  - trailing-whitespace
  - mixed-line-ending

Example .pre-commit-config.yaml located in the root directory:
```
repos:
  - repo: https://github.com/antonbabenko/pre-commit-terraform
    rev: v1.77.3
    hooks:
      - id: terraform_fmt
      - id: terraform_docs
        args: ["--args=--sort-by required"]
      - id: terraform_checkov
        args:
          - --args=--quiet
          - --args=--download-external-modules false
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: check-merge-conflict
      - id: trailing-whitespace
        args: [--markdown-linebreak-ext=md]
      - id: mixed-line-ending
        args: ["--fix=lf"]
```

## Documentation
- AWS Labs Diagram MCP server is used to produce relevant architecture, flow and sequence diagrams, included in main README.md
- AWS Labs Pricing MCP server is used to perform a basic cost calculation of the solution, included in the main README.md
- Every task should also ensure relevant and clear documentation is created or up to date. Prefer simple and user friendly documentation, don't overcomplicate.
- All documentation follows markdown format and is stored in the `docs/` directory
- Architecture diagrams are generated programmatically using the AWS diagram MCP server
- Cost analysis documentation includes detailed breakdowns, usage projections, and optimization recommendations
- Documentation includes deployment guides, troubleshooting guides, and operational runbooks
- There should be an examples folder with README.md explaining how to include the Terraform module call in an existing CI/CD codebase.
- In documentation, provide TL;DR to make it easy and quick for developers to get up to speed.
- In high level project documentation, include an executive summary for target group project owners, to articulate functionality and the value the solution provides.

## Cost Management
- AWS Labs Pricing MCP server provides accurate cost calculations for the infrastructure components of the solution.
- Cost analysis should include environment-specific projections (staging and production).
- Cost analysis should include AWS region comparison of eu-west-1, eu-central-1 and eu-north-1 for the production environment.
- CloudWatch cost metrics and dashboards provide real-time cost monitoring.
- A solution specific AWS Budget is deployed, based on infrastructure tag Key Service. Budget alerts prevents unexpected charges.
- Guidance is provided for the top three cost items that may increase with heavy production load.
- Cost documentation is included in the main `README.md`

## Principles
- Favor KISS over complexity, simplicity over comprehensibility
- Respect and adopt well-known cloud based architecture and integration patterns

