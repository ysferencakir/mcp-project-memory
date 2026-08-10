import json
import os
from collections.abc import Sequence

from mcp.types import EmbeddedResource, ImageContent, TextContent, Tool

from . import obsidian
from .config import ProjectMemoryConfig
from .project_memory import CheckpointData, ProjectMemory
from .tools import ToolHandler


def _build_service() -> ProjectMemory:
    api_key = os.getenv("OBSIDIAN_API_KEY", "")
    if not api_key:
        raise RuntimeError("OBSIDIAN_API_KEY environment variable required")

    api = obsidian.Obsidian(
        api_key=api_key,
        host=os.getenv("OBSIDIAN_HOST", "127.0.0.1"),
    )
    return ProjectMemory(api, ProjectMemoryConfig.from_env())


def _json_result(payload: dict) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
    return [TextContent(type="text", text=json.dumps(payload, indent=2))]


class CreateProjectFileSafeToolHandler(ToolHandler):
    def __init__(self):
        super().__init__("project_create_file_safe")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description=(
                "Create a new Markdown file inside the configured project memory root "
                "without overwriting a file that already exists. Paths are relative "
                "to the project root. This is sequentially safe, but the Obsidian "
                "Local REST API cannot provide atomic create-only behavior across "
                "concurrent server processes."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "relative_path": {
                        "type": "string",
                        "description": (
                            "Markdown path relative to the configured project memory "
                            "root, for example 'STATE.md' or 'sessions/2026-08-10.md'."
                        ),
                        "format": "path",
                    },
                    "content": {
                        "type": "string",
                        "description": "Initial Markdown content for the new file.",
                    },
                },
                "required": ["relative_path", "content"],
            },
        )

    def run_tool(
        self, args: dict
    ) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        if "relative_path" not in args or "content" not in args:
            raise RuntimeError("relative_path and content arguments required")

        service = _build_service()
        result = service.create_file_safe(args["relative_path"], args["content"])

        return _json_result({"status": result.status, "path": result.path})


class InitProjectToolHandler(ToolHandler):
    def __init__(self):
        super().__init__("project_init")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description=(
                "Initialize the configured project vault with the default Markdown "
                "memory documents. Existing files are preserved and reported."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "project_name": {
                        "type": "string",
                        "description": "Human-readable project name.",
                    },
                    "description": {
                        "type": "string",
                        "description": "Optional initial project purpose.",
                        "default": "",
                    },
                },
                "required": ["project_name"],
            },
        )

    def run_tool(
        self, args: dict
    ) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        if "project_name" not in args:
            raise RuntimeError("project_name argument required")
        result = _build_service().init_project(
            args["project_name"], args.get("description", "")
        )
        return _json_result(
            {
                "created": result.created,
                "already_exists": result.already_exists,
                "skipped": result.skipped,
            }
        )


class GetProjectContextToolHandler(ToolHandler):
    def __init__(self):
        super().__init__("project_get_context")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description=(
                "Load configured project-memory documents in deterministic order, "
                "including source paths, missing-file status, and truncation details."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "include": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": (
                            "Optional logical document names to load. Defaults to all "
                            "configured documents."
                        ),
                    },
                    "max_chars": {
                        "type": "integer",
                        "description": "Maximum total document characters to return.",
                        "default": 50000,
                        "minimum": 1,
                        "maximum": 200000,
                    },
                },
            },
        )

    def run_tool(
        self, args: dict
    ) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        result = _build_service().get_context(
            include=args.get("include"),
            max_chars=args.get("max_chars", 50_000),
        )
        return _json_result(result.to_dict())


class CheckpointProjectToolHandler(ToolHandler):
    _list_fields = (
        "completed",
        "blockers",
        "decisions",
        "pending_approvals",
        "verification",
        "files_changed",
    )

    def __init__(self):
        super().__init__("project_checkpoint")

    def get_tool_description(self) -> Tool:
        array_schema = {"type": "array", "items": {"type": "string"}}
        return Tool(
            name=self.name,
            description=(
                "Record an append-only session and update the current STATE, HANDOFF, "
                "and PROGRESS documents for the next agent. Run project_init first."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "agent_id": {"type": "string"},
                    "summary": {"type": "string"},
                    "next_steps": array_schema,
                    "completed": array_schema,
                    "blockers": array_schema,
                    "decisions": array_schema,
                    "pending_approvals": array_schema,
                    "verification": array_schema,
                    "files_changed": array_schema,
                    "session_id": {
                        "type": "string",
                        "description": (
                            "Optional stable identifier containing letters, numbers, "
                            "underscores, or hyphens."
                        ),
                    },
                },
                "required": ["agent_id", "summary", "next_steps"],
            },
        )

    def run_tool(
        self, args: dict
    ) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        missing = [
            name for name in ("agent_id", "summary", "next_steps") if name not in args
        ]
        if missing:
            raise RuntimeError(f"required arguments missing: {', '.join(missing)}")

        data = CheckpointData(
            agent_id=args["agent_id"],
            summary=args["summary"],
            next_steps=args["next_steps"],
            completed=args.get("completed", ()),
            blockers=args.get("blockers", ()),
            decisions=args.get("decisions", ()),
            pending_approvals=args.get("pending_approvals", ()),
            verification=args.get("verification", ()),
            files_changed=args.get("files_changed", ()),
            session_id=args.get("session_id"),
        )
        result = _build_service().checkpoint(data)
        return _json_result(
            {
                "session_id": result.session_id,
                "timestamp": result.timestamp,
                "session_path": result.session_path,
                "updated_paths": result.updated_paths,
            }
        )
