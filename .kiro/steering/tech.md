---
inclusion: always
---

# Tech Stack

## Application
- **Language**: Python 3 with Boto3
- **Testing**: pytest with unit tests, use virtual environments (pyenv)
- **API**: /health endpoint required for all REST APIs
- **Cleanup**: Remove temporary venvs and files after testing

## Infrastructure
- **IaC**: Terraform with aws/awscc providers
- **Modules**: Use terraform-aws-modules community modules where applicable
- **Testing**: Terraform native HCL-based tests + Checkov security scanning
- **Tagging**: All resources tagged with `Name` (resource-specific) and `Service:weather-forecast-app`
- **Pre-commit**: terraform_fmt, terraform_docs, checkov, trailing-whitespace, mixed-line-ending

## Security & Observability
- **Security**: CIS AWS Security Hub standards, IAM least privilege
- **Tracing**: AWS X-Ray for Lambda functions
- **Logging**: CloudWatch Logs with 180-day retention
- **Monitoring**: CloudWatch Dashboard with reliability, performance, cost metrics

## Documentation
- **Format**: Markdown in `docs/` directory with TL;DR sections
- **Diagrams**: Use AWS Labs Diagram MCP server for architecture diagrams
- **Cost Analysis**: Use AWS Labs Pricing MCP server (staging/prod, compare eu-west-1/eu-central-1/eu-north-1)
- **Examples**: Include Terraform module usage examples in `examples/` folder

## Workflow
- DO NOT create summary documents after tasks
- Provide brief chat summaries only
- Keep it simple (KISS principle)


## Frontend Testing

### fast-check v4 + CRA Jest: ESM subpath import resolution

**Symptom**: `SyntaxError: Cannot use import statement outside a module` or `Cannot find module 'pure-rand/generator/...'` when using `require('fast-check')` in Jest tests under Create React App.

**Root cause**: fast-check v4 ships its `"main"` field pointing to an ESM bundle. The CJS build lives at `lib/cjs/fast-check.js` but itself uses `require('pure-rand/<subpath>')` — and CRA's Jest resolver does not honour the `exports` field's `require` condition for subpath imports.

❌ Incorrect — Jest can't resolve the ESM entry or the CJS subpath imports automatically:
```json
// package.json — no jest config
```

✅ Correct — add `moduleNameMapper` in `package.json` to redirect both fast-check and all pure-rand subpaths to their CJS files:
```json
"jest": {
  "moduleNameMapper": {
    "^fast-check$": "<rootDir>/node_modules/fast-check/lib/cjs/fast-check.js",
    "^pure-rand/(.*)$": "<rootDir>/node_modules/pure-rand/lib/$1.js"
  }
}
```

This works without ejecting CRA and requires no Babel transform changes.
