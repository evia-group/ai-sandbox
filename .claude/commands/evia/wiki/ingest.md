---
description: Ingest one raw source into the wiki — convert, summarize, review checkpoint, propagate, index, log, commit
argument-hint: [filename or fuzzy name of a document in wiki/raw/ — omit to pick from un-ingested sources]
---

Ingest a single source document into the wiki. Follow `CLAUDE.md` conventions throughout.
This is a **supervised** workflow with one human checkpoint — do not skip it.

Target source: $ARGUMENTS

## Preflight — Obsidian CLI

All vault reads, writes and queries go through the `obsidian` CLI. Load the `obsidian-cli`
skill (plugin `obsidian@obsidian-skills`) first.

- `perl -e 'alarm 10; exec @ARGV' obsidian version` — must print a version. Killed (rc 142)
  or error → Obsidian not running → **Fallback**. Wrap later calls the same way.
- `obsidian vaults verbose` → pick the vault whose path is `<repo>/wiki` or an ancestor.
  None → **Fallback**. Put `vault="<name>"` first on every call below.
- `<wiki>` = path of `<repo>/wiki` relative to that vault root, with trailing slash
  (`wiki/` if vault = repo, empty if vault = `wiki/`). All `path=` values are vault-relative.
- Exit code is 0 even on failure: treat output starting with `Error:` as failure.
- Templates: `template=` only resolves from the vault's Templates folder, not
  `.claude/templates/` (dot-folders aren't indexed). Read the template file with Read,
  fill it, then `create path=... content="..." silent` (`\n` for newlines).
- Edits (no in-place replace op): `read`, rewrite, `create path=... content="..." overwrite
  silent`. Scalar frontmatter only: `property:set` / `property:remove`.
- Search: literal brackets/colons must be quoted inside the query, e.g.
  `query="\"original:\""`; unquoted `[x]` is a property filter.

## 0. Select the source

- If a target was given, resolve it to exactly one file in `files folder=<wiki>raw`
  (fuzzy-match on name).
- If no target was given: list `files folder=<wiki>raw`, minus those already ingested
  (`search query="[type:source]" path=<wiki>pages` → `property:read name=original
  path=...` per hit), and ask which one to ingest.
- If the resolved file already has a source page, say so and ask whether to re-ingest
  (update the existing pages) or abort.

## 1. Convert (binary sources only)

- Derive the kebab-case slug for this source (e.g. `Document_v1.5.1.docx` → `document-v1-5-1`).
- If the source is not markdown/plain text and `<wiki>raw-text/<slug>.md` is not in
  `files folder=<wiki>raw-text`: run
  `markitdown "wiki/raw/<original>" -o "wiki/raw-text/<slug>.md"` (shell, repo-relative).
- Sanity-check the conversion (`read path=<wiki>raw-text/<slug>.md`: non-empty,
  headings/tables survived). For PDFs with poor conversion, read the PDF natively instead
  and note the fallback in the log entry later.
- Never modify anything in `wiki/raw/`.

## 2. Read and summarize

- Read the full source (`read path=<wiki>raw-text/<slug>.md`, or natively).
- `read path=<wiki>index.md` to know which existing pages this source will touch;
  `search:context query="<term>" path=<wiki>pages` for key terms.
- Write the source page `<wiki>pages/<slug>.md` **immediately** from
  `.claude/templates/source.md` via `create`: frontmatter (`type: source`, `original`,
  `raw-text`, `aliases`, dates), key takeaways, and a **Proposed propagation** section
  listing the entity/concept pages you intend to create or update, each with one line of
  what changes.

## 3. Checkpoint — STOP and discuss

Present to the human: the written summary's key takeaways and the proposed propagation plan
(new pages, updated pages, classification, new glossary terms). **Wait for their feedback.**
They may correct emphasis, reject pages, reclassify, or add context that isn't in the source.
Apply corrections to the source page before continuing.

## 4. Propagate

- Create the agreed entity/concept pages from the templates (`create`); update existing
  ones (`read` + `create ... overwrite`, or `append`). On every touched entity/concept
  page: append this source to frontmatter `sources:` as a wikilink (`"[[<slug>]]"`) by
  rewriting the frontmatter (`read` + `create ... overwrite`), bump `updated:`
  (`property:set name=updated value=<YYYY-MM-DD> type=date`).
- Where the new source **contradicts** an existing claim, do not silently overwrite —
  state both versions in the page with their sources ("Lastenheft v1.5.1 says X; the
  kick-off deck says Y") and flag it under a `> [!warning] Contradiction` callout.
- Add new Fachbegriffe to the glossary: `append path=<wiki>pages/glossary.md content="..."`.
- Cross-link: new pages must be linked from at least one existing page, and link outward
  where natural. No orphans — check `backlinks path=<wiki>pages/<new>.md` (≥1 hit besides
  `index.md`/`log.md`).
- Remove the **Proposed propagation** section from the source page (it's done) and replace
  it with a short **Affected pages** list.

## 5. Bookkeeping

- Update `<wiki>index.md` (new pages, changed one-liners): `read` + `create ... overwrite`.
- `append path=<wiki>log.md content="## [YYYY-MM-DD] ingest | <display name>\n- ..."`
  + 2–5 bullets. If the Fallback was used, one bullet says so.
- Commit everything from this operation: `git add -A && git commit -m "ingest: <slug>"`.

## 6. Report

End with: takeaways in one paragraph, list of created/updated pages, any flagged
contradictions, suggested next source to ingest, and whether the Fallback was used.

## Fallback — no CLI

Plain file tools on `wiki/` (repo-relative): `files folder=` → `ls`/Glob; `read` → Read;
`create`/`overwrite` → Write; `append`/`property:*` → Edit; `property:read name=original`
→ `grep -h "^original:" wiki/pages/*.md`; `search:context` → `grep -n` in
`wiki/pages/*.md`; `backlinks` → grep for `[[<slug>` in `wiki/pages/*.md`.
