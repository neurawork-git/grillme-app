---
title: "Connection: The Scaling Ceiling Bites the Compiler First"
connects:
  - "concepts/knowledge-article-schema"
  - "concepts/index-guided-retrieval"
sources:
  - "docs/documentation-pipeline.md"
  - "knowledge-base/CLAUDE.md"
  - "knowledge-base/AGENTS.md"
created: 2026-08-20
updated: 2026-08-20
---

# Connection: The Scaling Ceiling Bites the Compiler First

## The Connection

The "no RAG" decision is argued in terms of the *query* path: an index of tens to
a few hundred articles fits in context, so index-guided retrieval beats vector
similarity until roughly 2,000 articles / ~2M tokens. But the limit is not
reached by `query.py`. `compile.py` inlines the current `index.md` **plus the
full text of every existing article** into its prompt, so the compiler's prompt
grows with the whole base while a query only ever reads the index plus the 3-10
articles it selects.

## Key Insight

The documented threshold therefore belongs to the wrong stage of the pipeline.
The base becomes uncompilable before it becomes unqueryable — and the failure
shows up as rising cost per compile rather than as a wrong answer, which makes it
easy to miss. `docs/documentation-pipeline.md` says so directly: "In practice
`compile.py` hits this ceiling before `query.py` does."

Two schema rules read differently in that light. "3-7 concepts per log, no more"
and "prefer UPDATE over CREATE" are presented as quality rules — avoid
near-duplicates, favour depth — but they are also the only mechanism keeping the
compile prompt bounded. Article count, not article quality, is what the compiler
pays for. The same applies to the background gate's use of `--all`: every
automatic compile reprocesses every daily log against the full inlined base.

## Evidence

- `docs/documentation-pipeline.md`, "Why No RAG": the ~2,000 article / ~2M token
  limit, followed by the note that `compile.py` reaches it first because it
  inlines every article rather than just the index.
- `knowledge-base/CLAUDE.md` gotchas: "`compile.py` inlines every existing
  article into the prompt. Prompt size grows with the base — the same scaling
  limit `AGENTS.md` cites for the index applies here first."
- `knowledge-base/AGENTS.md` compile rules 2 and 3: at most 3-7 concepts per log,
  and prefer updating an existing article over a near-duplicate.
- `knowledge-base/CLAUDE.md`: `session-start.py` spawns `scripts/compile.py
  --all`, so a background run recompiles every daily log.

## Related Concepts

- [[concepts/knowledge-article-schema]]
- [[concepts/index-guided-retrieval]]
- [[concepts/background-spawn-gate]]
