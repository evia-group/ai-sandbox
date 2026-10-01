# Monkey patched devcontainer setup from Anthropic

- Source: [Claude Code GitHub](https://github.com/anthropics/claude-code/tree/main)

Setup proxy on Docker and IDE and start container

## Install Matt Pocock's skills as Claude Code plugin

```bash
claude plugin marketplace add mattpocock/skills
claude plugin install mattpocock-skills@mattpocock
```

Or inside Claude Code: `/plugin marketplace add mattpocock/skills` then `/plugin install mattpocock-skills@mattpocock`.

## Install Obsidian skills as Claude Code plugin

```bash
claude plugin marketplace add kepano/obsidian-skills
claude plugin install obsidian@obsidian-skills
```

Or inside Claude Code: `/plugin marketplace add kepano/obsidian-skills` then `/plugin install obsidian@obsidian-skills`.

Needs the Obsidian app running with CLI enabled. Used by the `/evia:wiki:*` commands.

## Task workflow

Idea → grill → implement → record cost: see [docs/WORKFLOW.md](docs/WORKFLOW.md).
