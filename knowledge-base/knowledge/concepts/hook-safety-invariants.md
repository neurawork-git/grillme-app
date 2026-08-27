---
title: "Hook Safety Invariants"
aliases: [repo-guard, recursion-guard, never-crash-a-session]
tags: [harness, hooks, safety, conventions]
sources:
  - "CLAUDE.md"
  - "docs/hooks-runbook.md"
  - "docs/documentation-pipeline.md"
  - "daily/2026-08-27.md"
created: 2026-08-20
updated: 2026-08-27
---

# Hook Safety Invariants

A small set of invariants holds across every hook and script entrypoint in the
harness and is documented as non-negotiable: outputs never land under `.claude/`
or outside the repository, hooks never crash a session, state writes are atomic,
and nothing outside `daily/` and the declared outputs is ever written.

## Key Points

- **Never under `.claude/`.** Enforced in code by
  `_shared/repo_guard.py::assert_in_repo_not_dotclaude`, which resolves `..`
  before checking so traversal escapes are caught. It is re-checked at the top of
  `seed.py` / `update.py`, restated in both `AGENTS.md` files and in every LLM
  prompt. `.claude/` holds hook registration only.
- Guard violations **print `Refusing to …` rather than raising**; `flush.py`
  calls the guard before every daily-log append and logs a refusal instead of
  dropping the session.
- **Recursion guard.** Spawners set `CLAUDE_INVOKED_BY=neurawork_cc_harness` (via
  `child_env()`, or at the top of `flush.py` before the SDK import) and every
  hook entrypoint calls `recursion_guard()` — `sys.exit(0)` — **before any heavy
  import**. Checking later leaves a window in which a nested session runs the
  hooks.
- **Atomic writes** for all state and settings files: write `*.tmp`, then
  `os.replace()`, so a killed run cannot leave a half-written `state.json`.
- Hook input parsing is defensive: a failed `json.loads` is retried once with
  backslashes doubled (Windows path escaping), and any remaining failure yields
  `{}` rather than an exception.
- **On `PreToolUse` and `UserPromptSubmit`, a non-zero exit is not merely
  untidy — it is destructive.** Exit code 2 on `PreToolUse` blocks the tool
  call; a non-zero exit on `UserPromptSubmit` blocks prompt processing and
  erases the user's prompt. Both of the knowledge compiler's v3 hooks therefore
  wrap `main()` in a bare `except Exception: return` and end every path at
  `sys.exit(0)` — they fail open.

## Details

"Hooks never crash a session" is spelled out as three concrete habits: guard
first, swallow errors around optional work, and keep the `additionalContext`
print unconditional. In `SessionStart` the entire background-gate evaluation is
wrapped in a bare `except Exception: pass` carrying the comment *"injection must
always proceed"*, and a failed `Popen` raises `OSError` that is deliberately
swallowed.

The guard's scope is bounded on purpose: it governs *documentation targets* only.
An engine's own state and config legitimately live inside its own directory.
`.claude/settings.json` is touched only by an installer calling
`_shared/settings.py::merge_hooks`, which is idempotent — it recognises an
existing hook by whether a `marker` string appears in its command, updates only a
drifted command while keeping a hand-edited `timeout` and `type`, reuses an
existing `matcher: ""` group, writes atomically, and returns `False` when nothing
changed. It raises `SettingsError` and leaves the file untouched if the existing
JSON is invalid. The runbook is explicit: never hand-edit those entries when
installing or upgrading an engine.

The registered hooks began as three events × two documentation engines, each
event a single `matcher: ""` group with knowledge-base first and claudemd-lerner
second. `SessionStart` gets a 15-second timeout because it also evaluates the
background spawn gate; `PreCompact` and `SessionEnd` get 10. Every command uses
`$CLAUDE_PROJECT_DIR` rather than a hardcoded path, so the repository stays
relocatable. `.claude/settings.json` now carries six event groups: those three,
`PostToolUse` for `compliance-base/`, and the two added by knowledge-compiler
v3 — `UserPromptSubmit` (matcher `""`) and `PreToolUse` (matcher `"Skill"`),
both at a 10-second timeout.

The two v3 hooks add a second output invariant to the "never crash a session"
rule: **print nothing but the JSON envelope**. The consequences differ per
event, which is why each file states it separately — stray stdout on
`PreToolUse` breaks the JSON parse so the `additionalContext` that was built
silently fails to attach, while on `UserPromptSubmit` stray stdout *is* injected
as model-visible context, so a debug line becomes part of the prompt. Neither
hook may emit a `permissionDecision`: they inject, they never allow, deny, or
ask.

Cheapness is an invariant on these events too. `UserPromptSubmit` has no matcher
support and fires on every prompt in the repository, and `PreToolUse` would fire
on every tool call if it were registered in the catch-all group instead of its
own `Skill` group, so both hooks read no corpus files at all — see
[[concepts/kb-researcher-directive]].

## Related Concepts

- [[concepts/capture-distil-synthesise-pipeline]] — the stages these invariants
  protect
- [[concepts/background-spawn-gate]] — the gate the guard keeps from recursing
- [[concepts/documentation-harness]] — the engines that share these rules
- [[concepts/compliance-compiler]] — a fourth hook under the same conventions
- [[concepts/kb-researcher-directive]] — the two v3 hooks that must fail open
- [[concepts/harness-plugin-and-engine-versions]] — how an upgrade changes hook
  registration

## Sources

- `docs/hooks-runbook.md` — registered hooks, `merge_hooks`, recursion guard,
  safety invariants
- `CLAUDE.md` — conventions and key decisions on guards and atomic writes
- `docs/documentation-pipeline.md` — stage 1 bail-outs and hook input parsing
- [[daily/2026-08-27.md]] — that a `PreToolUse` hook must never exit non-zero
  (exit 2 blocks the tool call) and that both v3 hooks fail open
- `.claude/settings.json`, `knowledge-base/hooks/pre-skill.py`,
  `knowledge-base/hooks/user-prompt-submit.py` — the six registered groups and
  the per-event output rules
