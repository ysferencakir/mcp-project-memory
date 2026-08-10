"""JSON-backed task storage for the agent handoff demo."""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


class StorageError(RuntimeError):
    """Raised when the task file cannot be read or validated."""


class TaskNotFoundError(StorageError):
    """Raised when a requested task identifier does not exist."""


@dataclass(frozen=True, slots=True)
class Task:
    id: int
    title: str
    completed: bool = False


class TaskStore:
    """Persist tasks as JSON, replacing the data file atomically on writes."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def list_tasks(self) -> list[Task]:
        if not self.path.exists():
            return []

        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise StorageError(f"could not read {self.path}: {exc}") from exc

        return self._parse_tasks(payload)

    def add(self, title: str) -> Task:
        tasks = self.list_tasks()
        task = Task(
            id=max((existing.id for existing in tasks), default=0) + 1,
            title=title,
        )
        self._write(tasks + [task])
        return task

    def complete(self, task_id: int) -> Task:
        tasks = self.list_tasks()
        for index, task in enumerate(tasks):
            if task.id != task_id:
                continue
            completed_task = Task(task.id, task.title, completed=True)
            if not task.completed:
                tasks[index] = completed_task
                self._write(tasks)
            return completed_task
        raise TaskNotFoundError(f"task not found: {task_id}")

    def _parse_tasks(self, payload: Any) -> list[Task]:
        if not isinstance(payload, dict) or set(payload) != {"tasks"}:
            raise StorageError("task file must be an object containing only 'tasks'")
        if not isinstance(payload["tasks"], list):
            raise StorageError("'tasks' must be a list")

        tasks: list[Task] = []
        seen_ids: set[int] = set()
        for index, item in enumerate(payload["tasks"]):
            if not isinstance(item, dict) or set(item) != {"id", "title", "completed"}:
                raise StorageError(f"task at index {index} has an invalid shape")
            task_id = item["id"]
            title = item["title"]
            completed = item["completed"]
            if isinstance(task_id, bool) or not isinstance(task_id, int) or task_id < 1:
                raise StorageError(f"task at index {index} has an invalid id")
            if not isinstance(title, str) or not title.strip():
                raise StorageError(f"task at index {index} has an invalid title")
            if not isinstance(completed, bool):
                raise StorageError(f"task at index {index} has an invalid completed value")
            if task_id in seen_ids:
                raise StorageError(f"duplicate task id: {task_id}")
            seen_ids.add(task_id)
            tasks.append(Task(task_id, title, completed))
        return tasks

    def _write(self, tasks: list[Task]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                "w",
                encoding="utf-8",
                dir=self.path.parent,
                prefix=f".{self.path.name}.",
                suffix=".tmp",
                delete=False,
            ) as temporary:
                temporary_path = Path(temporary.name)
                json.dump(
                    {"tasks": [asdict(task) for task in tasks]},
                    temporary,
                    ensure_ascii=False,
                    indent=2,
                )
                temporary.write("\n")
                temporary.flush()
                os.fsync(temporary.fileno())
            os.replace(temporary_path, self.path)
        except OSError as exc:
            raise StorageError(f"could not write {self.path}: {exc}") from exc
        finally:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)
