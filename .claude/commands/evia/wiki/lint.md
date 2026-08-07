---
description: Health-check the wiki — auto-fix mechanical issues, report substantive ones
argument-hint: [optional focus, e.g. a page slug or "contradictions"]
---

Run a health check over the wiki. Follow `CLAUDE.md` conventions. Authority model:
**auto-fix mechanical issues, report substantive ones** — never resolve a substantive
finding without the human.

Focus (optional): $ARGUMENTS

## 1. Survey

Read `wiki/index.md`, `wiki/log.md` (recent entries), and every page in `wiki/pages/`.
Build the link graph (grep for `[[...]]` targets) and the provenance map (frontmatter
`sources:` lists).

## 2. Mechanical checks — fix silently, list in report

- **Broken wikilinks**: `[[target]]` where no `wiki/pages/<target>.md` exists → fix the
  link if it's a typo/renamed page; otherwise report as a missing-page finding (substantive).
- **Index drift**: pages missing from `wiki/index.md`, index entries pointing nowhere,
  stale one-liners → correct the index.
- **Frontmatter defects**: missing required keys per CLAUDE.md, `updated:` older than the
  file's real last change (per git), source pages without `original:` → repair.
- **Missing cross-references**: two pages that plainly discuss each other without linking
  → add the links.
- **Glossary gaps**: German Fachbegriffe used in pages but absent from `glossary.md`
  → add stub entries.

## 3. Substantive checks — report only, do NOT edit

- **Contradictions**: pages (or a page and its sources) making incompatible claims.
  Cite both locations and both underlying sources.
- **Stale claims**: statements whose provenance is an older source when a newer ingested
  source covers the same ground differently.
- **Orphan pages**: no inbound links from any other page — propose where they should be
  linked from, or whether they should be merged/deleted.
- **Missing concept/entity pages**: things repeatedly mentioned across pages that deserve
  their own page.
- **Data gaps**: questions the wiki raises but cannot answer — suggest which kind of
  source (or web search) would fill each gap.

## 4. Report

Output a findings report, severity-ordered:
1. What was auto-fixed (grouped, with counts).
2. Substantive findings, each with: location(s), evidence, and a recommended resolution.
3. Suggested follow-ups (sources to hunt, questions to ask).

Ask the human which substantive findings to act on; apply the approved ones.

## 5. Bookkeeping

- Append to `wiki/log.md`: `## [YYYY-MM-DD] lint | <short summary>` + bullets
  (auto-fixed counts, substantive findings raised, which were resolved).
- Commit: `git add -A && git commit -m "lint: <short summary>"`.
