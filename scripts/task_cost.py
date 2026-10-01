#!/usr/bin/env python3
"""Write the token usage of the Claude Code session that just ended into a task file's footer.

Usage: task_cost.py <task ID or path> <current session ID> [--session <ended session ID>]

Run it right after `/clear`. `/clear` ends the previous session and starts a new
one, and the ended session's transcript (under ~/.claude/projects/<cwd,
non-alphanumerics replaced by ->/) gets a final `cost-state` record: Claude
Code's own per-model totals, subagents and side calls (classifier, titles,
WebFetch summaries) included. The script reads that record from the most
recently ended session other than the current one (or from --session), and
rewrites everything below `<!-- task-cost -->` in the task file: one row per
session per model, then a Total row per model. Rerunning for the same session
replaces its rows.

Python stdlib only.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

MARKER = "<!-- task-cost -->"
CLEAR_MARKER = "<command-name>/clear</command-name>"
FIELDS = ("input", "output", "cache_read", "cache_write")
# cost-state modelUsage key for each footer column
COST_STATE_KEYS = {
    "input": "inputTokens",
    "output": "outputTokens",
    "cache_read": "cacheReadInputTokens",
    "cache_write": "cacheCreationInputTokens",
}
HEADER = "| Session | Started (UTC) | Wall-clock | Model | Input | Output | Cache read | Cache write |"
SEPARATOR = "| --- | --- | --- | --- | ---: | ---: | ---: | ---: |"


# ---------- transcript ----------


def project_dir(projects_root: Path, cwd: str) -> Path:
    # Claude Code replaces every non-alphanumeric character, not only "/".
    return projects_root / re.sub(r"[^A-Za-z0-9]", "-", cwd)


def read_jsonl(path: Path) -> list[dict]:
    entries = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue  # a partially written last line
    return entries


def cost_state(path: Path) -> dict | None:
    """The last cost-state record in a transcript (written when the session ends)."""
    states = [e for e in read_jsonl(path) if e.get("type") == "cost-state"]
    return states[-1] if states else None


def starts_with_clear(path: Path) -> bool:
    for entry in read_jsonl(path)[:10]:
        content = (entry.get("message") or {}).get("content")
        if entry.get("type") == "user" and isinstance(content, str) and CLEAR_MARKER in content:
            return True
    return False


def ended_session(proj: Path, current: str, explicit: str | None) -> tuple[str, dict]:
    """(session ID, cost-state) of the chosen ended session."""
    if explicit:
        path = proj / f"{explicit}.jsonl"
        if not path.exists():
            raise SystemExit(f"error: transcript not found: {path}")
        state = cost_state(path)
        if not state:
            raise SystemExit(f"error: session {explicit} has no cost-state record (still running?)")
        return explicit, state

    ended = []
    for path in proj.glob("*.jsonl"):
        if path.stem == current:
            continue
        state = cost_state(path)
        if state:
            ended.append((state["startTime"] + state["totalDuration"], path.stem, state))
    if not ended:
        raise SystemExit(f"error: no ended session with a cost-state record in {proj}")
    _, session_id, state = max(ended)
    return session_id, state


def session_usage(session_id: str, state: dict) -> dict:
    models = {}
    for model, u in (state.get("modelUsage") or {}).items():
        row = {f: u.get(k) or 0 for f, k in COST_STATE_KEYS.items()}
        if any(row.values()):
            models[model] = row
    return {
        "session": session_id[:8],
        "started": datetime.fromtimestamp(state["startTime"] / 1000, tz=timezone.utc),
        "seconds": int(state["totalDuration"] / 1000),
        "models": models,
    }


# ---------- task file ----------


def resolve_task(arg: str, repo: Path) -> Path:
    path = Path(arg)
    if not path.is_absolute():
        path = repo / path
    if path.is_file():
        return path
    matches = sorted(glob.glob(str(repo / "docs" / "tasks" / "*" / "*" / f"{arg}-task.md")))
    if not matches:
        raise SystemExit(f"error: no task file for {arg!r} (looked for docs/tasks/*/*/{arg}-task.md)")
    if len(matches) > 1:
        raise SystemExit(f"error: several task files for {arg!r}: {', '.join(matches)}")
    return Path(matches[0])


def check_frontmatter_id(path: Path, text: str) -> None:
    expected = path.name.removesuffix("-task.md")
    m = re.match(r"^---\n(.*?)\n---", text, re.S)
    found = None
    if m:
        idm = re.search(r"^id:\s*(\S+)", m.group(1), re.M)
        found = idm.group(1) if idm else None
    if found != expected:
        print(
            f"warning: frontmatter id {found!r} doesn't match filename {expected!r} ({path})",
            file=sys.stderr,
        )


def fmt_duration(seconds: int) -> str:
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h}h {m:02d}m" if h else f"{m}m {s:02d}s"


def parse_duration(text: str) -> int:
    total = 0
    for value, unit in re.findall(r"(\d+)([hms])", text):
        total += int(value) * {"h": 3600, "m": 60, "s": 1}[unit]
    return total


def fmt_int(n: int) -> str:
    return f"{n:,}"


def parse_rows(footer: str) -> list[dict]:
    """Session rows already in the footer (Total rows are recomputed)."""
    rows = []
    for line in footer.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) != 4 + len(FIELDS) or not re.fullmatch(r"`[0-9a-f]{8}`", cells[0]):
            continue
        rows.append(
            {
                "session": cells[0].strip("`"),
                "started": cells[1],
                "seconds": parse_duration(cells[2]),
                "model": cells[3],
                **{f: int(c.replace(",", "")) for f, c in zip(FIELDS, cells[4:])},
            }
        )
    return rows


def render_footer(rows: list[dict]) -> str:
    lines = [MARKER, "", "## Task cost", "", HEADER, SEPARATOR]
    for r in rows:
        nums = " | ".join(fmt_int(r[f]) for f in FIELDS)
        lines.append(
            f"| `{r['session']}` | {r['started']} | {fmt_duration(r['seconds'])} | {r['model']} | {nums} |"
        )

    wall = {}
    for r in rows:
        wall[r["session"]] = r["seconds"]  # the same on every row of a session
    total_seconds = fmt_duration(sum(wall.values()))
    by_model: dict[str, dict[str, int]] = {}
    for r in rows:
        acc = by_model.setdefault(r["model"], dict.fromkeys(FIELDS, 0))
        for f in FIELDS:
            acc[f] += r[f]
    for model in sorted(by_model):
        nums = " | ".join(f"**{fmt_int(by_model[model][f])}**" for f in FIELDS)
        lines.append(f"| **Total** | | {total_seconds} | {model} | {nums} |")

    lines += ["", "Raw tokens from Claude Code's end-of-session `cost-state` (subagents and side calls included). Written by `/record-task-cost`."]
    return "\n".join(lines) + "\n"


def update_task_file(path: Path, usage: dict) -> str:
    text = path.read_text(encoding="utf-8")
    check_frontmatter_id(path, text)
    # The marker must be on a line of its own; the last such line wins, so the
    # marker can still be mentioned inline in the task text.
    lines = text.splitlines(keepends=True)
    idx = [i for i, line in enumerate(lines) if line.strip() == MARKER]
    if idx:
        body, footer = "".join(lines[: idx[-1]]), "".join(lines[idx[-1] + 1 :])
    else:
        body, footer = text.rstrip("\n") + "\n\n", ""

    rows = [r for r in parse_rows(footer) if r["session"] != usage["session"]]
    started = usage["started"].strftime("%Y-%m-%d %H:%M")
    for model in sorted(usage["models"]):
        rows.append(
            {
                "session": usage["session"],
                "started": started,
                "seconds": usage["seconds"],
                "model": model,
                **usage["models"][model],
            }
        )
    rows.sort(key=lambda r: (r["started"], r["session"], r["model"]))

    new_footer = render_footer(rows)
    path.write_text(body + new_footer, encoding="utf-8")
    return new_footer


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("task", help="task ID (e.g. M0-15) or path to the task file")
    p.add_argument("current_session", help="the current session's ID (skipped when looking for the ended one)")
    p.add_argument("--session", help="record this ended session instead of the most recent one")
    p.add_argument("--repo", default=os.getcwd(), help="repo root (default: cwd)")
    p.add_argument(
        "--projects-dir",
        default=str(Path.home() / ".claude" / "projects"),
        help="Claude Code projects dir (default: ~/.claude/projects)",
    )
    args = p.parse_args(argv)

    repo = Path(args.repo).resolve()
    task_path = resolve_task(args.task, repo)
    proj = project_dir(Path(args.projects_dir), str(repo))
    current = proj / f"{args.current_session}.jsonl"
    if not args.session and current.exists() and not starts_with_clear(current):
        print(
            "warning: this session didn't start with /clear, so the most recently ended "
            "session may not be the task's session",
            file=sys.stderr,
        )
    session_id, state = ended_session(proj, args.current_session, args.session)
    usage = session_usage(session_id, state)
    if not usage["models"]:
        print("warning: the ended session has no model usage", file=sys.stderr)
    footer = update_task_file(task_path, usage)
    rel = task_path.relative_to(repo) if task_path.is_relative_to(repo) else task_path
    print(f"Recorded session {session_id} (started {usage['started']:%Y-%m-%d %H:%M} UTC) in {rel}\n")
    print(footer)
    return 0


if __name__ == "__main__":
    sys.exit(main())
