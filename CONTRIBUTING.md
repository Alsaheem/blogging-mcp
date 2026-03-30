# Contributing

Thanks for helping improve **blogging-mcp**. This document describes how to set up your environment, run checks, and open a pull request.

## Getting started

1. **Fork** the repository and create a branch from `main`.
2. **Clone** your fork and install dependencies:

   ```bash
   git clone https://github.com/<your-username>/blogging-mcp.git
   cd blogging-mcp
   uv sync --all-groups
   ```

3. Copy **`.env.example`** to **`.env`** and add real dev.to / Hashnode values for local runs. Never commit `.env` or paste API keys into issues or PR descriptions.

## Before you open a PR

Run the same checks as [CI](https://github.com/alsaheem/blogging-mcp/actions/workflows/ci.yml):

```bash
uv run ruff check .
uv run ruff format --check .
uv run pytest
```

To apply formatting automatically:

```bash
uv run ruff format .
```

## Pull requests

- Open PRs against **`main`**.
- Describe **what changed** and **why** (user-visible behavior, fixes, or refactors).
- Link related **issues** when applicable.
- For larger features or API changes, consider opening an **issue** first to align on direction.
- Do not commit secrets, tokens, or personal `.env` files.

## Security

If you find a security vulnerability, follow [SECURITY.md](SECURITY.md) and do not disclose it in a public issue.

## Questions

- Use [GitHub Issues](https://github.com/alsaheem/blogging-mcp/issues) for bugs and feature requests.
- Hosted docs: [alsaheem.github.io/blogging-mcp](https://alsaheem.github.io/blogging-mcp/).
