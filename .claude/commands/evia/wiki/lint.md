---
description: Health-check the wiki — auto-fix mechanical issues, report substantive ones
argument-hint: [optional focus, e.g. a page slug or "contradictions"]
---

Run a health check over the wiki. Follow `CLAUDE.md` conventions. Authority model:
**auto-fix mechanical issues, report substantive ones** — never resolve a substantive
finding without the human.

Focus (optional): $ARGUMENTS

## Preflight — Obsidian CLI

All vault reads, writes and queries go through the `obsidian` CLI. Load the `obsidian-cli`
skill (plugin `obsidian@obsidian-skills`) first.

- `perl -e 'alarm 10; exec @ARGV' obsidian version` — must print a version. Killed (rc 142)
  or error → Obsidian not running → **Fallback**. Wrap later calls the same way.
- `obsidian vaults verbose` → pick the vault whose path is `<repo>/wiki` or an ancestor.
  None → **Fallback**. Put `vault="<name>"` first on every call below.
- `<wiki>` = path of `<repo>/wiki` relative to that vault root, with trailing slash
  (`wiki/` if vault = repo, empty if vault = `wiki/`). All `path=` values are vault-relative.
  Vault-wide lists (`unresolved`, `orphans`, `aliases verbose`) → keep only `<wiki>` lines.
- Exit code is 0 even on failure: treat output starting with `Error:` as failure.
- Edits (no in-place replace op): `read`, rewrite, `create path=... content="..." overwrite
  silent`. Scalar frontmatter only: `property:set` / `property:remove`.
- Search: literal brackets/colons must be quoted inside the query (see §3);
  unquoted `[x]` is a property filter.

## 1. Survey

- `read path=<wiki>index.md`, `read path=<wiki>log.md` (recent entries).
- `files folder=<wiki>pages` → `read` every page.
- Link graph: `links path=...` and `backlinks path=...` per page.
- Provenance map: `property:read name=sources path=...` per page.

## 2. Mechanical checks — fix silently, list in report

- **Broken wikilinks**: `unresolved verbose` → fix the link if it's a typo/renamed page;
  otherwise report as a missing-page finding (substantive). Renaming a page: `rename` /
  `move` (Obsidian updates inbound links).
- **Index drift**: pages missing from `<wiki>index.md` (`files folder=<wiki>pages` vs
  `links path=<wiki>index.md`), index entries pointing nowhere, stale one-liners
  → correct the index.
- **Frontmatter defects**: `properties path=... format=json` per page — missing required
  keys per CLAUDE.md, `updated:` older than the file's real last change
  (`git log -1 --format=%cs -- <file>`), source pages (`search query="[type:source]"
  path=<wiki>pages`) without `original:` → repair.
- **Missing cross-references**: two pages that plainly discuss each other without linking
  (`search:context query="<name/alias>" path=<wiki>pages`, aliases via `aliases verbose`)
  → add the links.
- **Glossary gaps**: German Fachbegriffe used in pages but absent from `glossary.md`
  → add stub entries (`append path=<wiki>pages/glossary.md content="..."`).

## 3. Substantive checks — report only, do NOT edit

- **Contradictions**: pages (or a page and its sources) making incompatible claims.
  Cite both locations and both underlying sources. Existing flags:
  `search:context query="\"[!warning] Contradiction\"" path=<wiki>pages`.
- **Stale claims**: statements whose provenance is an older source when a newer ingested
  source covers the same ground differently.
- **Orphan pages**: no inbound links from any other page (`orphans`, plus pages whose only
  `backlinks` are `index.md`/`log.md`) — propose where they should be linked from, or
  whether they should be merged/deleted.
- **Missing concept/entity pages**: things repeatedly mentioned across pages that deserve
  their own page.
- **Data gaps**: questions the wiki raises but cannot answer — suggest which kind of
  source (or web search) would fill each gap.

## 4. Report

Output a findings report, severity-ordered:
1. What was auto-fixed (grouped, with counts).
2. Substantive findings, each with: location(s), evidence, and a recommended resolution.
3. Suggested follow-ups (sources to hunt, questions to ask).
4. Whether the Fallback was used.

Ask the human which substantive findings to act on; apply the approved ones.

## 5. Bookkeeping

- `append path=<wiki>log.md content="## [YYYY-MM-DD] lint | <short summary>\n- ..."`
  + bullets (auto-fixed counts, substantive findings raised, which were resolved,
  Fallback if used).
- Commit: `git add -A && git commit -m "lint: <short summary>"`.

## Fallback — no CLI

Plain file tools on `wiki/` (repo-relative): `files`/`read` → Glob/Read every
`wiki/pages/*.md`; `links`/`backlinks`/`orphans` → grep `[[...]]` targets, build the graph
by hand; `unresolved` → `[[target]]` with no `wiki/pages/<target>.md`; `properties`/
`property:*` → Read/Edit frontmatter; `search:context`/`aliases` → grep; `create`/`append`
→ Write/Edit; `rename`/`move` → `git mv` + fix inbound links.
