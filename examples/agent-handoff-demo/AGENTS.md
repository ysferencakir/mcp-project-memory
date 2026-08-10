# Agent instructions

This project is a continuity test for `mcp-project-memory`.

Before meaningful work:

1. Call `project_get_context` with the MCP server configured with
   `PROJECT_MEMORY_ROOT=agent-handoff-demo`.
2. Treat missing, truncated, or omitted documents as explicit context gaps.
3. Read `STATE`, `HANDOFF`, `ROADMAP`, `TODO`, and pending approvals before
   changing code.

During work:

- Keep the implementation small and dependency-free unless the project memory
  records an approved reason to add a dependency.
- Run the standard-library test suite after changes.
- Do not work concurrently with another agent writing to the same vault.
- Put critical, destructive, security-sensitive, or goal-changing proposals in
  `pending_approvals`; do not record them as approved decisions.

After meaningful work:

1. Reconcile the Obsidian `ROADMAP` and `TODO` documents with verified results.
2. Mark only unambiguously completed checklist items; leave partial or unclear
   items open instead of inferring completion from similar wording.
3. Read the changed planning documents back to verify them.
4. Call `project_checkpoint` with an honest summary, completed work, files
   changed, verification, decisions, pending approvals, blockers, and the next
   smallest concrete step.

Do not claim persistence until the checkpoint succeeds.
