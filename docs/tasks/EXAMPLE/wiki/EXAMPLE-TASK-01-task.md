---
id: EXAMPLE-TASK-01
epic: Wiki
title: llmwiki commands via Obsidian CLI
---

# EXAMPLE-TASK-01 · llmwiki commands via Obsidian CLI

## Goal

Switch `/evia:wiki:ingest` and `/evia:wiki:lint` to do all vault operations through the `obsidian` CLI (`obsidian-cli` skill from `obsidian@obsidian-skills`), with a file-based fallback.

## Scope

- In: `.claude/commands/evia/wiki/ingest.md`, `.claude/commands/evia/wiki/lint.md`, new `.claude/settings.json` (marketplace + plugin), README install section.
- Out: markitdown conversion and git commit steps (stay shell), `.claude/settings.local.json`, templates content.

## Acceptance criteria

- [ ] Both commands start with a preflight: load `obsidian-cli` skill, `obsidian version`, pick vault (`vaults verbose`, `vault=<name>`), derive vault-relative wiki prefix `<wiki>`; bounded calls via `perl -e 'alarm 10; exec @ARGV' obsidian ...` (no `timeout` on macOS).
- [ ] All vault reads/writes/queries use CLI (`read`, `create`, `append`, `property:*`, `properties`, `search`/`search:context`, `files folder=`, `links`, `backlinks`, `orphans`, `unresolved`, `aliases`, `rename`/`move`); no grep/`wiki/pages/*.md` scans outside Fallback.
- [ ] Each command has one short Fallback section mapping CLI ops to grep/Read/Edit; fallback use mentioned in report + log entry.
- [ ] Workflow semantics unchanged (checkpoint, authority model, contradiction callout, bookkeeping).
- [ ] `.claude/settings.json` registers `kepano/obsidian-skills` marketplace and enables `obsidian@obsidian-skills`.
- [ ] README has "Install Obsidian skills as Claude Code plugin" section after the Matt Pocock one.

## Notes

- `template=` resolves only from the vault's Templates core-plugin folder; `.claude/templates/` is a dot-folder (not indexed), so templates are read with Read and written via `create path=... content=...`.
- No in-place replace op: body edits = `read` + `create ... overwrite`. `property:set` only for scalars; list keys (`sources:` wikilinks) rewritten via read + overwrite, since list parsing of `property:set` is unverified.
- Orphan = no inbound links, or inbound only from `index.md`/`log.md` (`orphans` + `backlinks`).
- CLI exits 0 on errors; check output for `Error:`.
- Search: unquoted `original:` errors ("Operator not recognized"), unquoted `[[` errors; quote literals inside query (`query="\"[!warning] Contradiction\""`). Source pages via `[type:source]` property search.

<!-- task-cost -->
