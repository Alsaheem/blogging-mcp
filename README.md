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

Copy `.env.example` to `.env` and set **your own** credentials (never commit `.env`):

| Variable | Description |
|----------|-------------|
| `DEVTO_API_KEY` | From [dev.to](https://dev.to/settings/extensions) → **DEV Community API Keys** |
| `HASHNODE_TOKEN` | Personal Access Token from [Hashnode developer settings](https://hashnode.com/settings/developer) |
| `HASHNODE_PUBLICATION_HOST` | Your blog host, e.g. `username.hashnode.dev` or a custom domain |

Each person or deployment supplies these keys. Nothing in the repo should embed real tokens.

## Run the server

**stdio (default)** — Cursor or Claude Desktop spawn the process and talk over stdin/stdout:

```bash
uv run python -m blogging_mcp
```

**HTTP (Streamable HTTP)** — for Cursor **URL** mode or other remote clients. FastMCP serves the MCP endpoint at **`/mcp`** (default).

```bash
MCP_TRANSPORT=http MCP_HTTP_PORT=8765 uv run python -m blogging_mcp
```

Bind on all interfaces when the process runs on a VM or in Docker (so your laptop can reach it):

```bash
MCP_TRANSPORT=http MCP_HTTP_HOST=0.0.0.0 MCP_HTTP_PORT=8765 uv run python -m blogging_mcp
```

Environment:

- `MCP_TRANSPORT` — `stdio` (default) or `http`
- `MCP_HTTP_HOST` — bind address (default `127.0.0.1`)
- `MCP_HTTP_PORT` — port when using `http` (default `8765`)

Or:

```bash
uv run fastmcp run src/blogging_mcp/server.py:mcp
```

### HTTP deployment (servers, Docker, reverse proxies)

This matches the patterns in the FastMCP guide: [HTTP deployment](https://gofastmcp.com/deployment/http).

**1. Direct HTTP (built-in Uvicorn)** — same idea as `mcp.run(transport="http", host="0.0.0.0", port=8000)` in the docs; this project wires that through `MCP_TRANSPORT` and `MCP_HTTP_*`:

```bash
MCP_TRANSPORT=http MCP_HTTP_HOST=0.0.0.0 MCP_HTTP_PORT=8765 uv run python -m blogging_mcp
```

Clients use the Streamable HTTP URL **`http://<host>:<port>/mcp`** (default path; see FastMCP’s [custom path](https://gofastmcp.com/deployment/http) if you need another).

**2. ASGI app + Uvicorn** — same idea as `app = mcp.http_app()` in the docs; the app is exposed as [`blogging_mcp.asgi`](src/blogging_mcp/asgi.py):

```bash
uv run uvicorn blogging_mcp.asgi:app --host 0.0.0.0 --port 8765
```

Use this when you want the same knobs as the FastMCP guide (workers, middleware, mounting in Starlette/FastAPI, etc.).

**Production notes (from FastMCP):** put TLS and timeouts in front (e.g. nginx with **`proxy_buffering off`** for SSE), consider **`FASTMCP_STATELESS_HTTP=true`** when running multiple workers or behind a load balancer, and add **authentication** for anything reachable on the internet — see [Authentication](https://gofastmcp.com/servers/auth/authentication) in the FastMCP docs.

## Cursor: connect without putting keys in `mcp.json`

**Option A — stdio + `.env` file (recommended locally)**  
Cursor can load env vars from a file; you keep secrets only in `.env`:

```json
{
  "mcpServers": {
    "blogging": {
      "command": "uv",
      "args": ["run", "python", "-m", "blogging_mcp"],
      "cwd": "${workspaceFolder}",
      "envFile": "${workspaceFolder}/.env"
    }
  }
}
```

**Option B — stdio + shell env interpolation**  
Keys live in your environment; `mcp.json` only references them:

```json
{
  "mcpServers": {
    "blogging": {
      "command": "uv",
      "args": ["run", "python", "-m", "blogging_mcp"],
      "cwd": "${workspaceFolder}",
      "env": {
        "DEVTO_API_KEY": "${env:DEVTO_API_KEY}",
        "HASHNODE_TOKEN": "${env:HASHNODE_TOKEN}",
        "HASHNODE_PUBLICATION_HOST": "${env:HASHNODE_PUBLICATION_HOST}"
      }
    }
  }
}
```

**Option C — URL to a running HTTP server (localhost or VM)**  
1. Start the server with `MCP_TRANSPORT=http` and secrets in **its** environment (`.env` next to the app, Docker `-e`, systemd, etc.).  
2. Point Cursor at the Streamable HTTP endpoint:

```json
{
  "mcpServers": {
    "blogging": {
      "url": "http://127.0.0.1:8765/mcp"
    }
  }
}
```

For a server on another host, use `https://your-domain.example.com/mcp` (put TLS in front in production).

**Security:** If you expose the HTTP MCP on a public URL without authentication, anyone who can reach it can use your tools (including publishing). Prefer localhost, VPN/Tailscale, SSH tunnel, or a reverse proxy with auth. This project does not ship OAuth for the MCP HTTP listener.

Examples: [`mcp.json.example`](mcp.json.example) (stdio + `envFile`), [`mcp.url.json.example`](mcp.url.json.example) (HTTP on localhost — start the server first).

## Tools

**Create (both platforms)**  
- **`publish_article`** — Creates on dev.to and Hashnode (`createDraft` then `publishDraft` when `hashnode_published` is true). Returns per-platform outcomes (`ok`, `url`, `error`, `note`). If `hashnode_published` is false, only a Hashnode **draft** is created.

**dev.to (REST)** — responses use `{ "ok": true, "data": ... }` or `{ "ok": false, "error": "..." }`.  
- **`devto_get_article`** — `GET /api/articles/{id}`  
- **`devto_list_my_articles`** — `scope`: `published` | `unpublished` | `all`, pagination  
- **`devto_update_article`** — `PUT` partial update (max **4** tags)  
- **`devto_delete_article`** — `DELETE /api/articles/{id}`

**Hashnode (GraphQL)** — same `{ ok, data | error }` shape.  
- **`hashnode_get_post`** / **`hashnode_get_draft`** — read by id  
- **`hashnode_list_posts`** / **`hashnode_list_drafts`** — list publication content (cursor `after` for posts)  
- **`hashnode_update_post`** — update a **published** post (`updatePost`)  
- **`hashnode_remove_post`** — delete a published post (`removePost`)

Hashnode’s public API does not expose an **`updateDraft`** mutation; edit drafts in the Hashnode editor or publish then use **`hashnode_update_post`**.

**Other**  
- **`verify_credentials`** — Checks dev.to key and Hashnode publication (no writes).

## Development

```bash
uv run ruff check .
uv run ruff format .
uv run pytest
```

### GitHub Actions → Docker Hub

On **push to `main`/`master`** (after lint + tests pass), CI builds **`linux/amd64`** and pushes **`alsaheem/blogging-mcp:latest`**.

Add these **repository secrets** (Settings → Secrets and variables → Actions):

| Secret | Value |
|--------|--------|
| `DOCKERHUB_USERNAME` | Your Docker Hub username (e.g. `alsaheem`) |
| `DOCKERHUB_TOKEN` | A [Docker Hub access token](https://hub.docker.com/settings/security) (create under *Account Settings → Security*). Prefer this over your account password. |

You can also run the workflow manually (**Actions → CI → Run workflow**).

## Docker

The image is built from `pyproject.toml`, `uv.lock`, and `src/` only. **`.env` is in `.dockerignore`** — it is not copied into the build context, so secrets from your laptop are **not** baked into image layers **unless** you add `ARG`/`ENV` with keys in the `Dockerfile` (don’t).

**Secrets belong at runtime:** use `-e NAME=value`, `--env-file` pointing to a file **on the host**, or your orchestrator’s secret store. Anything you pass with `-e` exists in the **running container’s environment**, not in the image tarball you `docker push` (assuming you didn’t also commit keys into the Dockerfile).

### Cloud Run (linux/amd64, x86_64)

[Cloud Run](https://cloud.google.com/run/docs/container-contract) runs **`linux/amd64`** images by default. If you build on Apple Silicon (arm64), a plain `docker build` produces an **arm** image unless you set the platform.

Build and push for **amd64** with [Buildx](https://docs.docker.com/build/building/multi-platform/):

```bash
docker login   # Docker Hub (or Artifact Registry docker auth)
docker buildx build \
  --platform linux/amd64 \
  -t alsaheem/blogging-mcp:latest \
  --push .
```

Load into local Docker (amd64 image; runs via emulation on Apple Silicon):

```bash
docker buildx build --platform linux/amd64 -t alsaheem/blogging-mcp:latest --load .
```

### Local build (native platform)

```bash
docker build -t alsaheem/blogging-mcp:latest .
docker login   # as Docker Hub user alsaheem
docker push alsaheem/blogging-mcp:latest
docker run --rm -i \
  --env-file .env \
  alsaheem/blogging-mcp:latest
```

Or set variables explicitly (avoid logging the command in shared history if you use paste):

```bash
docker run --rm -i \
  -e DEVTO_API_KEY=... \
  -e HASHNODE_TOKEN=... \
  -e HASHNODE_PUBLICATION_HOST=you.hashnode.dev \
  alsaheem/blogging-mcp:latest
```

The container runs `uv run python -m blogging_mcp` (see `Dockerfile` `CMD`).

**HTTP** (e.g. Cursor URL mode from the host):

```bash
docker run --rm -p 8765:8765 \
  -e MCP_TRANSPORT=http \
  -e MCP_HTTP_HOST=0.0.0.0 \
  -e MCP_HTTP_PORT=8765 \
  --env-file .env \
  alsaheem/blogging-mcp:latest
```

Then Cursor can use `"url": "http://127.0.0.1:8765/mcp"`.

## License

MIT
