---
title: "Capture, Distil, Synthesise"
aliases: [three-stage-pipeline, flush-pipeline]
tags: [harness, pipeline, hooks]
sources:
  - "CLAUDE.md"
  - "docs/documentation-pipeline.md"
  - "docs/hooks-runbook.md"
  - "claudemd-lerner/CLAUDE.md"
created: 2026-08-20
updated: 2026-08-20
---

# Capture, Distil, Synthesise

Both documentation engines share the same three-stage shape. **Capture**:
`SessionEnd` and `PreCompact` hooks read the Claude Code JSONL transcript,
extract recent turns to a context file, and `Popen` a background `flush.py` — no
API call happens in the hook. **Distil**: `flush.py` makes one text-only SDK call
that condenses the session into an entry appended to `<engine>/daily/<date>.md`.
**Synthesise**: `update.py` or `compile.py` feeds the daily logs plus the live
repository to the SDK, which edits the output files directly.

## Key Points

- `extract_turns()` keeps only `user`/`assistant` text, takes the last 30 turns,
  and truncates to 15,000 characters *from the end*, snapping forward to the next
  `\n**` so the context never starts mid-turn.
- Turn thresholds differ by hook: `MIN_TURNS_TO_FLUSH` is 1 for SessionEnd and 5
  for PreCompact — a compaction only matters if the session was already
  substantial.
- `flush.py` is text-only (`allowed_tools=[]`, `max_turns=2`) and has three
  outcomes: `FLUSH_OK` or blank appends nothing, `FLUSH_ERROR` is appended under
  a `Memory Flush` heading and logged at ERROR, anything else is appended under a
  `Session` heading with an `HH:MM` timestamp.
- A **60-second dedup window** keyed on `session_id`
  (`scripts/last-flush.json`) prevents a double entry when SessionEnd and
  PreCompact fire back to back.
- Because the hooks send stdout and stderr to `DEVNULL`, `scripts/flush.log` is
  the only record of what stage 2 did.

## Details

Capture bails out early and often: it exits immediately if
`CLAUDE_INVOKED_BY` is set, if `transcript_path` is not a non-empty string
pointing at an existing file (`PreCompact` is documented to sometimes pass an
empty one), or if the extracted result is empty or under the turn threshold.
Context files are named `<engine>/scripts/<prefix><session_id>-<stamp>.md` with
`session-flush-` for SessionEnd and `flush-context-` for PreCompact, and
`flush.py` `unlink`s its input on every exit path — leftovers mean a flush was
killed mid-run.

The distil prompts differ slightly per engine. The learner asks for `**Context:**`,
`**Conventions / Architecture:**`, `**Decisions Made:**`, `**Commands:**` and
`**Lessons Learned:**`; the compiler's variant asks for `**Key Exchanges:**` and
`**Action Items:**` instead of commands. Both instruct the model to skip routine
tool calls, file reads, and trivial back-and-forth, and to omit any section that
would be empty.

Stage 0 is seeding, run once at install time in the foreground. Both `seed.py`
scripts refuse to run outside a git repository, refuse to run when
`git status --porcelain` shows changes outside their own engine directory,
re-assert the write guard on their output targets, assemble repo context (README
capped at 8,000 chars, existing `CLAUDE.md` files, the `docs/` listing capped at
50 entries, and the non-hidden top-level entries), and stamp
`last-update.json` / `last-compile.json` so the SessionStart gate does not fire
immediately afterwards.

## Related Concepts

- [[concepts/documentation-harness]] — the engines running these stages
- [[concepts/llm-as-compiler-model]] — why the stages are shaped this way
- [[concepts/hook-safety-invariants]] — the rules stage 1 must never break
- [[concepts/background-spawn-gate]] — what decides whether stage 3 runs

## Sources

- `CLAUDE.md` — the three-stage summary and the `_shared/` helper table
- `docs/documentation-pipeline.md` — stages 0-3 in detail, flush outcomes,
  incrementality
- `docs/hooks-runbook.md` — registered hooks, timeouts, diagnostics
- `claudemd-lerner/CLAUDE.md` — dedup window, turn thresholds, flush logging
