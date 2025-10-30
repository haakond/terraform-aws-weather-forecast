# MCP Servers

## Active Servers
- **aws-docs**: AWS documentation and best practices
- **aws-api**: Direct AWS API calls and resource management
- **aws-knowledge-mcp-server**: Architectural patterns and Well-Architected Framework
- **aws-terraform**: Terraform configurations and modules
- **aws-cloudformation**: CloudFormation templates
- **aws-serverless**: SAM templates and serverless patterns
- **aws-cdk**: CDK constructs and stacks

## Disabled
- **aws-core**: Package availability TBD
- **fetch**: HTTP requests (not needed)

## Usage Priority
1. **aws-terraform** for IaC (primary)
2. **aws-serverless** for Lambda/API Gateway patterns
3. **aws-docs** for service documentation
4. **aws-knowledge-mcp-server** for architecture guidance
5. **aws-api** for direct AWS operations

## Configuration
- Config: `.kiro/settings/mcp.json` (workspace) or `~/.kiro/settings/mcp.json` (global)
- Servers auto-reconnect on config changes
- Requires `uv` and `uvx` installed (install via pip or homebrew)
