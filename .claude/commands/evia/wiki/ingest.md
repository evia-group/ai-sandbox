---
description: Ingest one raw source into the wiki — convert, summarize, review checkpoint, propagate, index, log, commit
argument-hint: [filename or fuzzy name of a document in wiki/raw/ — omit to pick from un-ingested sources]
---

Ingest a single source document into the wiki. Follow `CLAUDE.md` conventions throughout.
This is a **supervised** workflow with one human checkpoint — do not skip it.

Target source: $ARGUMENTS

## 0. Select the source

- If a target was given, resolve it to exactly one file in `wiki/raw/` (fuzzy-match on name).
- If no target was given: list files in `wiki/raw/` that have no `source` page yet
  (compare against `original:` keys — `grep -h "^original:" wiki/pages/*.md`) and ask
  which one to ingest.
- If the resolved file already has a source page, say so and ask whether to re-ingest
  (update the existing pages) or abort.

## 1. Convert (binary sources only)

- Derive the kebab-case slug for this source (e.g. `Document_v1.5.1.docx` → `document-v1-5-1`).
- If the source is not markdown/plain text and `wiki/raw-text/<slug>.md` does not exist:
  run `markitdown "wiki/raw/<original>" -o "wiki/raw-text/<slug>.md"`.
- Sanity-check the conversion (non-empty, headings/tables survived). For PDFs with poor
  conversion, read the PDF natively instead and note the fallback in the log entry later.
- Never modify anything in `wiki/raw/`.

## 2. Read and summarize

- Read the full source (via `wiki/raw-text/` mirror, or natively).
- Read `wiki/index.md` to know which existing pages this source will touch.
- Write the source page `wiki/pages/<slug>.md` **immediately** from
  `.claude/templates/source.md`: frontmatter (`type: source`, `original`, `raw-text`,
  `aliases`, dates), key takeaways, and a **Proposed propagation** section listing the
  entity/concept pages you intend to create or update, each with one line of what changes.

## 3. Checkpoint — STOP and discuss

Present to the human: the written summary's key takeaways and the proposed propagation plan
(new pages, updated pages, classification, new glossary terms). **Wait for their feedback.**
They may correct emphasis, reject pages, reclassify, or add context that isn't in the source.
Apply corrections to the source page before continuing.

## 4. Propagate

- Create/update the agreed entity and concept pages from the templates. On every touched
  entity/concept page: append this source to frontmatter `sources:`, bump `updated:`.
- Where the new source **contradicts** an existing claim, do not silently overwrite —
  state both versions in the page with their sources ("Lastenheft v1.5.1 says X; the
  kick-off deck says Y") and flag it under a `> [!warning] Contradiction` callout.
- Add new Fachbegriffe to `wiki/pages/glossary.md`.
- Cross-link: new pages must be linked from at least one existing page, and link outward
  where natural. No orphans.
- Remove the **Proposed propagation** section from the source page (it's done) and replace
  it with a short **Affected pages** list.

## 5. Bookkeeping

- Update `wiki/index.md` (new pages, changed one-liners).
- Append to `wiki/log.md`: `## [YYYY-MM-DD] ingest | <display name>` + 2–5 bullets.
- Commit everything from this operation: `git add -A && git commit -m "ingest: <slug>"`.

## 6. Report

End with: takeaways in one paragraph, list of created/updated pages, any flagged
contradictions, and suggested next source to ingest.
