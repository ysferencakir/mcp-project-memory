from collections.abc import Mapping


PROJECT_INDEX_DOCUMENTS: tuple[str, ...] = (
    "state",
    "roadmap",
    "todo",
    "decisions",
    "handoff",
    "progress",
)


def _build_project_index(document_paths: Mapping[str, str]) -> str:
    links = [
        f"- [[{document_paths[name]}|{name.upper()}]]"
        for name in PROJECT_INDEX_DOCUMENTS
        if name in document_paths
    ]
    if not links:
        return ""
    return "\n## Project memory\n\n" + "\n".join(links) + "\n"


def build_default_templates(
    project_name: str,
    description: str = "",
    document_paths: Mapping[str, str] | None = None,
) -> dict[str, str]:
    """Build the default project-memory documents.

    Filenames are deliberately absent here. Logical names are resolved through
    ``ProjectMemoryConfig.documents`` by the service layer.
    """

    purpose = description.strip() or "Describe the project's purpose here."
    project_index = _build_project_index(document_paths or {})
    return {
        "project": (
            f"# {project_name}\n\n"
            "## Purpose\n\n"
            f"{purpose}\n\n"
            "## Scope\n\n"
            "- Define the current project scope.\n\n"
            "## Constraints\n\n"
            "- Record durable constraints here.\n"
            f"{project_index}"
        ),
        "state": (
            "# State\n\n"
            "## Current status\n\n"
            "Project memory initialized.\n\n"
            "## Completed\n\n"
            "- Project memory initialized.\n\n"
            "## Blockers\n\n"
            "- None recorded.\n\n"
            "## Next steps\n\n"
            "- Add the first concrete project task.\n"
        ),
        "roadmap": "# Roadmap\n\n## Now\n\n- Define the first milestone.\n",
        "decisions": (
            "# Decisions\n\n"
            "Record durable decisions with date, status, context, and rationale.\n"
        ),
        "todo": "# TODO\n\n- [ ] Define the first concrete task.\n",
        "handoff": (
            "# Handoff\n\n"
            "No agent handoff has been recorded yet.\n"
        ),
        "progress": (
            "# Progress\n\n"
            "Development checkpoints will be appended here.\n"
        ),
    }
