# mcp-project-memory

An MCP server for persistent project context and agent handoff, built on top of
the existing Obsidian Local REST API integration.

The project is evolving from `mcp-obsidian`. The existing Obsidian tools and
the `mcp-obsidian` command remain available while project-level `project_*`
tools are added alongside them.

<a href="https://glama.ai/mcp/servers/3wko1bhuek"><img width="380" height="200" src="https://glama.ai/mcp/servers/3wko1bhuek/badge" alt="server for Obsidian MCP server" /></a>

## Components

### Tools

The server currently exposes the following existing Obsidian tools:

- `obsidian_list_files_in_vault`
- `obsidian_list_files_in_dir`
- `obsidian_get_file_contents`
- `obsidian_batch_get_file_contents`
- `obsidian_simple_search`
- `obsidian_complex_search`
- `obsidian_search_by_tag`
- `obsidian_get_frontmatter`
- `obsidian_patch_content`
- `obsidian_append_content`
- `obsidian_put_content`
- `obsidian_delete_file`
- `obsidian_get_periodic_note`
- `obsidian_get_recent_periodic_notes`
- `obsidian_get_recent_changes`

Project-memory tools:

- `project_create_file_safe`: Creates a Markdown file inside the configured
  project root without overwriting a file that already exists in normal
  sequential use.
- `project_init`: Creates the configured project-memory documents from small
  default templates while preserving files that already exist.
- `project_get_context`: Loads project documents in continuity-first order and
  reports source paths, missing files, truncation, and omitted documents.
- `project_checkpoint`: Creates an append-only session record, replaces the
  current `STATE` and `HANDOFF` views, appends an entry to `PROGRESS`, and
  appends approved `decisions` to `DECISIONS`.

`obsidian_put_content` can completely overwrite an existing file. Prefer the
safe project tool when creating project-memory documents.

### Example prompts

Its good to first instruct Claude to use Obsidian. Then it will always call the tool.

The use prompts like this:
- Get the contents of the last architecture call note and summarize them
- Search for all files where Azure CosmosDb is mentioned and quickly explain to me the context in which it is mentioned
- Summarize the last meeting notes and put them into a new note 'summary meeting.md'. Add an introduction so that I can send it via email.

## Configuration

### Obsidian REST API Key

Never commit the Obsidian API key. For the reproducible Windows setup where
Codex and Claude Code share the same vault, follow the
[Main Computer Setup](docs/MAIN_COMPUTER_SETUP.md). It uses client environment
forwarding and includes configuration templates for both clients.

There are two basic ways to provide the environment to the server:

1. Forward environment variables from a local MCP client configuration. Keep
   the configuration user-local if it contains the key:

```json
{
  "mcp-obsidian": {
    "command": "uvx",
    "args": [
      "mcp-obsidian"
    ],
    "env": {
      "OBSIDIAN_API_KEY": "<your_api_key_here>",
      "OBSIDIAN_HOST": "<your_obsidian_host>",
      "OBSIDIAN_PORT": "<your_obsidian_port>",
      "PROJECT_MEMORY_ROOT": ""
    }
  }
}
```
Sometimes Claude has issues detecting the location of uv / uvx. You can use `which uvx` to find and paste the full path in above config in such cases.

2. Create a Git-ignored `.env` file in the server working directory with the
   following variables:

```
OBSIDIAN_API_KEY=your_api_key_here
OBSIDIAN_HOST=your_obsidian_host
OBSIDIAN_PORT=your_obsidian_port
OBSIDIAN_PROTOCOL=https
PROJECT_MEMORY_ROOT=
```

Note:
- You can find the API key in the Obsidian plugin config
- Default port is 27124 if not specified
- Default host is 127.0.0.1 if not specified
- Default protocol is HTTPS
- One vault represents one project by default. An empty
  `PROJECT_MEMORY_ROOT` stores project-memory documents at the vault root.
- Set `PROJECT_MEMORY_ROOT` to a vault-relative subdirectory only when needed.

### Project document names

Default logical document names include `PROJECT.md`, `STATE.md`, `ROADMAP.md`,
`DECISIONS.md`, `TODO.md`, `HANDOFF.md`, and `PROGRESS.md`. They are defined at
the configuration boundary rather than in project-memory business logic.
Newly initialized `PROJECT.md` files contain an Obsidian project-memory index
whose links use the configured vault-relative paths, including
`PROJECT_MEMORY_ROOT` and document-name overrides.

You can override or add names with a JSON object:

```text
PROJECT_MEMORY_DOCUMENTS={"state":"status/CURRENT.md","progress":"PROGRESS.md"}
```

The project-memory layer only accepts relative Markdown paths, rejects `..`,
absolute paths, backslashes, ambiguous path segments, and percent-encoded
paths.

### Safe creation limitation

The Obsidian Local REST API does not provide an atomic create-only operation.
`project_create_file_safe` performs a read-before-write check and will not
overwrite an already observed file. Two independent MCP processes could still
race between that check and the write. V1 assumes Claude Code and Codex work
sequentially and leave handoffs rather than writing the same file concurrently.

### Recommended agent workflow

Initialize a new project vault once:

```json
{
  "tool": "project_init",
  "arguments": {
    "project_name": "mcp-project-memory",
    "description": "Persistent project context shared by coding agents"
  }
}
```

