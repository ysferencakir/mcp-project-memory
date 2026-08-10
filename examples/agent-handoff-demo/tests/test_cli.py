from __future__ import annotations

import io
import os
import subprocess
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CLI_PATH = PROJECT_ROOT / "src" / "agent_handoff_demo" / "cli.py"
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from agent_handoff_demo.cli import main  # noqa: E402


class CliTests(unittest.TestCase):
    def test_status_reports_ready(self) -> None:
        output = io.StringIO()

        with redirect_stdout(output):
            exit_code = main(["status"])

        self.assertEqual(exit_code, 0)
        self.assertEqual(output.getvalue(), "agent-handoff-demo: ready\n")

    def test_add_then_list_tasks_with_stable_ids(self) -> None:
        with TemporaryDirectory() as directory:
            data_file = Path(directory) / "tasks.json"

            first_output = io.StringIO()
            with redirect_stdout(first_output):
                first_exit = main(
                    ["--data-file", str(data_file), "add", "Write tests"]
                )

            second_output = io.StringIO()
            with redirect_stdout(second_output):
                second_exit = main(
                    ["--data-file", str(data_file), "add", "Ship demo"]
                )

            list_output = io.StringIO()
            with redirect_stdout(list_output):
                list_exit = main(["--data-file", str(data_file), "list"])

            self.assertEqual(first_exit, 0)
            self.assertEqual(first_output.getvalue(), "Added task 1: Write tests\n")
            self.assertEqual(second_exit, 0)
            self.assertEqual(second_output.getvalue(), "Added task 2: Ship demo\n")
            self.assertEqual(list_exit, 0)
            self.assertEqual(
                list_output.getvalue(),
                "[ ] 1: Write tests\n[ ] 2: Ship demo\n",
            )

    def test_list_without_a_data_file_is_empty(self) -> None:
        with TemporaryDirectory() as directory:
            output = io.StringIO()
            with redirect_stdout(output):
                exit_code = main(
                    ["--data-file", str(Path(directory) / "missing.json"), "list"]
                )

        self.assertEqual(exit_code, 0)
        self.assertEqual(output.getvalue(), "No tasks.\n")

    def test_add_rejects_an_empty_title(self) -> None:
        with TemporaryDirectory() as directory:
            error = io.StringIO()
            with redirect_stderr(error):
                exit_code = main(
                    ["--data-file", str(Path(directory) / "tasks.json"), "add", "  "]
                )

        self.assertEqual(exit_code, 2)
        self.assertEqual(error.getvalue(), "error: task title cannot be empty\n")

    def test_list_reports_malformed_storage(self) -> None:
        with TemporaryDirectory() as directory:
            data_file = Path(directory) / "tasks.json"
            data_file.write_text("not json", encoding="utf-8")
            error = io.StringIO()
            with redirect_stderr(error):
                exit_code = main(["--data-file", str(data_file), "list"])

        self.assertEqual(exit_code, 1)
        self.assertIn("error: could not read", error.getvalue())

    def test_complete_marks_the_task_without_changing_ids(self) -> None:
        with TemporaryDirectory() as directory:
            data_file = Path(directory) / "tasks.json"
            with redirect_stdout(io.StringIO()):
                main(["--data-file", str(data_file), "add", "First"])
                main(["--data-file", str(data_file), "add", "Second"])

            complete_output = io.StringIO()
            with redirect_stdout(complete_output):
                complete_exit = main(
                    ["--data-file", str(data_file), "complete", "1"]
                )

            list_output = io.StringIO()
            with redirect_stdout(list_output):
                list_exit = main(["--data-file", str(data_file), "list"])

        self.assertEqual(complete_exit, 0)
        self.assertEqual(complete_output.getvalue(), "Completed task 1: First\n")
        self.assertEqual(list_exit, 0)
        self.assertEqual(list_output.getvalue(), "[x] 1: First\n[ ] 2: Second\n")

    def test_complete_reports_a_missing_id(self) -> None:
        with TemporaryDirectory() as directory:
            data_file = Path(directory) / "tasks.json"
            with redirect_stdout(io.StringIO()):
                main(["--data-file", str(data_file), "add", "Existing"])

            error = io.StringIO()
            with redirect_stderr(error):
                exit_code = main(
                    ["--data-file", str(data_file), "complete", "99"]
                )

        self.assertEqual(exit_code, 1)
        self.assertEqual(error.getvalue(), "error: task not found: 99\n")

    def test_complete_reports_malformed_storage(self) -> None:
        with TemporaryDirectory() as directory:
            data_file = Path(directory) / "tasks.json"
            data_file.write_text('{"tasks": "invalid"}', encoding="utf-8")
            error = io.StringIO()
            with redirect_stderr(error):
                exit_code = main(
                    ["--data-file", str(data_file), "complete", "1"]
                )

        self.assertEqual(exit_code, 1)
        self.assertEqual(error.getvalue(), "error: 'tasks' must be a list\n")

    def test_subprocess_emits_utf8_when_initial_encoding_is_cp1252(self) -> None:
        with TemporaryDirectory() as directory:
            data_file = Path(directory) / "tasks.json"
            environment = os.environ.copy()
            environment["PYTHONIOENCODING"] = "cp1252"

            commands = (
                (["add", "Bağlamı doğrula"], "Added task 1: Bağlamı doğrula\n"),
                (["list"], "[ ] 1: Bağlamı doğrula\n"),
                (["complete", "1"], "Completed task 1: Bağlamı doğrula\n"),
                (["list"], "[x] 1: Bağlamı doğrula\n"),
            )

            for command, expected_output in commands:
                result = subprocess.run(
                    [
                        sys.executable,
                        str(CLI_PATH),
                        "--data-file",
                        str(data_file),
                        *command,
                    ],
                    capture_output=True,
                    check=False,
                    env=environment,
                )

                self.assertEqual(
                    result.returncode,
                    0,
                    result.stderr.decode("utf-8", errors="replace"),
                )
                self.assertEqual(
                    result.stdout.decode("utf-8"),
                    expected_output.replace("\n", os.linesep),
                )


if __name__ == "__main__":
    unittest.main()
