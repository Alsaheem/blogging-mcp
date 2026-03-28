# Blogging MCP — image contains only app code + locked deps. No API keys in layers.
# Local build: docker build -t alsaheem/blogging-mcp .
# Cloud Run (linux/amd64 / x86_64): use buildx — see README "Cloud Run".
# Run:  pass secrets at runtime (-e / --env-file), never bake them into the image.
#
# Default: stdio (for `docker run -i` with a client attaching to stdin).
# HTTP:   set MCP_TRANSPORT=http and publish port 8765 (see README).

FROM python:3.12-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

COPY pyproject.toml uv.lock README.md ./
COPY src ./src

RUN uv sync --frozen --no-dev

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

ENV MCP_TRANSPORT=http
ENV MCP_HTTP_HOST=0.0.0.0 
ENV MCP_HTTP_PORT=8765

EXPOSE 8765

RUN useradd --create-home --uid 1000 app && chown -R app:app /app
USER app

# Same entrypoint as local `uv run python -m blogging_mcp` (uses project env from uv.lock)
CMD ["uv", "run", "python", "-m", "blogging_mcp"]
