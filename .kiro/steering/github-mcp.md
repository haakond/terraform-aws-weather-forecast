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
