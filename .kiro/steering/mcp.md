---
inclusion: auto
name: mcp-servers
description: MCP server configuration, available tools, and usage priority. Use when configuring MCP servers, troubleshooting server connections, or selecting which MCP tool to use.
---

# MCP Servers

## Usage Priority
1. **awslabs-terraform** — Terraform provider docs, module search, Checkov scanning
2. **awslabs-knowledge-mcp-server** — AWS docs search, regional availability, Well-Architected guidance
3. **awslabs-api** — Direct AWS CLI command execution, pricing queries
4. **github-mcp-server** — GitHub issues, PRs, repository operations

## Configuration
- Workspace config: `.kiro/settings/mcp.json`
- Requires `uv` and `uvx` installed
