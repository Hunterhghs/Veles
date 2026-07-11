# Fable Agent

An open-source, extensible AI coding agent framework in Python, inspired by Fable 5's capabilities. Fable plans tasks with an **Orchestrator**, delegates to specialized **sub-agents** (Coder, Verifier, Architect), works through a sandboxed **tooling suite**, keeps **long-term memory** across sessions, and exports everything — tools, memory, and system prompts — over the **Model Context Protocol (MCP)** so any other AI coding agent (Claude Code, Roo Code, Cursor, Reasonix, custom scripts) can use it.

```
┌─────────────────────────────────────────────────────────────┐
│                        Orchestrator                          │
│         plans · delegates · verifies · remembers             │
└───────┬──────────────────┬──────────────────┬───────────────┘
        │                  │                  │
   ┌────▼─────┐      ┌─────▼────┐      ┌──────▼────┐
   │ Architect │      │  Coder   │      │ Verifier  │
   │ read-only │      │ full R/W │      │ read+exec │
   └────┬─────┘      └─────┬────┘      └──────┬────┘
        │                  │                  │
┌───────▼──────────────────▼──────────────────▼───────────────┐
│  Tooling suite: read_file · write_file · edit_file (diff)   │
│  list_dir · grep · glob · run_command    (workspace-sandboxed)│
├──────────────────────────────────────────────────────────────┤
│  Memory store (SQLite FTS5 or JSON) — persists across runs   │
├──────────────────────────────────────────────────────────────┤
│  Export layer: MCP server (stdio) + CLI + Python API         │
└──────────────────────────────────────────────────────────────┘
```

## Features

