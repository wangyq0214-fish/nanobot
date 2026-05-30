# CLAUDE.md

本文件为 Claude Code (claude.ai/code) 在此代码库中工作提供指导。

## 项目概述

**nanobot** (PyPI 包名: `nanobot-ai`) 是一个轻量级 Python 3.11+ AI Agent 框架，可将 LLM 连接到各种聊天平台（Telegram、Slack、Discord、飞书、钉钉、WhatsApp 等），支持工具执行、记忆、技能和定时任务。项目还包含 React/TypeScript WebUI 和 WhatsApp bridge。

## 分支策略

采用双分支模型。不确定时，提交到 `nightly`。

| 变更类型 | 目标分支 |
|---------|---------|
| 新功能 / 重构 | `nightly` |
| Bug 修复 / 文档 | `main` |

Nightly 分支的功能会每周 cherry-pick 到 `main` 的 PR 中。

## 常用命令

### Python (核心)
```bash
pip install -e ".[dev]"        # 安装开发依赖
uv sync --all-extras           # 使用 uv 安装（推荐）
pytest                         # 运行所有测试 (asyncio_mode = "auto")
pytest tests/test_foo.py       # 运行单个测试文件
pytest -k test_name            # 按名称运行单个测试
ruff check nanobot/            # 代码检查
ruff format nanobot/           # 代码格式化
```

可选依赖组：`api`、`wecom`、`weixin`、`msteams`、`matrix`、`discord`、`langsmith`、`pdf`。通过 `pip install -e ".[group]"` 安装。

CI 在 Ubuntu + Windows 上测试 Python 3.11–3.14。Ruff 在 CI 中仅检查 F401/F841。

### WebUI (webui/)
```bash
cd webui && bun install        # 安装依赖
bun run dev                    # 开发服务器
bun run build                  # 生产构建 (tsc + vite)
bun run test                   # 测试 (vitest)
bun run lint                   # 代码检查 (eslint)
```

### Bridge (bridge/)
```bash
cd bridge && npm install && npm run build
```

## 架构

### 核心消息流

```
聊天平台 → MessageBus (异步队列) → AgentLoop → LLM Provider → 工具执行 → 响应 → MessageBus → 平台
```

### 核心模块 (nanobot/)

| 模块 | 职责 |
|------|------|
| `agent/loop.py` | 核心 Agent 循环 — 接收消息、构建上下文、调用 LLM、执行工具 |
| `agent/runner.py` | 工具执行共享循环（迭代、重试、微压缩） |
| `agent/context.py` | `ContextBuilder` — 从模板、记忆、技能组装系统提示词 |
| `agent/memory.py` | 基于文件的记忆：`MEMORY.md`、`history.jsonl`、`SOUL.md`、`USER.md`；整合 + dream |
| `agent/skills.py` | 从工作区/内置目录加载 `SKILL.md` 文件（YAML frontmatter + markdown） |
| `agent/hook.py` | 生命周期钩子：`before_iteration`、`before_execute_tools`、`after_iteration`、`on_stream`、`finalize_content` |
| `agent/subagent.py` | 后台子 Agent 任务执行 |
| `agent/tools/` | 内置工具：文件系统、Shell、搜索、Web、定时任务、ask、消息、notebook、spawn、MCP |
| `agent/manager.py` | `SimpleAgentManager` — 多 Agent 人格编排 |
| `providers/` | LLM Provider 抽象 (`LLMProvider` ABC)。25+ 提供商通过 `ProviderSpec` 注册表自动匹配 |
| `channels/` | 聊天平台集成，继承 `BaseChannel`。通过 `pkgutil` + entry_points 自动发现 |
| `bus/` | `MessageBus`，包含 `InboundMessage`/`OutboundMessage` 异步队列 |
| `session/` | `SessionManager` — 会话历史持久化（JSON 文件） |
| `config/` | Pydantic 配置模式（支持 camelCase 和 snake_case），环境变量插值 (`${VAR}`) |
| `command/` | 斜杠命令路由（priority → exact → prefix → interceptors） |
| `cron/` | 定时任务："at"（一次性）、"every"（间隔）、"cron"（表达式） |
| `api/` | OpenAI 兼容 HTTP API (`/v1/chat/completions`、`/v1/models`) |
| `cli/` | Typer CLI：`nanobot agent`、`nanobot gateway`、`nanobot serve`、`nanobot onboard`、`nanobot status` |

### 关键设计模式

- **MessageBus**：异步队列解耦聊天平台与 Agent 核心
- **Provider 注册表**：`providers/registry.py` 中的 `ProviderSpec` — 两步添加新 Provider，通过模型关键字、API key 前缀或 base URL 自动匹配
- **Tool 系统**：`Tool` ABC + JSON Schema 验证，`ToolRegistry` 动态注册
- **插件式 Channel**：通过 `pkgutil` 扫描 + `entry_points("nanobot.channels")` 自动发现
- **配置**：`config/schema.py` 中的 Pydantic 模型，从 `~/.nanobot/config.json` 加载，支持 `${ENV_VAR}` 插值和 `_migrate_config()` 模式演进
- **Skills**：基于目录的 `SKILL.md` 文件，渐进式加载 — 先加载摘要，按需加载完整内容
- **模板**：`nanobot/templates/` — Jinja2 模板（`SOUL.md`、`USER.md`、`TOOLS.md`、`AGENTS.md`）由 `ContextBuilder` 组装成系统提示词

### 入口点

- **CLI**：`nanobot` 命令 → `nanobot/cli/commands.py`（Typer 应用）
- **SDK**：`nanobot/nanobot.py` 中的 `Nanobot.from_config()` → `await bot.run("message")` → `RunResult`
- **模块**：`python -m nanobot` → 同一 Typer 应用

### 测试

`tests/` 中的测试镜像源码包结构（`tests/agent/`、`tests/providers/`、`tests/channels/` 等）。根目录下的测试是集成测试。

### 文档

详细文档位于 `docs/`：配置、部署、SDK 用法、Channel 设置、Channel 插件指南。

## 代码风格

- Python 3.11+，行宽 100，`ruff` 规则 E/F/I/N/W（忽略 E501）
- 异步优先（全程使用 `asyncio`），测试使用 `asyncio_mode = "auto"`
- 优先小而专注的改动，而非大范围重写
- 优先可读性，避免过度抽象
