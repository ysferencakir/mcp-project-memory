"""Command-line entry point for the agent handoff demo."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import TextIO

if __package__:
    from .storage import StorageError, TaskStore
else:
    from storage import StorageError, TaskStore


def _configure_utf8_output(*streams: TextIO) -> None:
    """Use UTF-8 for real text streams while leaving test doubles untouched."""
    for stream in streams:
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agent-handoff-demo",
        description="A tiny task CLI developed through sequential agent handoffs.",
    )
    parser.add_argument(
        "--data-file",
        type=Path,
        default=Path("tasks.json"),
        help="JSON task file (default: tasks.json).",
    )
    subcommands = parser.add_subparsers(dest="command", required=True)
    subcommands.add_parser("status", help="Verify that the demo CLI is ready.")
    add_parser = subcommands.add_parser("add", help="Create a task.")
    add_parser.add_argument("title", help="Task title.")
    subcommands.add_parser("list", help="List tasks.")
    complete_parser = subcommands.add_parser("complete", help="Complete a task.")
    complete_parser.add_argument("id", type=int, help="Task identifier.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    _configure_utf8_output(sys.stdout, sys.stderr)
    args = build_parser().parse_args(argv)
    if args.command == "status":
        print("agent-handoff-demo: ready")
        return 0

    store = TaskStore(args.data_file)
    try:
        if args.command == "add":
            title = args.title.strip()
            if not title:
                print("error: task title cannot be empty", file=sys.stderr)
                return 2
            task = store.add(title)
            print(f"Added task {task.id}: {task.title}")
            return 0
        if args.command == "list":
            tasks = store.list_tasks()
            if not tasks:
                print("No tasks.")
                return 0
            for task in tasks:
                marker = "x" if task.completed else " "
                print(f"[{marker}] {task.id}: {task.title}")
            return 0
        if args.command == "complete":
            task = store.complete(args.id)
            print(f"Completed task {task.id}: {task.title}")
            return 0
    except StorageError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    raise AssertionError(f"unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
