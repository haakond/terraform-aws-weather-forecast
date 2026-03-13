---
inclusion: auto
name: subagent-delegation
description: Subagent delegation rules and file-pattern routing. Use when executing spec tasks, editing code files, or orchestrating multi-domain work across Terraform, Python, frontend, security, docs, cost analysis, or diagram agents.
---

# Subagent Delegation

When executing spec tasks or any work matching these domains, delegate to the appropriate custom subagent in `.kiro/agents/`:

| Domain | Subagent | When to delegate |
|--------|----------|-----------------|
| Terraform (all) | `terraform` | Implementing resources, writing tests, validating, module development, troubleshooting |
| Python (all) | `python` | pytest, scripts, moto mocking, data processing, verification |
| Security scanning | `security-scanner` | Checkov scans, IAM reviews, Security Hub compliance |
| Documentation | `docs-writer` | README generation, terraform-docs, module docs |
| Cost analysis | `finops-advisor` | AWS pricing queries, cost optimization |
| Web crawling | `web-crawler` | Fetching external docs, content extraction |
| Frontend (all) | `frontend-expert` | JS, React, HTML, CSS, accessibility, responsive design |
| Architecture diagrams | `aws-diagram` | draw.io diagrams from Terraform modules |

## Diagram output

- Always save generated diagrams to a `.drawio` file (e.g., `docs/<name>.drawio`), then open the file with the draw.io application
- Never open diagrams as temporary browser previews

## Rules

- **MANDATORY**: Never edit, create, or delete files matching the patterns below directly — always delegate to the corresponding subagent via `invokeSubAgent`. No exceptions.

| File pattern | Subagent |
|-------------|----------|
| `*.tf`, `*.tfvars`, `*.tftest.hcl` | `terraform` |
| `*.py` | `python` |
| `*.js`, `*.jsx`, `*.html`, `*.css` | `frontend-expert` |

- The subagent has embedded domain knowledge and scoped MCP servers — it will produce better results
- For Python: never run Python commands directly — the `python` subagent enforces venv activation and script-based execution
- For Terraform: the `terraform` subagent handles implementation, test writing, AND validation

## Chat-driven batch execution

For executing spec tasks, ask the chat agent to execute a range of tasks:

> "Execute tasks 7 through 12 for the spec, delegating each to the appropriate specialized subagent"

The chat agent reads task descriptions from `tasks.md`, matches each task's domain to the right subagent, and delegates sequentially. This is preferred over "Run All Tasks" which bypasses specialized agents.

## Quality gate — security scanning at checkpoints

After Terraform implementation checkpoint tasks, invoke the `security-scanner` agent. HIGH and CRITICAL findings block task completion.

## Orchestrator efficiency

- The orchestrator tracks task status and sequences work — not read source files
- Subagents read spec files and source code themselves
- Reference file paths in prompts instead of passing large excerpts
