# Task workflow: idea → implementation → cost

How to take one task from a rough idea to committed code, with its token cost recorded. Built on [Matt Pocock's skills](https://github.com/mattpocock/skills) (main flow from his `/ask-matt`) plus this repo's `/record-task-cost`.

## Once per machine / repo

1. Install the plugin (see [README](../README.md#install-matt-pococks-skills-as-claude-code-plugin)).
2. Run `/setup-matt-pocock-skills` once. Pick **local files** as issue tracker.

## Task files

- One task = one file: `docs/tasks/<milestone>/<epic>/<ID>-task.md`, e.g. `docs/tasks/M0/planning/M0-01-task.md`.
- Copy [`docs/tasks/_template.md`](tasks/_template.md). Frontmatter `id` must match the filename.
- Everything below `<!-- task-cost -->` belongs to `scripts/task_cost.py`. Don't edit it by hand.

## Rule: one session per step, separated by `/clear`

`/record-task-cost` records the session that **just ended**. A session ends on `/clear`. So start every task session with `/clear`, and run `/record-task-cost` as the first command after the next `/clear`. Each recorded session adds its own rows to the footer, so a task can collect several sessions (planning + implementation).

## Path A: small task (fits one session)

```
/clear
/grill-with-docs <your idea>          # agent interviews you; updates CONTEXT.md / ADRs
> Write this up as docs/tasks/M0/planning/M0-01-task.md from the template.
/implement docs/tasks/M0/planning/M0-01-task.md   # TDD + /code-review + commit
/clear
/record-task-cost M0-01               # writes the cost footer
/clear                                # before the next task
```

Grill, task file and implementation stay in one context window, so the agent builds on the same thinking.

## Path B: bigger feature (several sessions)

```
/clear
/grill-with-docs <your idea>
/to-spec                              # spec from the conversation
/to-tickets                           # ask: one task file per ticket in docs/tasks/<milestone>/<epic>/, from the template, with "Blocked by"
/clear
/record-task-cost M0-01               # planning session → first ticket (or an epic task file)
```

Then for each ticket, blockers first:

```
/clear
/implement docs/tasks/M0/planning/M0-02-task.md
/clear
/record-task-cost M0-02
```

Don't `/clear` or `/compact` between grill, spec and tickets: they should share one context. Each `/implement` starts fresh, since the ticket holds everything it needs.

## Other useful skills

- Can't settle a question on paper → `/prototype` (bridge with `/handoff`).
- Something broken → `/diagnosing-bugs`.
- Unsure which skill fits → `/ask-matt`.

## For agents

- Don't create task files outside `docs/tasks/<milestone>/<epic>/<ID>-task.md`. Use the template.
- Don't touch the `<!-- task-cost -->` footer. Only `/record-task-cost` writes it.
- `/record-task-cost` is user-invoked only. If a task is done, remind the user to `/clear` and run it.
