---
inclusion: manual
---

# GitHub MCP Server

## Setup

### Prerequisites

- Colima (Docker runtime): `brew install colima`
- Docker CLI: `brew install docker`
- GitHub Personal Access Token with scopes: `repo`, `read:org`, `read:user`

### Start Colima

```bash
colima start
```

To start automatically on login:

```bash
brew services start colima
```

### GitHub PAT

Add to `~/.zshrc`:

```bash
export GITHUB_PERSONAL_ACCESS_TOKEN="ghp_yourtoken..."
```

Then reload: `source ~/.zshrc`

### Kiro MCP Config

In `~/.kiro/settings/mcp.json`, add under `mcpServers`:

```json
"github-mcp-server": {
  "command": "docker",
  "args": [
    "run",
    "-i",
    "--rm",
    "-e",
    "GITHUB_PERSONAL_ACCESS_TOKEN",
    "ghcr.io/github/github-mcp-server"
  ],
  "env": {
    "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_PERSONAL_ACCESS_TOKEN}"
  },
  "disabled": false,
  "autoApprove": []
}
```

### Pull the image

```bash
docker pull ghcr.io/github/github-mcp-server
```

### Verify

Restart Kiro and check MCP logs — you should see a successful connection with no auth errors.

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `Incompatible auth server` | Remote URL used instead of Docker | Switch to Docker config above |
| `Non-200 status code (400)` | PAT env var not set or not expanded | Verify `echo $GITHUB_PERSONAL_ACCESS_TOKEN` returns a value |
| `docker: command not found` | Docker CLI not installed or Colima not started | `brew install docker && colima start` |
| Image pull fails | Colima not running | `colima start` |

## Team Composition

| Name | Email | GitHub Username |
|------|-------|-----------------|
| Håkon Eriksen Drange | haakondrange@gmail.com | haakond |

When the user asks for issues assigned to them, look up issues assigned to `haakond`.

## Spec ↔ GitHub Issue Workflow

### New spec → GitHub Issue

When a new Kiro spec is created and `requirements.md` is accepted:

1. Create a GitHub issue in `haakond/terraform-aws-weather-forecast` using the contents of `requirements.md`
2. The issue body should contain the user stories and acceptance criteria from `requirements.md`
3. One `requirements.md` = one GitHub issue
4. Assign the issue to `haakond`

### GitHub Issue → New spec

When the user asks to create a Kiro spec from an existing GitHub issue:

1. Create the spec (requirements, design, tasks) based on the issue content
2. Once `requirements.md` is accepted, update the existing GitHub issue body to reflect the finalized requirements — do not create a new issue
