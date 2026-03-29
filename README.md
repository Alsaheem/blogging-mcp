# Blogging MCP

An [MCP](https://modelcontextprotocol.io/) server built with [FastMCP](https://gofastmcp.com/) that publishes Markdown articles to **dev.to** and **Hashnode** in one call. Hashnode uses the [GraphQL API](https://docs.hashnode.com/quickstart/introduction) (`POST https://gql.hashnode.com`); see the [Hashnode API reference](https://apidocs.hashnode.com/).

## Quick start: Cursor and Claude Desktop

You do **not** need to clone this repo or install Python for **HTTP** mode—only your dev.to and Hashnode credentials and the JSON below.

**Short path:** Base64-encode the three values ([Credentials](#1-credentials)). **Cursor:** copy [`mcp.cursor.json.local.example`](mcp.cursor.json.local.example) → `~/.cursor/mcp.json`, paste your Base64 strings, run [`MCP_TRANSPORT=http`](#run-the-server), restart Cursor. **Claude Desktop:** copy [`mcp.claude.json.local.example`](mcp.claude.json.local.example) into `claude_desktop_config.json`, same values in `--header` lines, run the HTTP server, restart Claude.

### 1. Credentials

Get your own keys from dev.to and Hashnode (see table). For **HTTP** MCP, put each value in the `"headers"` block as **standard Base64** (UTF-8 string, then encode). The server **decodes** Base64 on each request; if decoding fails (invalid Base64 or not valid UTF-8), the raw string is used so plain text still works.

Encode on the command line (use `echo -n` so you do not add a newline):

```bash
echo -n 'paste-your-real-devto-key-here' | base64
echo -n 'paste-your-hashnode-token-here' | base64
echo -n 'yourblog.hashnode.dev' | base64
```

Paste the **single-line** output into the matching header value in `mcp.json`.

| Where to get the value | Header name in JSON |
|------------------------|---------------------|
| [dev.to API key](https://dev.to/settings/extensions) → **DEV Community API Keys** | `X-DEVTO-API-KEY` |
| [Hashnode PAT](https://hashnode.com/settings/developer) | `X-HASHNODE-TOKEN` |
| Your blog host, e.g. `username.hashnode.dev` | `X-HASHNODE-PUBLICATION-HOST` |

**Security:** a file with real secrets is sensitive. Do **not** commit `mcp.json` to git if it contains tokens; keep it only on your machine (or use a global config path outside any repo).

For **HTTP** MCP (`"url": …`), credentials are sent with the **`"headers"`** block on each request. The `"env"` key in `mcp.json` only applies to **stdio** servers Cursor spawns locally—not to remote HTTP.

### 2. Cursor

**File:** `mcp.json` in Cursor’s config directory:

| OS | Path |
|----|------|
| macOS / Linux | `~/.cursor/mcp.json` |
| Windows | `%USERPROFILE%\.cursor\mcp.json` |

Create `~/.cursor` (or the Windows equivalent) if needed, or open **Cursor Settings → MCP** and edit from there.

**Pattern:** `"url"` + `"headers"`. Values are **Base64** (see [Credentials](#1-credentials)). The snippets below use **dummy** Base64—replace with encodings of your **real** secrets.

**Local server** — start the app first with `MCP_TRANSPORT=http` (default `http://127.0.0.1:8765/mcp`):

```json
{
  "mcpServers": {
    "blogging-mcp": {
      "url": "http://127.0.0.1:8765/mcp",
      "headers": {
        "X-DEVTO-API-KEY": "ZXhhbXBsZS1kZXZ0by1rZXktcGxhY2Vob2xkZXI=",
        "X-HASHNODE-TOKEN": "MDAwMDAwMDAtMDAwMC0wMDAwLTAwMDAtMDAwMDAwMDAwMDAx",
        "X-HASHNODE-PUBLICATION-HOST": "ZXhhbXBsZWJsb2cuaGFzaG5vZGUuZGV2"
      }
    }
  }
}
```

**Hosted URL** — same `headers` shape; only `"url"` changes (see [`mcp.cursor.json.remote.example`](mcp.cursor.json.remote.example)):

```json
{
  "mcpServers": {
    "blogging-mcp": {
      "url": "https://blogging-mcp-81529650669.europe-west1.run.app/mcp",
      "headers": {
        "X-DEVTO-API-KEY": "ZXhhbXBsZS1kZXZ0by1rZXktcGxhY2Vob2xkZXI=",
        "X-HASHNODE-TOKEN": "MDAwMDAwMDAtMDAwMC0wMDAwLTAwMDAtMDAwMDAwMDAwMDAx",
        "X-HASHNODE-PUBLICATION-HOST": "ZXhhbXBsZWJsb2cuaGFzaG5vZGUuZGV2"
      }
    }
  }
}
```

A single `Authorization: Bearer …` header is **not** enough for this server unless you add your own proxy that maps one token to these three values.

**After saving:** fully **quit Cursor** (*Cursor → Quit* / Cmd+Q on macOS) and open it again so MCP reloads.

Copy-paste examples: [`mcp.cursor.json.local.example`](mcp.cursor.json.local.example), [`mcp.cursor.json.remote.example`](mcp.cursor.json.remote.example).

### 3. Claude Desktop

**Claude Desktop does not support** Cursor’s `"url"` + `"headers"` block. Use **[`mcp-remote`](https://github.com/geelen/mcp-remote)** (`npx`, Node 18+) to connect to the same HTTP URL, or run **stdio** from a clone (plain `env`, no Base64)—see [Run from source](#run-from-source-optional).

**File:**

| OS | Path |
|----|------|
| macOS | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Windows | `%APPDATA%\Claude\claude_desktop_config.json` |
| Linux | `~/.config/Claude/claude_desktop_config.json` |

Keep `"preferences"` (and any other keys) in the **same** JSON object as `"mcpServers"`.

**HTTP via `mcp-remote`** — start [`MCP_TRANSPORT=http`](#run-the-server) first. Each credential is a separate `--header` with **`Name: base64`** (space after the colon). Local example:

```json
{
  "mcpServers": {
    "blogging-mcp": {
      "command": "npx",
      "args": [
        "mcp-remote",
        "http://127.0.0.1:8765/mcp",
        "--allow-http",
        "--header",
        "X-DEVTO-API-KEY: ZXhhbXBsZS1kZXZ0by1rZXktcGxhY2Vob2xkZXI=",
        "--header",
        "X-HASHNODE-TOKEN: MDAwMDAwMDAtMDAwMC0wMDAwLTAwMDAtMDAwMDAwMDAwMDAx",
        "--header",
        "X-HASHNODE-PUBLICATION-HOST: ZXhhbXBsZWJsb2cuaGFzaG5vZGUuZGV2"
      ]
    }
  }
}
```

Hosted: use [`mcp.claude.json.remote.example`](mcp.claude.json.remote.example) (HTTPS URL, **no** `--allow-http`). If `npx` hangs on first install, use `"args": ["-y", "mcp-remote", ...]`.

**After saving:** fully **quit Claude Desktop** and reopen. **Claude web / Connectors** may not support custom headers; prefer **stdio** or **`mcp-remote`** here.

Examples: [`mcp.claude.json.local.example`](mcp.claude.json.local.example), [`mcp.claude.json.remote.example`](mcp.claude.json.remote.example).

### Run from source (optional)

Only if you **develop** this repo or **self-host** (e.g. `http://127.0.0.1:8765/mcp`). Use `~/.cursor/mcp.json` with **stdio** or a custom `"url"`:

| Pattern | Notes |
|---------|--------|
| stdio + `.env` | `cwd` + `envFile` pointing at your clone and `.env` (see stdio JSON below) |
| stdio + shell env | `"cwd": "/absolute/path/to/blogging-articles-mcp"` and `"env": { "DEVTO_API_KEY": "…", … }` (plain strings) |
| Local HTTP | `"url": "http://127.0.0.1:8765/mcp"` and **`headers`** (see [Cursor](#2-cursor)); run `MCP_TRANSPORT=http uv run python -m blogging_mcp` |

**Claude Desktop (stdio)** — replace `cwd` with your clone path:

```json
{
  "mcpServers": {
    "blogging-mcp": {
      "command": "uv",
      "args": ["run", "python", "-m", "blogging_mcp"],
      "cwd": "/absolute/path/to/blogging-articles-mcp",
      "env": {
        "DEVTO_API_KEY": "your-devto-api-key-here",
        "HASHNODE_TOKEN": "your-hashnode-personal-access-token-here",
        "HASHNODE_PUBLICATION_HOST": "yourblog.hashnode.dev"
      }
    }
  }
}
```

**Security:** A public HTTP MCP URL without authentication can be abused if anyone can reach it. This project does not ship OAuth on the HTTP listener; use auth in front of self-hosted deployments when needed.

---

## Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/)

## Setup (local development)

Clone the repository and install dependencies:

```bash
cd blogging-articles-mcp
uv sync --all-groups
```

Copy `.env.example` to `.env` and set `DEVTO_API_KEY`, `HASHNODE_TOKEN`, and `HASHNODE_PUBLICATION_HOST` to your real values (same secrets as in `mcp.json` **headers** if you use HTTP—never commit `.env`).

**Who configures what:** each **user** uses their own dev.to and Hashnode credentials. For HTTP MCP, put **Base64-encoded** values in **`mcp.json` `headers`**; for local server / stdio, use `.env` or `env` in the client config (plain values). Do not commit real tokens to git.

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
- `MCP_HTTP_TIMEOUT` — HTTP client timeout in seconds for dev.to / Hashnode calls (default `30`)

Streamable HTTP behavior (JSON vs SSE, stateless mode) is controlled by **FastMCP** — see its docs and env vars such as **`FASTMCP_JSON_RESPONSE`** / **`FASTMCP_STATELESS_HTTP`** if you need to tune the transport.

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

**Production notes (from FastMCP):** put TLS and timeouts in front (e.g. nginx with **`proxy_buffering off`** for SSE), consider **`FASTMCP_STATELESS_HTTP=true`** behind load balancers, and add **authentication** for anything reachable on the internet — see [Authentication](https://gofastmcp.com/servers/auth/authentication) in the FastMCP docs.

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
