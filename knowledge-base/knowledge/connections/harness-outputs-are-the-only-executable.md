---
title: "Connection: The Only Executable in This Repo Is Its Documentation"
connects:
  - "concepts/grillme-app-repository"
  - "concepts/llm-as-compiler-model"
sources:
  - "CLAUDE.md"
  - "README.md"
  - ".claude/spec.md"
  - "knowledge-base/CLAUDE.md"
  - "docs/documentation-pipeline.md"
created: 2026-08-20
updated: 2026-08-20
---

# Connection: The Only Executable in This Repo Is Its Documentation

## The Connection

The compiler analogy calls `daily/` the source code and `CLAUDE.md` / `docs/` /
`knowledge/` the *executable*. In `grillme-app` that analogy stops being a
metaphor: there is no application source at all. The documentation the harness
produces is currently the only compiled artefact the repository has, and the
harness itself is the only running code.

## Key Insight

This inverts the usual seeding situation. A harness installed on a mature
codebase grounds its articles in code it can `Read`, `Glob`, and `Grep`; here the
"live repository" it is told to verify against is almost entirely prose — the
GrillMe v1 specification plus the harness's own `CLAUDE.md` and `AGENTS.md`
files. Every architectural fact about GrillMe in this base is therefore a
*specified* fact, not a *verified* one, and will need re-grounding against real
code once implementation starts.

The repository's own state makes that boundary explicit rather than hidden: the
spec is marked "not a line of code yet" and says this directory becomes its own
repository once implementation begins, while `knowledge-base/CLAUDE.md` records
that the base is empty and instructs against hand-authoring articles — run
`seed.py` once, then let `compile.py` maintain it.

## Evidence

- `CLAUDE.md`: "a git repository that currently contains **no application
  source**"; `README.md` holds only the project title.
- `.claude/spec.md`: "Status: Idee ausformuliert, noch keine Zeile Code."
- `docs/documentation-pipeline.md` names the outputs as the executable and states
  the consequence: documentation is never organised by hand.
- The seed rules in both constitutions insist on grounding every statement in a
  file actually read — which, in this repository, means specification prose and
  harness sources.
- `knowledge-base/CLAUDE.md`: `knowledge/index.md` contained only its table
  header, and `concepts/`, `connections/`, `qa/` did not yet exist.

## Related Concepts

- [[concepts/grillme-app-repository]]
- [[concepts/llm-as-compiler-model]]
- [[concepts/documentation-harness]]
