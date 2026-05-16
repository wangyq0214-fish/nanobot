# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**nanobot** (`nanobot-ai` on PyPI) is a lightweight Python 3.11+ AI agent framework that connects LLMs to chat channels (Telegram, Slack, Discord, Feishu, DingTalk, WhatsApp, etc.) with tool execution, memory, skills, and scheduling. It also includes a React/TypeScript WebUI and a WhatsApp bridge.

## Branching Strategy

Two-branch model. When in doubt, target `nightly`.

| Your Change | Target Branch |
|-------------|---------------|
| New feature / refactoring | `nightly` |
| Bug fix / docs | `main` |

Nightly features are cherry-picked into `main` PRs ~weekly.

## Common Commands

### Python (core)
```bash
pip install -e ".[dev]"        # Install with dev dependencies
uv sync --all-extras           # Alternative using uv (preferred)
pytest                         # Run all tests (asyncio_mode = "auto")
pytest tests/test_foo.py       # Run a single test file
pytest -k test_name            # Run a single test by name
ruff check nanobot/            # Lint
ruff format nanobot/           # Format
```

Optional dependency groups: `api`, `wecom`, `weixin`, `msteams`, `matrix`, `discord`, `langsmith`, `pdf`. Install with `pip install -e ".[group]"`.

CI runs on Ubuntu + Windows across Python 3.11–3.14. Ruff in CI only checks F401/F841.

### WebUI (webui/)
```bash
cd webui && bun install        # Install
bun run dev                    # Dev server
bun run build                  # Production build (tsc + vite)
bun run test                   # Tests (vitest)
bun run lint                   # Lint (eslint)
```

### Bridge (bridge/)
```bash
cd bridge && npm install && npm run build
```

## Architecture

### Core Message Flow

```
Chat Channels → MessageBus (async queues) → AgentLoop → LLM Provider → Tool execution → Response → MessageBus → Channels
```

### Key Modules (nanobot/)

| Module | Role |
|--------|------|
| `agent/loop.py` | Core agent loop — receives messages, builds context, calls LLM, executes tools |
| `agent/runner.py` | Shared execution loop for tool-using agents (iteration, retry, micro-compaction) |
| `agent/context.py` | `ContextBuilder` — assembles system prompt from templates, memory, skills |
| `agent/memory.py` | File-based memory: `MEMORY.md`, `history.jsonl`, `SOUL.md`, `USER.md`; consolidation + dream |
| `agent/skills.py` | Loads `SKILL.md` files (YAML frontmatter + markdown) from workspace/builtin dirs |
| `agent/hook.py` | Lifecycle hooks: `before_iteration`, `before_execute_tools`, `after_iteration`, `on_stream`, `finalize_content` |
| `agent/subagent.py` | Background subagent task execution |
| `agent/tools/` | Built-in tools: filesystem, shell, search, web, cron, ask, message, notebook, spawn, MCP |
| `agent/manager.py` | `SimpleAgentManager` — multi-agent persona orchestration |
| `providers/` | LLM provider abstraction (`LLMProvider` ABC). 25+ providers via `ProviderSpec` registry |
| `channels/` | Chat platform integrations extending `BaseChannel`. Auto-discovered via `pkgutil` + entry_points |
| `bus/` | `MessageBus` with `InboundMessage`/`OutboundMessage` async queues |
| `session/` | `SessionManager` — conversation history persistence (JSON files) |
| `config/` | Pydantic config schema (accepts camelCase and snake_case), env var interpolation (`${VAR}`) |
| `command/` | Slash command routing (priority → exact → prefix → interceptors) |
| `cron/` | Scheduled tasks: "at" (one-shot), "every" (interval), "cron" (expression) |
| `api/` | OpenAI-compatible HTTP API (`/v1/chat/completions`, `/v1/models`) |
| `cli/` | Typer CLI: `nanobot agent`, `nanobot gateway`, `nanobot serve`, `nanobot onboard`, `nanobot status` |

### Key Patterns

- **MessageBus**: Async queues decouple channels from the agent core
- **Provider registry**: `ProviderSpec` in `providers/registry.py` — add new providers in 2 steps. Auto-matching by model keywords, API key prefix, or base URL
- **Tool system**: `Tool` ABC with JSON Schema validation, `ToolRegistry` for dynamic registration
- **Plugin channels**: Auto-discovered via `pkgutil` scanning + `entry_points("nanobot.channels")`
- **Config**: Pydantic models in `config/schema.py`, loaded from `~/.nanobot/config.json`. Supports `${ENV_VAR}` interpolation and `_migrate_config()` for schema evolution
- **Skills**: Directory-based with `SKILL.md` files. Progressive loading — summary first, full content on demand
- **Templates**: `nanobot/templates/` — Jinja2 templates (`SOUL.md`, `USER.md`, `TOOLS.md`, `AGENTS.md`) assembled into system prompts by `ContextBuilder`

### Entry Points

- **CLI**: `nanobot` command → `nanobot/cli/commands.py` (Typer app)
- **SDK**: `Nanobot.from_config()` in `nanobot/nanobot.py` → `await bot.run("message")` → `RunResult`
- **Module**: `python -m nanobot` → same Typer app

### Tests

Tests in `tests/` mirror the source package structure (`tests/agent/`, `tests/providers/`, `tests/channels/`, etc.). Root-level tests are integration tests.

### Docs

Detailed documentation in `docs/`: configuration, deployment, SDK usage, channel setup, channel plugin guide.

## Code Style

- Python 3.11+, line length 100, `ruff` rules E/F/I/N/W (E501 ignored)
- Async-first (`asyncio` throughout), tests use `asyncio_mode = "auto"`
- Prefer small, focused changes over broad rewrites
- Prefer readable code over clever abstractions
