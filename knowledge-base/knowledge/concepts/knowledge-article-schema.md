---
title: "Knowledge Article Schema"
aliases: [article-format, wikilink-convention, lint-checks]
tags: [knowledge-base, conventions, schema]
sources:
  - "knowledge-base/AGENTS.md"
  - "knowledge-base/CLAUDE.md"
created: 2026-08-20
updated: 2026-08-20
---

# Knowledge Article Schema

The knowledge base has three article kinds — `concepts/` (one atomic idea per
file), `connections/` (a non-obvious relationship between two or more existing
concepts), and optional `qa/` (a filed query answer) — plus `index.md`, the
master catalog, and `log.md`, an append-only build log. Every article carries
YAML frontmatter and a fixed set of sections.

## Key Points

- **Frontmatter minimum**: `title`, `sources`, `created`, `updated`. A concept
  article adds optional `aliases` and `tags`; a connection article carries a
  `connects:` list.
- Section shape for a concept: a two-to-four-sentence statement, `## Key Points`
  (aim for 3-5 self-contained bullets), `## Details` (two or more
  encyclopedia-style paragraphs), `## Related Concepts`, `## Sources`.
- **Wikilinks are repo-relative from `knowledge/`, without `.md`** — double
  square brackets around `concepts/slug` or `connections/slug`. Daily-log
  references are the one exception and keep the extension
  (`daily/2026-06-18.md`) because a log is a source, not an article; `lint.py`
  special-cases the `daily/` prefix.
- Every article must cite its source(s) in both `sources:` and `## Sources`, and
  link to **at least two** other articles.
- **3-7 concepts per log, no more** — quality over volume, and always prefer
  updating an existing article (appending to its `sources:`) over a
  near-duplicate. Connection articles are rare by design.

## Details

The index is the retrieval mechanism, not a table of contents: a table of every
article with a one-line summary, what it was compiled from, and an updated date.
Both the compiler and the query engine read it first and then open only the
articles a task needs. `log.md` gets one appended entry per compile, query, or
lint, timestamped in full ISO with offset.

There is a deliberate tracking asymmetry: `knowledge/index.md` is versioned but
`knowledge/log.md` is not, even though `AGENTS.md` treats both as knowledge-base
files. The stated reason is that the build log is local noise while the index is
the retrieval mechanism and must be shared. `daily/`, `reports/`, the state and
stamp files, the lock, `flush.log`, and the transient context files are all
gitignored.

`lint.py` runs six structural checks plus one LLM check, and **any `error`
severity makes it exit 1**: `broken_link` (error), `contradiction` (warning, or
error if the LLM call itself fails), `orphan_page`, `orphan_source` and
`stale_article` (warnings), `missing_backlink` (suggestion, auto-fixable), and
`sparse_article` — fewer than 200 words (suggestion). `--structural-only` skips
the contradiction check for a fast, zero-cost pass.

## Related Concepts

- [[concepts/index-guided-retrieval]] — what the index is for
- [[concepts/llm-as-compiler-model]] — who writes these articles and why
- [[connections/compile-prompt-ceiling]] — where the schema meets its scaling
  limit

## Sources

- `knowledge-base/AGENTS.md` — article formats, index and log formats, compile
  rules, lint checks
- `knowledge-base/CLAUDE.md` — local conventions, the lint severity table, the
  index/log tracking asymmetry
