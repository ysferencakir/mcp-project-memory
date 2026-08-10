import json
import os
from dataclasses import dataclass, field
from typing import Mapping


DEFAULT_PROJECT_DOCUMENTS: dict[str, str] = {
    "project": "PROJECT.md",
    "state": "STATE.md",
    "roadmap": "ROADMAP.md",
    "decisions": "DECISIONS.md",
    "todo": "TODO.md",
    "handoff": "HANDOFF.md",
    "progress": "PROGRESS.md",
}

DEFAULT_CONTEXT_ORDER: tuple[str, ...] = (
    "project",
    "state",
    "handoff",
    "roadmap",
    "todo",
    "decisions",
    "progress",
)


@dataclass(frozen=True)
class ProjectMemoryConfig:
    """Configuration for the project-level memory layer.

    A vault represents one project by default, so an empty ``root`` means the
    vault root. Users who keep project memory in a subdirectory can set
    ``PROJECT_MEMORY_ROOT``.
    """

    root: str = ""
    documents: Mapping[str, str] = field(
        default_factory=lambda: DEFAULT_PROJECT_DOCUMENTS.copy()
    )

    @classmethod
    def from_env(cls) -> "ProjectMemoryConfig":
        root = os.getenv("PROJECT_MEMORY_ROOT", "").strip()
        documents = DEFAULT_PROJECT_DOCUMENTS.copy()
        raw_documents = os.getenv("PROJECT_MEMORY_DOCUMENTS")

        if raw_documents:
            try:
                parsed = json.loads(raw_documents)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    "PROJECT_MEMORY_DOCUMENTS must be a valid JSON object"
                ) from exc

            if not isinstance(parsed, dict) or not all(
                isinstance(key, str) and isinstance(value, str)
                for key, value in parsed.items()
            ):
                raise ValueError(
                    "PROJECT_MEMORY_DOCUMENTS must map string names to string paths"
                )

            documents.update(parsed)

        return cls(root=root, documents=documents)
