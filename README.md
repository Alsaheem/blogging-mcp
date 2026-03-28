# Blogging MCP

An [MCP](https://modelcontextprotocol.io/) server built with [FastMCP](https://gofastmcp.com/) that publishes Markdown articles to **dev.to** and **Hashnode** in one call.

Hashnode uses the official [GraphQL API](https://docs.hashnode.com/quickstart/introduction) (`POST https://gql.hashnode.com`). See also the [Hashnode API reference](https://apidocs.hashnode.com/).

## Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/)

## Setup

```bash
cd blogging-articles-mcp
uv sync --all-groups
```

Copy `.env.example` to `.env` and set:

| Variable | Description |
|----------|-------------|
| `DEVTO_API_KEY` | From [dev.to](https://dev.to/settings/extensions) → **DEV Community API Keys** |
| `HASHNODE_TOKEN` | Personal Access Token from [Hashnode developer settings](https://hashnode.com/settings/developer) |
| `HASHNODE_PUBLICATION_HOST` | Your blog host, e.g. `username.hashnode.dev` or a custom domain |

## Run (stdio, for Cursor / Claude Desktop)

```bash
uv run python -m blogging_mcp
```

Or:

```bash
uv run fastmcp run src/blogging_mcp/server.py:mcp
```

Environment:

- `MCP_TRANSPORT` — `stdio` (default) or `http`
- `MCP_HTTP_PORT` — port when using `http` (default `8765`)

## Run (HTTP)

```bash
MCP_TRANSPORT=http MCP_HTTP_PORT=8765 uv run python -m blogging_mcp
```

## Cursor MCP config

Add to your MCP settings (adjust path):

```json
{
  "mcpServers": {
    "blogging": {
      "command": "uv",
      "args": ["run", "python", "-m", "blogging_mcp"],
      "cwd": "/absolute/path/to/blogging-articles-mcp",
      "env": {
        "DEVTO_API_KEY": "your-key",
        "HASHNODE_TOKEN": "your-pat",
        "HASHNODE_PUBLICATION_HOST": "you.hashnode.dev"
      }
    }
  }
}
```

If you **host** the server over HTTP (see **Run (HTTP)** below), configure your MCP client to use that endpoint’s URL instead of `command` / `cwd`—follow your client’s docs for remote or SSE MCP servers.

## Tools

- **`publish_article`** — Posts to dev.to (REST) and Hashnode (`createDraft` then `publishDraft` when `hashnode_published` is true). Returns `dev_to` and `hashnode` outcomes (`ok`, `url`, `error`, `note`).
- **`verify_credentials`** — Checks dev.to key and Hashnode publication resolution (no publishing).

If `hashnode_published` is false, only a Hashnode **draft** is created; see the `note` field on the Hashnode outcome.

## Development

```bash
uv run ruff check .
uv run ruff format .
uv run pytest
```

## Docker

```bash
docker build -t blogging-mcp .
docker run --rm -i \
  -e DEVTO_API_KEY=... \
  -e HASHNODE_TOKEN=... \
  -e HASHNODE_PUBLICATION_HOST=you.hashnode.dev \
  blogging-mcp
```

For HTTP: `-e MCP_TRANSPORT=http -p 8765:8765`.

## License

MIT
# blogging-mcp
