import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Literal, Sequence
from urllib.parse import unquote
from uuid import uuid4

from .config import DEFAULT_CONTEXT_ORDER, ProjectMemoryConfig
from .obsidian import Obsidian, ObsidianApiError
from .project_templates import build_default_templates


class ProjectPathError(ValueError):
    """Raised when a project path could escape or ambiguously address its root."""


@dataclass(frozen=True)
class CreateFileResult:
    status: Literal["created", "already_exists"]
    path: str


class CheckpointConflictError(RuntimeError):
    """Raised when an append-only checkpoint session already exists."""


@dataclass(frozen=True)
class InitProjectResult:
    created: list[str]
    already_exists: list[str]
    skipped: list[str]


@dataclass(frozen=True)
class ContextDocument:
    name: str
    path: str
    status: Literal["loaded", "missing"]
    content: str | None
    truncated: bool = False


@dataclass(frozen=True)
class ProjectContextResult:
    documents: list[ContextDocument]
    omitted: list[str]
    max_chars: int
    used_chars: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CheckpointData:
    agent_id: str
    summary: str
    next_steps: Sequence[str]
    completed: Sequence[str] = ()
    blockers: Sequence[str] = ()
    decisions: Sequence[str] = ()
    pending_approvals: Sequence[str] = ()
    verification: Sequence[str] = ()
    files_changed: Sequence[str] = ()
    session_id: str | None = None


@dataclass(frozen=True)
class CheckpointResult:
    session_id: str
    timestamp: str
    session_path: str
    updated_paths: list[str]


def validate_relative_path(path: str, *, allow_empty: bool = False) -> str:
    """Validate and normalize a vault-relative POSIX path."""

    if not isinstance(path, str):
        raise ProjectPathError("path must be a string")
    if path == "" and allow_empty:
        return ""
    if not path or path != path.strip():
        raise ProjectPathError("path must not be empty or contain outer whitespace")
    if "\\" in path:
        raise ProjectPathError("path must use '/' separators")
    if unquote(path) != path:
        raise ProjectPathError("percent-encoded paths are not allowed")
    if path.startswith("/") or path.endswith("/"):
        raise ProjectPathError("path must be relative and identify a file")
    if any(ord(character) < 32 for character in path):
        raise ProjectPathError("path must not contain control characters")

    parts = path.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise ProjectPathError("path must not contain empty, '.' or '..' segments")

    return "/".join(parts)


class ProjectMemory:
    """Project-level rules layered on top of the existing Obsidian client."""

    def __init__(self, client: Obsidian, config: ProjectMemoryConfig):
        self.client = client
        self.config = config

    def resolve_path(self, relative_path: str) -> str:
        relative = validate_relative_path(relative_path)
        if not relative.lower().endswith(".md"):
            raise ProjectPathError("project memory files must use the .md extension")

        root = validate_relative_path(self.config.root, allow_empty=True)
        return f"{root}/{relative}" if root else relative

    def resolve_document_path(self, name: str) -> str:
        try:
            relative_path = self.config.documents[name]
        except KeyError as exc:
            raise ValueError(f"unknown project document: {name}") from exc
        return self.resolve_path(relative_path)

    def create_file_safe(self, relative_path: str, content: str) -> CreateFileResult:
        """Create a Markdown file unless it already exists.

        The Local REST API has no atomic create-only operation. This method
        prevents normal sequential overwrites by checking first, but callers
        must not treat it as safe against concurrent processes racing between
        GET and PUT.
        """

        if not isinstance(content, str):
            raise ValueError("content must be a string")

        vault_path = self.resolve_path(relative_path)

        try:
            self.client.get_file_contents(vault_path)
        except ObsidianApiError as exc:
            if exc.status_code != 404:
                raise
        else:
            return CreateFileResult(status="already_exists", path=vault_path)

        self.client.put_content(vault_path, content)
        return CreateFileResult(status="created", path=vault_path)

    def init_project(self, project_name: str, description: str = "") -> InitProjectResult:
        if not isinstance(project_name, str) or not project_name.strip():
            raise ValueError("project_name must be a non-empty string")
        if not isinstance(description, str):
            raise ValueError("description must be a string")

        templates = build_default_templates(project_name.strip(), description)
        created: list[str] = []
        already_exists: list[str] = []
        skipped: list[str] = []

        for name, content in templates.items():
            relative_path = self.config.documents.get(name)
            if relative_path is None:
                skipped.append(name)
                continue

            result = self.create_file_safe(relative_path, content)
            if result.status == "created":
                created.append(result.path)
            else:
                already_exists.append(result.path)

        return InitProjectResult(
            created=created,
            already_exists=already_exists,
            skipped=skipped,
        )

    def get_context(
        self,
        include: Sequence[str] | None = None,
        max_chars: int = 50_000,
    ) -> ProjectContextResult:
        if (
            isinstance(max_chars, bool)
            or not isinstance(max_chars, int)
            or not 1 <= max_chars <= 200_000
        ):
            raise ValueError("max_chars must be an integer between 1 and 200000")

        if include is None:
            names = [
                name for name in DEFAULT_CONTEXT_ORDER if name in self.config.documents
            ]
            names.extend(
                name for name in self.config.documents if name not in DEFAULT_CONTEXT_ORDER
            )
        else:
            names = list(include)
        if not all(isinstance(name, str) for name in names):
            raise ValueError("include must contain only document names")
        names = list(dict.fromkeys(names))

        unknown = [name for name in names if name not in self.config.documents]
        if unknown:
            raise ValueError(f"unknown project documents: {', '.join(unknown)}")

        documents: list[ContextDocument] = []
        omitted: list[str] = []
        used_chars = 0

        for index, name in enumerate(names):
            if used_chars >= max_chars:
                omitted.extend(names[index:])
                break

            path = self.resolve_document_path(name)
            try:
                content = self.client.get_file_contents(path)
            except ObsidianApiError as exc:
                if exc.status_code != 404:
                    raise
                documents.append(
                    ContextDocument(
                        name=name,
                        path=path,
                        status="missing",
                        content=None,
                    )
                )
                continue

            remaining = max_chars - used_chars
            truncated = len(content) > remaining
            selected_content = content[:remaining]
            used_chars += len(selected_content)
            documents.append(
                ContextDocument(
                    name=name,
                    path=path,
                    status="loaded",
                    content=selected_content,
                    truncated=truncated,
                )
            )

        return ProjectContextResult(
            documents=documents,
            omitted=omitted,
            max_chars=max_chars,
            used_chars=used_chars,
        )

    def checkpoint(
        self,
        data: CheckpointData,
        *,
        now: datetime | None = None,
    ) -> CheckpointResult:
        self._validate_checkpoint_data(data)
        current_time = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
        timestamp = current_time.isoformat(timespec="seconds").replace("+00:00", "Z")
        filename_timestamp = current_time.strftime("%Y-%m-%dT%H-%M-%SZ")
        session_id = data.session_id or uuid4().hex[:12]

        if not re.fullmatch(r"[A-Za-z0-9_-]+", session_id):
            raise ValueError(
                "session_id may contain only letters, numbers, '_' and '-'"
            )

        session_relative_path = f"sessions/{filename_timestamp}-{session_id}.md"
        session_content = self._build_session_content(data, timestamp, session_id)
        session_result = self.create_file_safe(session_relative_path, session_content)
        if session_result.status != "created":
            raise CheckpointConflictError(
                f"checkpoint session already exists: {session_result.path}"
            )

        state_path = self.resolve_document_path("state")
        handoff_path = self.resolve_document_path("handoff")
        progress_path = self.resolve_document_path("progress")
        updated_paths = [state_path, handoff_path]

        self.client.put_content(
            state_path,
            self._build_state_content(data, timestamp, session_result.path),
        )
        self.client.put_content(
            handoff_path,
            self._build_handoff_content(data, timestamp, session_result.path),
        )
        if data.decisions:
            decisions_path = self.resolve_document_path("decisions")
            self.client.append_content(
                decisions_path,
                self._build_decisions_entry(data, timestamp, session_result.path),
            )
            updated_paths.append(decisions_path)
        self.client.append_content(
            progress_path,
            self._build_progress_entry(data, timestamp, session_result.path),
        )
        updated_paths.append(progress_path)

        return CheckpointResult(
            session_id=session_id,
            timestamp=timestamp,
            session_path=session_result.path,
            updated_paths=updated_paths,
        )

    @staticmethod
    def _validate_checkpoint_data(data: CheckpointData) -> None:
        if not isinstance(data.agent_id, str) or not data.agent_id.strip():
            raise ValueError("agent_id must be a non-empty string")
        if not isinstance(data.summary, str) or not data.summary.strip():
            raise ValueError("summary must be a non-empty string")

        fields: dict[str, Sequence[str]] = {
            "next_steps": data.next_steps,
            "completed": data.completed,
            "blockers": data.blockers,
            "decisions": data.decisions,
            "pending_approvals": data.pending_approvals,
            "verification": data.verification,
            "files_changed": data.files_changed,
        }
        for name, values in fields.items():
            if isinstance(values, str) or not all(
                isinstance(value, str) and bool(value.strip()) for value in values
            ):
                raise ValueError(f"{name} must be a list of non-empty strings")
        if not data.next_steps:
            raise ValueError("next_steps must contain at least one item")

    @staticmethod
    def _bullets(values: Sequence[str], empty: str = "None recorded.") -> str:
        if not values:
            return f"- {empty}\n"
        return "".join(f"- {value.strip()}\n" for value in values)

    @classmethod
    def _build_session_content(
        cls, data: CheckpointData, timestamp: str, session_id: str
    ) -> str:
        return (
            f"# Session {session_id}\n\n"
            f"- Agent: `{data.agent_id.strip()}`\n"
            f"- Timestamp: `{timestamp}`\n\n"
            f"## Summary\n\n{data.summary.strip()}\n\n"
            f"## Completed\n\n{cls._bullets(data.completed)}\n"
            f"## Files changed\n\n{cls._bullets(data.files_changed)}\n"
            f"## Verification\n\n{cls._bullets(data.verification)}\n"
            f"## Decisions\n\n{cls._bullets(data.decisions)}\n"
            f"## Pending approvals\n\n{cls._bullets(data.pending_approvals)}\n"
            f"## Blockers\n\n{cls._bullets(data.blockers)}\n"
            f"## Next steps\n\n{cls._bullets(data.next_steps)}"
        )

    @classmethod
    def _build_state_content(
        cls, data: CheckpointData, timestamp: str, session_path: str
    ) -> str:
        return (
            "# State\n\n"
            f"_Last checkpoint: `{timestamp}` by `{data.agent_id.strip()}`._\n\n"
            f"Session: [[{session_path}]]\n\n"
            f"## Current status\n\n{data.summary.strip()}\n\n"
            f"## Completed\n\n{cls._bullets(data.completed)}\n"
            f"## Blockers\n\n{cls._bullets(data.blockers)}\n"
            f"## Next steps\n\n{cls._bullets(data.next_steps)}"
        )

    @classmethod
    def _build_handoff_content(
        cls, data: CheckpointData, timestamp: str, session_path: str
    ) -> str:
        return (
            "# Handoff\n\n"
            f"- From: `{data.agent_id.strip()}`\n"
            f"- Timestamp: `{timestamp}`\n"
            f"- Session: [[{session_path}]]\n\n"
            f"## Summary\n\n{data.summary.strip()}\n\n"
            f"## Next steps\n\n{cls._bullets(data.next_steps)}\n"
            f"## Blockers\n\n{cls._bullets(data.blockers)}\n"
            f"## Pending approvals\n\n{cls._bullets(data.pending_approvals)}"
        )

    @classmethod
    def _build_progress_entry(
        cls, data: CheckpointData, timestamp: str, session_path: str
    ) -> str:
        return (
            f"\n## {timestamp} — {data.agent_id.strip()}\n\n"
            f"{data.summary.strip()}\n\n"
            f"Session: [[{session_path}]]\n\n"
            f"### Completed\n\n{cls._bullets(data.completed)}\n"
            f"### Next steps\n\n{cls._bullets(data.next_steps)}"
        )

    @classmethod
    def _build_decisions_entry(
        cls, data: CheckpointData, timestamp: str, session_path: str
    ) -> str:
        return (
            f"\n## {timestamp} — {data.agent_id.strip()}\n\n"
            f"Session: [[{session_path}]]\n\n"
            f"{cls._bullets(data.decisions)}"
        )
