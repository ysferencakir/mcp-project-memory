import json
import logging
from collections.abc import Sequence
from functools import lru_cache
from importlib.metadata import version
from typing import Any
import os
from dotenv import load_dotenv
from mcp.server import Server
from mcp.types import (
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)

load_dotenv()

from . import project_tools, tools

# Load environment variables

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp-obsidian")

api_key = os.getenv("OBSIDIAN_API_KEY")
if not api_key:
    raise ValueError(f"OBSIDIAN_API_KEY environment variable required. Working directory: {os.getcwd()}")

SERVER_INSTRUCTIONS = """This server is the durable project-memory authority for the project selected by PROJECT_MEMORY_ROOT. At the start of every new conversation or meaningful project task, before planning or editing, call project_get_context and use the returned STATE, HANDOFF, ROADMAP, TODO, DECISIONS, PROGRESS, and session links as the source of truth; do not rely on chat history alone. Report missing, truncated, or omitted context explicitly.

Call project_init only when project_get_context confirms that memory is not initialized and initialization is intended; it preserves existing files. Keep all project-memory writes inside PROJECT_MEMORY_ROOT. Prefer project_create_file_safe for new notes. Treat overwrite and delete tools as destructive and require clear user intent. Do not write concurrently with another agent using the same project root.

Before completing meaningful work or handing off, verify the work, reconcile ROADMAP and TODO with evidence, leave partial or uncertain items open, read changed planning documents back, and call project_checkpoint with an honest summary, completed work, changed files, verification, decisions, pending approvals, blockers, and next steps. Do not claim that context was persisted unless the checkpoint succeeds and returns a session path. A simple read-only answer that does not advance the project does not require a checkpoint."""

SERVER_VERSION = version("mcp-obsidian")

app = Server(
    "mcp-project-memory",
    version=SERVER_VERSION,
    instructions=SERVER_INSTRUCTIONS,
)

tool_handlers = {}
def add_tool_handler(tool_class: tools.ToolHandler):
    global tool_handlers

    tool_handlers[tool_class.name] = tool_class

def get_tool_handler(name: str) -> tools.ToolHandler | None:
    if name not in tool_handlers:
        return None
    
    return tool_handlers[name]

add_tool_handler(tools.ListFilesInDirToolHandler())
add_tool_handler(tools.ListFilesInVaultToolHandler())
add_tool_handler(tools.GetFileContentsToolHandler())
add_tool_handler(tools.SearchToolHandler())
add_tool_handler(tools.PatchContentToolHandler())
add_tool_handler(tools.AppendContentToolHandler())
add_tool_handler(tools.PutContentToolHandler())
add_tool_handler(tools.DeleteFileToolHandler())
add_tool_handler(tools.ComplexSearchToolHandler())
add_tool_handler(tools.SearchByTagToolHandler())
add_tool_handler(tools.GetFrontmatterToolHandler())
add_tool_handler(tools.BatchGetFileContentsToolHandler())
add_tool_handler(tools.PeriodicNotesToolHandler())
add_tool_handler(tools.RecentPeriodicNotesToolHandler())
add_tool_handler(tools.RecentChangesToolHandler())
add_tool_handler(project_tools.CreateProjectFileSafeToolHandler())
add_tool_handler(project_tools.InitProjectToolHandler())
add_tool_handler(project_tools.GetProjectContextToolHandler())
add_tool_handler(project_tools.CheckpointProjectToolHandler())

@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""

    return [th.get_tool_description() for th in tool_handlers.values()]

@app.call_tool()
async def call_tool(name: str, arguments: Any) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
    """Handle tool calls for command line run."""
    
    if not isinstance(arguments, dict):
        raise RuntimeError("arguments must be dictionary")


    tool_handler = get_tool_handler(name)
    if not tool_handler:
        raise ValueError(f"Unknown tool: {name}")

    try:
        return tool_handler.run_tool(arguments)
    except Exception as e:
        logger.error(str(e))
        raise RuntimeError(f"Caught Exception. Error: {str(e)}")


async def main():

    # Import here to avoid issues with event loops
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )
