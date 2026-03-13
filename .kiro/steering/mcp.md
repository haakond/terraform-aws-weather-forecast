---
inclusion: auto
---

# MCP Servers

## Active Servers (4)
- **awslabs-knowledge-mcp-server**: AWS documentation search, regional availability, Well-Architected guidance (remote, no local process)
- **awslabs-terraform**: Terraform AWS/AWSCC provider docs, module search, Checkov security scanning
- **awslabs-api**: Direct AWS CLI command execution and resource management
- **awslabs-pricing**: AWS pricing API queries, cost analysis, Terraform project cost estimation

## Removed (not needed for this project)
- **awslabs-docs**: Redundant — `awslabs-knowledge-mcp-server` covers documentation search with better results
- **awslabs-core**: Only provides `prompt_understanding` meta-tool — low value
- **awslabs-serverless**: SAM-focused — this project uses raw Terraform, not SAM
- **awslabs-diagram**: The `aws-diagram` agent writes draw.io XML directly — the MCP server produces PNGs via Python `diagrams` package, which is a different format
- **fetch**: Built-in `webFetch` tool already provides this capability

## Usage Priority
1. **awslabs-terraform** for IaC provider docs, module search, Checkov
2. **awslabs-knowledge-mcp-server** for AWS docs search and architecture guidance
3. **awslabs-pricing** for cost analysis
4. **awslabs-api** for direct AWS operations

## Powers (keep)
- **aws-cost-optimization**: Billing analysis, budget monitoring, spend optimization (complements awslabs-pricing)
- **aws-finops-cost-estimator**: AWS Calculator link generation and cost reports

## Powers (remove via Powers panel — not relevant to Terraform weather app)
- **strands**: AI agent SDK — not used
- **aws-agentcore**: Bedrock AgentCore — not used
- **aws-infrastructure-as-code**: CDK-focused — project uses Terraform
- **cloud-architect**: CDK in Python — project uses Terraform
- **power-builder**: Meta-tool for building powers — not needed for daily work

## Configuration
- MCP config: `.kiro/settings/mcp.json`
- Powers: managed via Powers panel (command palette → "Configure Powers")
- MCP servers auto-reconnect on config changes
- Requires `uv` and `uvx` installed
