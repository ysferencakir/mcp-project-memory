import asyncio
import os
import sys
from datetime import timedelta
from importlib.metadata import version

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def _run_handshake():
    env = os.environ.copy()
    env["OBSIDIAN_API_KEY"] = "handshake-only"
    env["PROJECT_MEMORY_ROOT"] = "_handshake-test"
    params = StdioServerParameters(
        command=sys.executable,
        args=[
            "-c",
            "import asyncio; from mcp_obsidian.server import main; asyncio.run(main())",
        ],
        env=env,
    )

    async with stdio_client(params) as streams:
        async with ClientSession(
            *streams,
            read_timeout_seconds=timedelta(seconds=10),
        ) as session:
            initialized = await session.initialize()
            tools = await session.list_tools()
            return initialized, tools


def test_stdio_handshake_advertises_instructions_and_all_tools():
    initialized, tools = asyncio.run(_run_handshake())

    assert initialized.serverInfo.name == "mcp-project-memory"
    assert initialized.serverInfo.version == version("mcp-obsidian")
    assert initialized.instructions is not None
    assert "project_get_context" in initialized.instructions[:512]
    assert "project_checkpoint" in initialized.instructions
    assert len(tools.tools) == 19
