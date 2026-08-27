---
title: "The NeuraWork Documentation Harness"
aliases: [two-engines, claudemd-lerner, knowledge-base-engine]
tags: [harness, architecture, tooling]
sources:
  - "CLAUDE.md"
  - "docs/documentation-pipeline.md"
  - "claudemd-lerner/CLAUDE.md"
  - "knowledge-base/CLAUDE.md"
  - "knowledge-base/AGENTS.md"
  - "claudemd-lerner/AGENTS.md"
  - "daily/2026-08-27.md"
created: 2026-08-20
updated: 2026-08-27
---

# The NeuraWork Documentation Harness

The harness is a set of self-contained, per-repo engines that turn Claude Code
session transcripts into durable project documentation. Two are documented in the
root `CLAUDE.md`: `claudemd-lerner/`, the *learner*, which keeps the `CLAUDE.md`
hierarchy and the `docs/` tree current, and `knowledge-base/`, the *knowledge
compiler*, which builds the wiki under `knowledge-base/knowledge/`. A third,
`compliance-base/`, is installed alongside them.

## Key Points

- **Two engines, deliberately separate.** The learner maintains only the docs the
  agent already reads and builds no wiki; the compiler maintains only the wiki.
  Each has its own `AGENTS.md`, `config.json`, state file, and lock, so one can
  be installed without the other.
- The locks are named apart on purpose — `cl-update.lock` for the learner,
  `kc-compile.lock` for the compiler — so the two never contend. Hook filenames
  differ the same way (`cl-` prefixed vs. unprefixed).
- **`_shared/` is vendored, not shared at runtime.** Both engines carry a
  byte-identical copy, which keeps each independently installable — at the cost
  that **a fix to one copy must be applied to both**.
- Machinery is gitignored, outputs are tracked: `daily/`, `scripts/state.json`,
  the `last-*.json` stamps, lock files, `*.log`, transient context files,
  `__pycache__/`, `.venv/`, and `uv.lock` are all excluded.
- Both engines are `uv`-managed packages (`requires-python >= 3.12`) whose tests
  are stdlib `unittest` with no declared test-runner dependency.
- Engines are installed from the `neurawork-cc-harness` plugin and versioned
  **independently** of one another — see
  [[concepts/harness-plugin-and-engine-versions]]. The knowledge compiler is at
  version 3 here, which is the version that gave the engine a second job:
  injecting the `kb-researcher` directive into research workflows.

## Details

The two engines differ in where they may write. The learner draws a critical-path
split in `scripts/config.py`: `ROOT_DIR` (`<repo>/claudemd-lerner`) holds only
machinery, while `REPO_ROOT` (its parent) is where the outputs live —
`<repo>/CLAUDE.md` and `<repo>/docs/`. The knowledge compiler has no such split:
everything it produces lands under `knowledge-base/knowledge/`, so `ROOT_DIR` is
both machinery root and output root. Both roots are overridable by environment
variable (`LERNER_ROOT`, `KNOWLEDGE_ROOT`), which is how the capture hooks
redirect output out of a git worktree.

The `_shared/` package is stdlib-only and identical in both engines:
`hookio.py` (hook stdin parsing with a Windows backslash retry,
`recursion_guard()`, `child_env()`), `gitctx.py` (worktree detection and
main-checkout resolution, never raises), `repo_guard.py`
(`assert_in_repo_not_dotclaude()`), `transcript.py` (`extract_turns()`),
`settings.py` (`merge_hooks()` for idempotent hook registration), and `recon.py`
(install-time read-only recon).

A shared code convention runs through all of it: the Claude Agent SDK is imported
*lazily, inside the function that uses it*, so hook startup stays cheap and an
import-time failure cannot break a session. `scripts/` is on `sys.path` rather
than being a package, so scripts import each other flat.

The asymmetry between the engines has widened since the seed. The knowledge
compiler now ships five hooks — `session-start.py`, `session-end.py`,
`pre-compact.py`, and the v3 pair `user-prompt-submit.py` / `pre-skill.py` —
plus `scripts/research_directive.py`, a pure-stdlib module the two new hooks
share. The learner still runs the original three. Only the compiler feeds its
output back into a live session as research material, because only it produces a
corpus an agent can be pointed at.

## Related Concepts

- [[concepts/llm-as-compiler-model]] — the mental model all engines are built on
- [[concepts/capture-distil-synthesise-pipeline]] — the three stages they share
- [[concepts/hook-safety-invariants]] — the rules every entrypoint obeys
- [[concepts/compliance-compiler]] — the third engine installed here
- [[concepts/grillme-app-repository]] — the repository they are installed in
- [[connections/harness-outputs-are-the-only-executable]] — the harness output is
  the only working artefact here

## Sources

- `CLAUDE.md` — engine roles, commands, conventions, key decisions
- `docs/documentation-pipeline.md` — stage design and the compiler analogy
- `claudemd-lerner/CLAUDE.md` — the `ROOT_DIR` / `REPO_ROOT` split, local
  conventions, gotchas
- `knowledge-base/CLAUDE.md` — layout, config, local conventions, gotchas
- `knowledge-base/AGENTS.md`, `claudemd-lerner/AGENTS.md` — the two constitutions
