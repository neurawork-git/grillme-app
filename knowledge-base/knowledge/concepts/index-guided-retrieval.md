---
title: "Index-Guided Retrieval (Why No RAG)"
aliases: [no-rag, query-engine]
tags: [knowledge-base, decision, retrieval]
sources:
  - "knowledge-base/AGENTS.md"
  - "docs/documentation-pipeline.md"
  - "CLAUDE.md"
  - "knowledge-base/CLAUDE.md"
  - "daily/2026-08-27.md"
created: 2026-08-20
updated: 2026-08-27
---

# Index-Guided Retrieval (Why No RAG)

The knowledge base answers questions by reasoning over a curated `index.md`
rather than by vector similarity. The stated rationale: at repo scale — tens to a
few hundred articles — embeddings match similar *words* while the LLM matches
relevant *meaning*. No embeddings, no chunking, no vector store.

## Key Points

- The query loop is explicit: read `index.md` first, pick 3-10 relevant articles,
  read them **in full**, synthesise an answer citing sources as wikilinks.
- If the base lacks the answer, say so plainly — do not invent.
- The stated ceiling: past roughly **2,000 articles / ~2M tokens** the index
  stops fitting in context, and a keyword + semantic search layer should be added
  at that point. Until then, no vector store.
- `query.py` **returns errors as its answer string** — an SDK failure yields
  `"Error querying knowledge base: …"` printed as if it were the answer, not a
  non-zero exit. Check the text, not the exit code.
- `--file-back` widens the tool set: without it `query.py` is read-only
  (`Read`, `Glob`, `Grep`); with it, `Write` and `Edit` are added and the LLM
  files a `knowledge/qa/` article, adds an index row, and appends to
  `knowledge/log.md`.

## Details

The decision is recorded identically in three places — the root `CLAUDE.md` key
decisions, the "Why No RAG" section of `knowledge-base/AGENTS.md`, and the
matching section of `docs/documentation-pipeline.md` — which makes it one of the
harness's load-bearing design commitments rather than an implementation detail.

The index is therefore not documentation *about* the base; it is the base's
retrieval mechanism. That is also why it is the one knowledge-base file kept
under version control alongside the articles while `log.md` is gitignored.

Query cost is folded into the same accounting as compilation: `query.py` adds its
cost to `state["total_cost"]` alongside a `query_count`.

Since engine version 3 there is a second reader of the base that is not
`query.py`: the `kb-researcher` subagent spawned during PRP research workflows
(see [[concepts/kb-researcher-directive]]). It is handed the same retrieval
contract in stronger terms — start at the index, cite full article paths, and
then **walk backlinks**, because `connections/` articles are reachable no other
way. Backlink traversal is the part the human-facing query rules leave implicit,
and it is what turns the index from a flat catalog into an entry point.

## Related Concepts

- [[concepts/knowledge-article-schema]] — the index format this depends on
- [[concepts/llm-as-compiler-model]] — retrieval as the "runtime" half of the
  analogy
- [[connections/compile-prompt-ceiling]] — the limit bites the compiler before
  the query engine
- [[concepts/kb-researcher-directive]] — the second reader of the base
- [[connections/knowledge-base-closes-the-loop]] — retrieval as an input to the
  next session

## Sources

- `knowledge-base/AGENTS.md` — query rules and the "Why No RAG" section
- `docs/documentation-pipeline.md` — the same reasoning plus cost accounting
- `CLAUDE.md` — "No RAG" as a key decision
- `knowledge-base/CLAUDE.md` — `query.py` gotchas and `--file-back` behaviour
- [[daily/2026-08-27.md]] — `kb-researcher` as a fourth research axis reading
  this base
