# Hooks Runbook

Operating the two documentation engines' Claude Code hooks: what is registered,
what runs when, and how to diagnose it. For the design behind the stages, see
[documentation-pipeline.md](documentation-pipeline.md).

## Registered Hooks

`.claude/settings.json` registers six hooks — three events × two engines, each
event using a single `matcher: ""` group with both engines' commands in order
(knowledge-base first, claudemd-lerner second).

| Event | Command | Timeout |
|---|---|---|
| `SessionStart` | `uv run --directory "$CLAUDE_PROJECT_DIR/knowledge-base" python hooks/session-start.py` | 15s |
| `SessionStart` | `uv run --directory "$CLAUDE_PROJECT_DIR/claudemd-lerner" python hooks/cl-session-start.py` | 15s |
| `PreCompact` | `uv run --directory "$CLAUDE_PROJECT_DIR/knowledge-base" python hooks/pre-compact.py` | 10s |
| `PreCompact` | `uv run --directory "$CLAUDE_PROJECT_DIR/claudemd-lerner" python hooks/cl-pre-compact.py` | 10s |
| `SessionEnd` | `uv run --directory "$CLAUDE_PROJECT_DIR/knowledge-base" python hooks/session-end.py` | 10s |
| `SessionEnd` | `uv run --directory "$CLAUDE_PROJECT_DIR/claudemd-lerner" python hooks/cl-session-end.py` | 10s |

`SessionStart` gets the longer timeout because it also evaluates the background
spawn gate. All commands use `$CLAUDE_PROJECT_DIR` — never a hardcoded path — so
the repo stays relocatable.

**Never hand-edit these entries when installing or upgrading an engine.** Use
`_shared/settings.py::merge_hooks`, which takes `(event, command, timeout,
marker)` tuples and is idempotent: it recognises an existing hook by whether the
`marker` string appears in its command, updates only a drifted command (keeping
any hand-edited `timeout` and `type`), reuses an existing `matcher: ""` group,
writes atomically, and returns `False` when nothing changed. It raises
`SettingsError` and leaves the file untouched if the existing JSON is invalid.

## What SessionStart Injects

Each engine prints one JSON object on stdout:

```json
{"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": "..."}}
```

Sections are joined with `\n\n---\n\n` and the whole payload is hard-capped at
`MAX_CONTEXT_CHARS = 20_000`, with `\n\n...(truncated)` appended past the limit.

**claudemd-lerner** injects: today's date; the full repo-root `CLAUDE.md` (or a
`(none yet — run seed or let the learner build it)` placeholder); the `docs/`
listing capped at 50 entries; and the last 30 lines of the most recent daily log,
searching today and yesterday only.

**knowledge-base** injects: today's date; `knowledge/index.md` (or
`(empty — nothing compiled yet)`); and the same recent-daily-log tail.

The injection is unconditional — the gate evaluation is wrapped in a bare
`except Exception: pass` with the comment *"injection must always proceed"*.

## The Background Spawn Gate

`should_update()` / `should_compile()` in each engine's `scripts/utils.py` are
pure functions with no SDK import and no I/O, so the hook and the tests can both
call them cheaply. A run is spawned only when **all** of these hold:

- **Not in a linked worktree** — `main()` checks `repo_root(...) and not
  in_worktree(...)` before calling the gate at all.
- **New daily content exists** — the newest `daily/*.md` mtime is later than the
  `last-*.json` stamp (or there is no stamp).
- **No fresh lock** — the lock file is missing or older than `age_hours`.
- **The last run is old enough** — at least `update_age_hours` /
  `compile_age_hours` (default 6) has passed. A missing stamp counts as
  infinitely old.

On spawn: `Popen([...])` with `start_new_session=True`, `child_env()` (which sets
`CLAUDE_INVOKED_BY`), and output to `DEVNULL`; then the lock file is written with
the current timestamp. An `OSError` is swallowed — a failed spawn must not break
the session.

Note that the spawned command is `--all`, not the incremental default, so a
background run reprocesses every daily log.

## Worktree Behaviour

`_shared/gitctx.py` detects a linked worktree by comparing
`git rev-parse --git-dir` against `git rev-parse --git-common-dir`; in the main
checkout both resolve to the same `.git`. Both values may be **relative to cwd**,
so they are always `resolve()`d before comparison, and every function degrades to
the safe non-worktree answer on error — a hook must never crash the session.

