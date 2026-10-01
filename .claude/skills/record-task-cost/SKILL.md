---
name: record-task-cost
description: Right after /clear, write the ended session's exact token usage (per model, subagents and side calls included) and wall-clock time into a task file's footer.
argument-hint: "[task ID or path, e.g. M0-15]"
disable-model-invocation: true
allowed-tools: Bash(python3 scripts/task_cost.py:*)
---

Record the token cost of the task session that just ended in its task file. The user runs this as the first command after `/clear`: `/clear` ends the task session, and Claude Code then writes that session's final per-model totals (a `cost-state` record) into its transcript.

1. Pick the task:
   - If `$ARGUMENTS` is set, use it (a task ID like `M0-15`, or a path to a task file).
   - Otherwise ask the user for the task ID. After `/clear` this session has no memory of the task, so don't guess.
2. From the repo root, run:

   ```
   python3 scripts/task_cost.py <task> ${CLAUDE_SESSION_ID}
   ```

   The script skips the current session and records the most recently ended one. To record a specific ended session instead, add `--session <session ID>`.
3. Show the user which session was recorded, the footer the script printed, and any warnings (for example, that this session didn't start with `/clear`, or a frontmatter `id` that doesn't match the filename). Don't edit the footer by hand: the script owns everything below `<!-- task-cost -->`, and rerunning it replaces that session's rows.
