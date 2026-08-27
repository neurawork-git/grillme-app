---
title: "The LLM-as-Compiler Model"
aliases: [compiler-analogy, daily-logs-are-source-code]
tags: [harness, design, decision]
sources:
  - "CLAUDE.md"
  - "docs/documentation-pipeline.md"
  - "knowledge-base/AGENTS.md"
  - "claudemd-lerner/AGENTS.md"
created: 2026-08-20
updated: 2026-08-20
---

# The LLM-as-Compiler Model

Every engine in this repository is built on one analogy, stated at the top of
each `AGENTS.md`: `daily/` is source code (raw session logs, append-only, never
rewritten), the LLM is the compiler, and the outputs — `knowledge/`, `CLAUDE.md`,
`docs/` — are the executable. `lint` is the test suite and `query` the runtime.

## Key Points

- The consequence that matters: **documentation is never organised by hand.**
  Sessions produce logs, the LLM does the synthesis and cross-linking.
- Hand-*editing* an output file is allowed — the learner is instructed to
  preserve hand-written content — but hand-*organising* the tree defeats the
  design.
- **Prefer UPDATE over CREATE, and `Edit` over rewrite.** The learner edits
  surgically to keep diffs readable; the compiler updates an existing article
  rather than creating a near-duplicate.
- **Incremental by content hash.** `update.py` and `compile.py` track the first
  16 hex chars of each daily log's SHA-256 in `scripts/state.json` and reprocess
  only what changed.
- Lineage: a repo-local implementation of the LLM-as-compiler idea (Andrej
  Karpathy's LLM wiki, rebuilt openly by coleam00's claude-memory-compiler), with
  the doc-maintenance pattern from NeuraWork's own coding-suite learner. The
  designs are independent NeuraWork work; only the underlying concept is shared.

## Details

State is saved after each log, so an interrupted multi-log run keeps the work it
already paid for. A failed run returns cost `0.0` and records nothing, leaving
the log marked changed for the next attempt — failures are retried rather than
silently swallowed.

The synthesis step runs in a deliberately hermetic environment: the SDK is
invoked with `permission_mode="acceptEdits"`, `max_turns=30`,
`setting_sources=[]`, and `strict_mcp_config=True`, so the run does not inherit
the repository's own Claude Code settings or MCP servers. The model edits the
output files directly with `Read`/`Write`/`Edit`/`Glob`/`Grep`; `update_one()`
deliberately discards the assistant's text and prints only the cost, so a run is
debugged from the resulting file diffs, not from stdout.

Both constitutions restate the same grounding rule in their own words: never
invent, ground every statement in the daily log or in a file actually read, and
leave out anything uncertain. The learner's update rules add that facts are
routed by scope — repo-wide facts to the root `CLAUDE.md`, area facts to the
nearest in-depth area file, long explanations to `docs/` — and that no edits at
all are made if nothing in the log warrants a doc change.

Cost is tracked throughout: every SDK call reads `cfg["model"]` and passes
`cfg.get("model") or None`, so the empty-string default defers to the SDK, and
`ResultMessage.total_cost_usd` accumulates in `state["total_cost"]`.

## Related Concepts

- [[concepts/documentation-harness]] — the engines that implement the model
- [[concepts/capture-distil-synthesise-pipeline]] — how a session becomes a log
  and then output
- [[concepts/knowledge-article-schema]] — the shape the compiler emits
- [[concepts/index-guided-retrieval]] — the runtime half of the analogy
- [[concepts/compliance-compiler]] — the same analogy applied to regulation
- [[connections/harness-outputs-are-the-only-executable]] — what that means in
  this particular repository

## Sources

- `CLAUDE.md` — key decisions, incrementality, lineage
- `docs/documentation-pipeline.md` — the compiler analogy, stage 3, cost and
  model selection
- `knowledge-base/AGENTS.md` — the compiler model block and compile rules
- `claudemd-lerner/AGENTS.md` — the learner model block and update rules