The two hook families treat worktrees differently, on purpose:

- **Capture hooks redirect.** `effective_root()` maps output into
  `<main-checkout>/<engine-dir>` so the daily log and context file survive
  `git worktree remove`. The redirect is passed to the child via `LERNER_ROOT` /
  `KNOWLEDGE_ROOT`, which `scripts/config.py` reads to override `ROOT_DIR`.
- **SessionStart skips the spawn entirely** inside a worktree — a disposable
  checkout should not be rewriting the main checkout's documentation.

`main_checkout_root()` returns `None` for bare or otherwise unexpected layouts,
and callers fall back to the local engine directory.

## Recursion Guard

`update.py`, `compile.py`, `flush.py`, and `query.py` all invoke the Claude Agent
SDK, which starts a nested Claude Code — which would fire these same hooks again.

The guard: spawners set `CLAUDE_INVOKED_BY=neurawork_cc_harness` (via
`child_env()`, or directly at the top of `flush.py` before the SDK import), and
every hook entrypoint calls `recursion_guard()` — `sys.exit(0)` if the variable
is set — **before any heavy import or work**. Preserve that ordering in any new
hook; checking later leaves a window where a nested session runs the hooks.

## Diagnostics

**Where to look**

| Symptom | Check |
|---|---|
| No daily log appearing | `<engine>/scripts/flush.log` — the hooks discard stdout/stderr, so this is the only trace |
| Flush ran but wrote nothing | `flush.log` shows `Result: FLUSH_OK` — the model judged the session not doc-worthy |
| Flush errored | A `Memory Flush` entry in `daily/<date>.md` plus an ERROR line in `flush.log` |
| Background run never fires | Compare `scripts/last-update.json` / `last-compile.json` against `daily/*.md` mtimes, and check for a fresh `cl-update.lock` / `kc-compile.lock` |
| Nothing at all happens | Confirm you are not in a linked worktree, and that `CLAUDE_INVOKED_BY` is unset in your shell |

**Run a hook by hand.** Hooks read JSON from stdin, so they can be exercised
directly:

```bash
echo '{"session_id":"manual","transcript_path":"/path/to/transcript.jsonl"}' \
  | uv run --directory claudemd-lerner python hooks/cl-session-end.py
```

`SessionStart` needs no meaningful payload — run it to see exactly what gets
injected:

```bash
echo '{}' | uv run --directory claudemd-lerner python hooks/cl-session-start.py
echo '{}' | uv run --directory knowledge-base  python hooks/session-start.py
```

**Force a run, ignoring the gate.** The gate only governs the automatic spawn;
the scripts themselves are always runnable:

```bash
uv run --directory claudemd-lerner python scripts/update.py --dry-run
uv run --directory claudemd-lerner python scripts/update.py --all
uv run --directory knowledge-base  python scripts/compile.py --all
```

**Clear a stuck lock.** A lock older than `age_hours` is ignored automatically;
delete it to unblock sooner:

```bash
rm -f claudemd-lerner/scripts/cl-update.lock knowledge-base/scripts/kc-compile.lock
```

**Leftover context files.** `flush.py` unlinks its input on every exit path, so
`scripts/session-flush-*.md` or `scripts/flush-context-*.md` files hanging around
mean a flush was killed mid-run. They are gitignored and safe to delete.

## Safety Invariants

These hold across every entrypoint and must not be relaxed:

- **Outputs never land under `.claude/`**, and never outside the repository.
  `_shared/repo_guard.py::assert_in_repo_not_dotclaude` resolves `..` before
  checking, so traversal escapes are caught. `seed.py` and `update.py` call it up
  front and print `Refusing to …` rather than raising; `flush.py` calls it before
  every daily-log append and logs a refusal instead. The guard governs
  documentation targets only — an engine's own state and config legitimately live
  in its directory.
- **Hooks never crash a session.** Guard first, swallow errors around optional
  work, keep the `additionalContext` print unconditional.
- **State writes are atomic** — `*.tmp` then `os.replace()` — so a killed run
  cannot leave a half-written `state.json` or settings file.
- **Nothing outside `daily/` and the declared outputs is ever written** by the
  engines. `.claude/settings.json` is touched only by an installer calling
  `merge_hooks`.
