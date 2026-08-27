---
title: "The Background Spawn Gate"
aliases: [should-compile, should-update, worktree-behaviour]
tags: [harness, hooks, worktree, gating]
sources:
  - "CLAUDE.md"
  - "docs/hooks-runbook.md"
  - "knowledge-base/CLAUDE.md"
  - "claudemd-lerner/CLAUDE.md"
created: 2026-08-20
updated: 2026-08-20
---

# The Background Spawn Gate

`SessionStart` does two things per engine: it injects current context as
`additionalContext`, and — behind an age gate — spawns the synthesis stage in the
background. `should_update()` / `should_compile()` in each engine's
`scripts/utils.py` are **pure functions** with no SDK import and no I/O, so the
hook and the tests can both call them cheaply.

## Key Points

- A run is spawned only when **all** hold: the session is not in a linked
  worktree, the newest `daily/*.md` mtime is later than the `last-*.json` stamp,
  no lock file younger than `age_hours` exists, and at least `update_age_hours` /
  `compile_age_hours` (default 6) has passed. A missing stamp counts as
  infinitely old.
- On spawn: `Popen` with `start_new_session=True`, `child_env()` (which sets
  `CLAUDE_INVOKED_BY`), output to `DEVNULL`, then the lock file is written with
  the current timestamp. An `OSError` is swallowed.
- **The spawned command is `--all`, not the incremental default**, so a
  background run reprocesses every daily log.
- The gate governs only the automatic spawn; the scripts themselves are always
  runnable by hand, and `--dry-run` lists what would be processed.
- A lock older than `age_hours` is ignored automatically; deleting
  `cl-update.lock` / `kc-compile.lock` unblocks sooner.

## Details

Worktrees are handled differently by the two hook families, on purpose. Capture
hooks **redirect**: `effective_root()` maps output into
`<main-checkout>/<engine-dir>` so the daily log and context file survive
`git worktree remove`, passing the redirect to the child via `LERNER_ROOT` /
`KNOWLEDGE_ROOT`, which `scripts/config.py` reads to override `ROOT_DIR`.
`SessionStart` instead **skips the spawn entirely** inside a worktree — a
disposable checkout should not be rewriting the main checkout's documentation.

Detection lives in `_shared/gitctx.py`, which compares `git rev-parse --git-dir`
against `git rev-parse --git-common-dir`; in the main checkout both resolve to
the same `.git`. Both values may be relative to cwd, so they are always
`resolve()`d before comparison, and every function degrades to the safe
non-worktree answer on error. `main_checkout_root()` returns `None` for bare or
otherwise unexpected layouts, and callers fall back to the local engine
directory.

What `SessionStart` injects is capped: sections joined with `\n\n---\n\n` and the
whole payload hard-capped at `MAX_CONTEXT_CHARS = 20_000` with
`\n\n...(truncated)` appended past the limit. The learner injects today's date,
the full repo-root `CLAUDE.md`, the `docs/` listing capped at 50 entries, and the
last 30 lines of the most recent daily log (searching today and yesterday only);
the knowledge compiler injects today's date, `knowledge/index.md`, and the same
daily-log tail.

## Related Concepts

- [[concepts/hook-safety-invariants]] — why a failed spawn must not surface
- [[concepts/capture-distil-synthesise-pipeline]] — the stage this gate decides
  to run
- [[connections/compile-prompt-ceiling]] — why spawning `--all` matters as the
  base grows

## Sources

- `docs/hooks-runbook.md` — the gate conditions, worktree behaviour, injection,
  and diagnostics
- `CLAUDE.md` — the "gated, locked, and worktree-aware" decision
- `knowledge-base/CLAUDE.md`, `claudemd-lerner/CLAUDE.md` — purity of
  `should_compile()` / `should_update()` and the `--all` gotcha
