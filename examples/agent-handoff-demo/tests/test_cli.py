from __future__ import annotations

import io
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from agent_handoff_demo.cli import main  # noqa: E402


class CliTests(unittest.TestCase):
    def test_status_reports_ready(self) -> None:
        output = io.StringIO()

        with redirect_stdout(output):
            exit_code = main(["status"])

        self.assertEqual(exit_code, 0)
        self.assertEqual(output.getvalue(), "agent-handoff-demo: ready\n")


if __name__ == "__main__":
    unittest.main()
