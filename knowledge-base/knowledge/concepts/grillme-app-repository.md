---
title: "grillme-app Repository"
aliases: [grillme-app, repository-purpose]
tags: [repo, purpose, overview]
sources:
  - "CLAUDE.md"
  - "README.md"
  - ".claude/spec.md"
  - ".claude/settings.json"
created: 2026-08-20
updated: 2026-08-20
---

# grillme-app Repository

`grillme-app` is a git repository that currently contains **no application
source**. Its `README.md` holds only the project title. What is checked in today
is two things: the written specification for the GrillMe product, and the
NeuraWork Claude Code documentation harness that maintains this repository's own
documentation.

## Key Points

- The root `CLAUDE.md` states plainly that the repo holds no application source;
  `README.md` contains nothing but the project title.
- `.claude/spec.md` holds the GrillMe v1 specification, written up on
  2026-08-20 and explicitly marked *"noch keine Zeile Code"* (not a line of code
  yet).
- Three self-contained engines are installed as subdirectories:
  `claudemd-lerner/`, `knowledge-base/`, and `compliance-base/`.
- All engine output lands **inside the repository, never under `.claude/`**;
  `.claude/` holds hook registration (`settings.json`) and the spec only.
- The spec notes that this directory becomes its own repository once
  implementation starts.

## Details

The repository's tracked content splits cleanly in two. The first half is
documentation *about a product that does not exist yet* — the GrillMe v1
specification in `.claude/spec.md`, which records not only the decisions but the
reasoning behind each one, so that later changes know what they are arguing
against. The second half is the machinery that writes documentation: the
[[concepts/documentation-harness]] engines, plus the `docs/` tree and the root
`CLAUDE.md` those engines maintain.

The layout given in the root `CLAUDE.md` is `README.md`, `CLAUDE.md`, `docs/`,
`.claude/settings.json` (hook registration, never written by the engines), and
the engine directories. `.claude/settings.json` additionally registers a
`PostToolUse` hook for `compliance-base/`, an engine the root `CLAUDE.md`
architecture section does not yet describe — see
[[concepts/compliance-compiler]].

Both documentation engines are `uv`-managed Python packages requiring Python
≥ 3.12, and every documented command is run from the repository root, e.g.
`uv run --directory knowledge-base python scripts/compile.py`.

## Related Concepts

- [[concepts/grillme-v1-scope]] — the product this repository is named for
- [[concepts/grillme-architecture]] — the stack the spec commits to
- [[concepts/documentation-harness]] — the engines checked in here today
- [[connections/harness-outputs-are-the-only-executable]] — why docs are the
  only working artefact in the repo right now

## Sources

- `CLAUDE.md` — project purpose, architecture tree, engine commands
- `README.md` — confirms the repo holds only a title
- `.claude/spec.md` — GrillMe v1 specification and its status line
- `.claude/settings.json` — the registered hooks, including compliance-base
