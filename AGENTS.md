# KSEI - Agent Guidelines

## ⚠️ Important Rules for AI Agents

When testing, developing, or running KSEI:
* **Secrets & Credentials**: Always use `secrun` when running scripts or commands that interact with AKSes KSEI API:
  ```bash
  secrun uv run ksei dump
  ```
* **User-Agent Handling**: AKSes KSEI WAF enforces strict User-Agent validation. Always use a consistent desktop browser User-Agent (`DEFAULT_USER_AGENT`) and avoid random mobile/outdated user agents.
* **Request Pacing**: The AKSes KSEI backend experiences session lock errors (HTTP 500) when requests are sent simultaneously without pacing. Keep pacing and retries in batch endpoints.
* **Unit Tests**: Run tests with `uv run python -m pytest`.

## Architecture & Entrypoints

* `src/ksei/client.py`: Core synchronous and asynchronous `KSEIClient` interacting with AKSes KSEI REST service.
* `src/ksei/cli.py`: CLI commands (`ksei dump`, `ksei mcp`).
* `src/ksei/server.py`: Model Context Protocol (MCP) server for AKSes KSEI.
* `src/ksei/utils.py`: File-based auth token cache (`FileAuthStore`) and masking helpers.