- **Orchestrator & sub-agents** — the orchestrator never edits files itself; it plans and delegates. Sub-agents get role-appropriate tool access (the Architect can't write, the Verifier can run tests but not patch).
- **Model-agnostic, key-optional** — first-class Anthropic support plus any OpenAI-compatible endpoint (OpenAI, Reasonix, OpenRouter, Ollama, LM Studio, vLLM, Groq, ...). Swap providers with one flag; runs entirely without an API key against local runtimes (`--provider ollama`).
- **Tooling suite** — file read/write, exact-match diff editing, directory listing, regex search, glob, and shell execution. All file access is sandboxed to the chosen workspace directory.
- **Memory & context store** — agents persist task summaries, decisions, and project facts. New sessions start with relevant memory injected, so context survives across runs (and is shared with external agents via MCP).
- **Exportable interface** — an MCP server exposes the tools, the memory, the full agent pipeline, and the system prompts. A CLI wraps everything for humans and scripts.

## Installation

```bash
git clone https://github.com/Hunterhghs/Fable-5.git
cd Fable-5
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[mcp]"        # or: pip install -e . (without the MCP server)
```

Requires Python 3.10+.

## Running without an API key

Fable does not require an API key. Point it at any local, key-less model runtime:

```bash
# Ollama (default: http://localhost:11434/v1, model qwen2.5-coder)
ollama pull qwen2.5-coder
fable run "Fix the failing tests" --provider ollama

# LM Studio (default: http://localhost:1234/v1)
fable run "Add docstrings to utils.py" --provider lmstudio --model your-loaded-model

# Any other OpenAI-compatible server (vLLM, llama.cpp, Reasonix local, ...)
fable run "your task" --provider openai-compatible \
    --base-url http://localhost:8000/v1 --model your-model
```

When no key is configured, the Authorization header is simply omitted. Everything else — the tool suite, memory store, MCP server, prompts, and CLI inspection commands (`fable tools|prompts|memory`) — never needed a key in the first place; only `fable run` and the MCP `run_agent` tool talk to a model at all.

To make key-less local mode the default for a project, put it in `fable.toml`:

```toml
[fable]
provider = "ollama"
model = "qwen2.5-coder"
```

## Configuration

For cloud providers, set an API key (checked in this order):

```bash
export FABLE_API_KEY=...        # works for any provider
export ANTHROPIC_API_KEY=...    # for provider=anthropic
export OPENAI_API_KEY=...       # for provider=openai
export DEEPSEEK_API_KEY=...     # for provider=deepseek
```

Optionally drop a `fable.toml` in your project root:

```toml
[fable]
provider = "anthropic"            # anthropic | openai | deepseek | ollama | lmstudio | openai-compatible
model = "claude-sonnet-4-5"
# base_url = "http://localhost:11434/v1"   # for openai-compatible endpoints
memory_backend = "sqlite"         # sqlite | json
```

Environment variables (`FABLE_PROVIDER`, `FABLE_MODEL`, `FABLE_BASE_URL`, ...) override the TOML file; CLI flags override both.

## Usage

### CLI

```bash
# Run the full agent pipeline on a task
fable run "Add input validation to the signup endpoint" --workspace ~/code/myapp

# Use a different provider/model
fable run "Fix the failing tests" --provider openai --model gpt-4o
fable run "Add error handling" --provider deepseek       # deepseek-chat by default
fable run "Refactor utils.py" --provider ollama          # local, no API key

# Inspect what Fable exports
fable tools                 # tool suite with schemas
fable prompts coder         # any system prompt (orchestrator|coder|verifier|architect)
fable memory recent         # what the agent remembers
fable memory search "api"   # keyword/FTS search over memory
```

### Python API

```python
from fable_agent import FableConfig, Orchestrator

config = FableConfig.load(workspace="~/code/myapp", provider="anthropic")
orchestrator = Orchestrator(config=config)
result = orchestrator.run_task("Add a /health endpoint that returns build info")
print(result.output)
```

You can also use the pieces independently — see [`examples/`](examples/):

- [`examples/run_task.py`](examples/run_task.py) — full pipeline, with live progress events
- [`examples/custom_tool.py`](examples/custom_tool.py) — registering your own tool
- [`examples/use_memory.py`](examples/use_memory.py) — reading/writing the memory store directly

## Exporting to other AI agents (MCP)

The MCP server is the interoperability layer. Start it with:

```bash
fable mcp --workspace /path/to/project
# or: python -m fable_agent.mcp_server --workspace /path/to/project
```

It speaks MCP over stdio and exposes:

| Kind | Name | What it does |
|---|---|---|
| Tool | `read_file`, `write_file`, `edit_file`, `list_dir`, `grep`, `glob`, `run_command` | Fable's full tooling suite, sandboxed to the workspace |
| Tool | `memory_remember`, `memory_recall` | Shared long-term memory — external agents read/write the same store Fable uses |
| Tool | `run_agent` | Hand a whole task to Fable's orchestrator (plan → code → verify) and get the report |
| Prompt | `fable_orchestrator`, `fable_coder`, `fable_verifier`, `fable_architect` | Fable's system prompts, so external agents can adopt its roles |

### Claude Code

```bash
claude mcp add fable -- fable mcp --workspace /path/to/project
```

### Cursor / Roo Code / other MCP clients

Add to your MCP config (e.g. `.cursor/mcp.json` or Roo Code's MCP settings):

```json
{
  "mcpServers": {
    "fable": {
      "command": "fable",
      "args": ["mcp", "--workspace", "/path/to/project"],
      "env": { "FABLE_API_KEY": "your-key-if-using-run_agent" }
    }
  }
}
```

### Reasonix and custom API scripts

Two integration paths, use whichever fits:

1. **As an MCP client** — point Reasonix at the stdio server exactly as above. Any MCP-capable runtime gets the tools, memory, and prompts with no adapter code.
2. **As a model endpoint** — if Reasonix exposes an OpenAI-compatible API, run Fable *on top of it*:

```bash
fable run "your task" --provider openai-compatible \
    --base-url https://your-reasonix-endpoint/v1 --model your-model
```

For fully custom scripts, the MCP Python SDK client works out of the box:

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

params = StdioServerParameters(command="fable", args=["mcp", "--workspace", "."])
async with stdio_client(params) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
        tools = await session.list_tools()
        result = await session.call_tool("grep", {"pattern": "TODO"})
```

### Exporting just the prompts

The system prompts are plain markdown in [`fable_agent/prompts/`](fable_agent/prompts/). Copy them, pipe them (`fable prompts coder > coder.md`), or fetch them over MCP as prompt resources. They are written to be model-agnostic.

## Project structure

```
fable_agent/
├── agents/
│   ├── base.py           # the core agent loop (model <-> tools)
│   ├── orchestrator.py   # planner + delegate/remember/recall tools
│   └── subagents.py      # Coder, Verifier, Architect with scoped toolsets
├── llm/
│   ├── base.py           # provider-agnostic Message/ToolCall/LLMResponse types
│   ├── anthropic_provider.py
│   ├── openai_provider.py  # OpenAI + any compatible endpoint
│   └── registry.py       # config -> provider factory
├── tools/
│   ├── base.py           # Tool, ToolRegistry, workspace sandboxing
│   ├── filesystem.py     # read / write / diff-edit / list
│   ├── search.py         # grep / glob
│   └── terminal.py       # shell execution with timeout + output caps
├── memory/
│   ├── store.py          # MemoryStore interface + MemoryEntry
│   ├── sqlite_store.py   # SQLite + FTS5 (default)
│   └── json_store.py     # human-readable JSON backend
├── prompts/              # exportable system prompts (markdown)
├── mcp_server/           # MCP export layer (stdio)
└── cli.py                # `fable` command
```

## Extending

**Add a tool** — subclass `Tool` (or `WorkspaceTool` for sandboxed file access), define `name`, `description`, a JSON-schema `parameters`, and `execute()`, then register it. See `examples/custom_tool.py`.

**Add a sub-agent** — write a prompt in `fable_agent/prompts/<role>.md`, add a class in `subagents.py` with the toolset it should have, and add it to `SUBAGENT_TYPES`. The orchestrator's `delegate` tool picks it up automatically.

**Add a provider** — implement `LLMProvider.chat()` (one method) in `fable_agent/llm/` and wire it into `registry.py`.

**Add a memory backend** — implement the four methods of `MemoryStore` and register it in `fable_agent/memory/__init__.py`.

## Development

```bash
pip install -e ".[dev]"
pytest
```

## License

MIT