At the beginning of an agent session, call `project_get_context`. Its default
order is `project`, `state`, `handoff`, `roadmap`, `todo`, `decisions`, then
`progress`. The response identifies missing, truncated, and omitted documents
instead of silently hiding them.

At the end of a meaningful work session, call `project_checkpoint`:

```json
{
  "agent_id": "codex",
  "summary": "Implemented the first project-memory tools.",
  "completed": ["Added project initialization and context loading."],
  "files_changed": ["src/mcp_obsidian/project_memory.py"],
  "verification": ["All tests passed."],
  "decisions": ["Use one project per vault."],
  "pending_approvals": [],
  "blockers": [],
  "next_steps": ["Run the live Obsidian smoke test on the main computer."]
}
```

Checkpoint writes an immutable `sessions/...md` record first. It then updates
the current state and handoff files, appends approved decisions to
`DECISIONS.md`, and appends a human-readable entry to `PROGRESS.md`, making
development visible from Obsidian. Items in `pending_approvals` are kept in the
session and handoff but are not promoted into durable decisions. Checkpoint is
intentionally not a multi-file atomic transaction; if a later write fails, the
session file remains as the recovery record.

Before checkpointing, reconcile `ROADMAP` and `TODO` with verified results and
read the changed planning documents back. Mark only unambiguous completed
items. `project_checkpoint` intentionally does not infer checklist completion
from free-form summary text or mutate planning documents automatically.

### Docker

The MCP server can run as a Linux container while Obsidian remains on the host.
The image uses pinned Python and uv image versions, installs from `uv.lock`,
runs as a non-root user, and receives the API key only at runtime. Because the
Obsidian Local REST API listens on host loopback, Docker Desktop uses
`host.docker.internal`; Linux Docker Engine uses host networking. See
[Docker setup](docs/DOCKER_SETUP.md) for build commands, networking details,
security boundaries, and Codex/Claude examples.

## Quickstart

### Install

#### Obsidian REST API

You need the Obsidian REST API community plugin running: https://github.com/coddingtonbear/obsidian-local-rest-api

V1's complete 15-tool compatibility baseline is pinned to **Local REST API
4.1.7**. It was verified live with Obsidian 1.13.4. Install and enable that
plugin version in the settings and copy the API key.

Local REST API 5.x removes the periodic-note REST endpoints used by the two
existing periodic tools and changes other API behavior. The four
`project_*` tools may use only basic vault operations, but 5.x is not the
supported full-tool baseline until a separate compatibility slice is designed
and tested. Do not blindly upgrade the plugin on the V1 installation.

#### Claude Desktop

On MacOS: `~/Library/Application\ Support/Claude/claude_desktop_config.json`

On Windows: `%APPDATA%/Claude/claude_desktop_config.json`

<details>
  <summary>Development/Unpublished Servers Configuration</summary>
  
```json
{
  "mcpServers": {
    "mcp-obsidian": {
      "command": "uv",
      "args": [
        "--directory",
        "<dir_to>/mcp-obsidian",
        "run",
        "mcp-obsidian"
      ],
      "env": {
        "OBSIDIAN_API_KEY": "<your_api_key_here>",
        "OBSIDIAN_HOST": "<your_obsidian_host>",
        "OBSIDIAN_PORT": "<your_obsidian_port>"
      }
    }
  }
}
```
</details>

<details>
  <summary>Published Servers Configuration</summary>
  
```json
{
  "mcpServers": {
    "mcp-obsidian": {
      "command": "uvx",
      "args": [
        "mcp-obsidian"
      ],
      "env": {
        "OBSIDIAN_API_KEY": "<YOUR_OBSIDIAN_API_KEY>",
        "OBSIDIAN_HOST": "<your_obsidian_host>",
        "OBSIDIAN_PORT": "<your_obsidian_port>"
      }
    }
  }
}
```
</details>

## Development

### Building

To prepare the package for distribution:

1. Sync dependencies and update lockfile:
```bash
uv sync
```

Run the test suite with the locked environment:

```bash
uv run --frozen pytest
```

Before using a real project vault, follow the dedicated
[Live Obsidian Smoke Test](docs/LIVE_OBSIDIAN_SMOKE_TEST.md) against a new empty
vault.

For a shared Claude Code/Codex installation, use the
[Main Computer Setup](docs/MAIN_COMPUTER_SETUP.md) and adopt the
[Agent Memory Protocol](docs/AGENT_MEMORY_PROTOCOL.md).

### Agent handoff demo

[`examples/agent-handoff-demo`](examples/agent-handoff-demo) is a deliberately
small Python CLI project for testing continuity across fresh Codex and Claude
Code sessions. Its first session initializes Obsidian memory under
`PROJECT_MEMORY_ROOT=agent-handoff-demo`; subsequent agents implement small
roadmap slices after loading that persisted context.

### Debugging

Since MCP servers run over stdio, debugging can be challenging. For the best debugging
experience, we strongly recommend using the [MCP Inspector](https://github.com/modelcontextprotocol/inspector).

You can launch the MCP Inspector via [`npm`](https://docs.npmjs.com/downloading-and-installing-node-js-and-npm) with this command:

```bash
npx @modelcontextprotocol/inspector uv --directory /path/to/mcp-obsidian run mcp-obsidian
```

Upon launching, the Inspector will display a URL that you can access in your browser to begin debugging.

You can also watch the server logs with this command:

```bash
tail -n 20 -f ~/Library/Logs/Claude/mcp-server-mcp-obsidian.log
```
