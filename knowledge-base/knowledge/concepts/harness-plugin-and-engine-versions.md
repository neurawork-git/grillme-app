---
title: "Plugin Distribution and Per-Engine Versions"
aliases: [neurawork-cc-harness, engine-version, adopt-refresh-install]
tags: [harness, install, versioning, credentials]
sources:
  - "daily/2026-08-27.md"
  - "knowledge-base/VERSION"
  - "knowledge-base/config.json"
created: 2026-08-27
updated: 2026-08-27
---

# Plugin Distribution and Per-Engine Versions

The harness engines are installed into a repository from the
`neurawork-cc-harness` Claude Code plugin, and each engine carries its **own**
version number in a `VERSION` file rather than sharing one harness version. On
2026-08-27 this repository's `knowledge-base/` was taken to engine version 3;
the log records `claudemd-lerner` at 1 and `compliance-compiler` at 2, both with
version 5 available, as an open follow-up.

## Key Points

- Installing over an existing engine is an **ADOPT/refresh**, not a fresh
  install: the existing `knowledge-base/` directory is reused and nothing it
  already contains is overwritten. Compiled articles, daily logs, and the local
  `config.json` survive an upgrade.
- Versions are per engine and drift on purpose — the three installed here sit at
  three different numbers, so "the harness version" is not a meaningful quantity
  in this repository.
- An upgrade changes machinery *and* hook registration: v3 of the knowledge
  compiler added two new entrypoints and two new groups in
  `.claude/settings.json` — see [[concepts/kb-researcher-directive]].
- **Credentials are the engine's own.** Compiler API calls require an
  `ANTHROPIC_API_KEY` or a `CLAUDE_CODE_OAUTH_TOKEN` in the environment;
  subscription credentials are not sanctioned for use by third-party plugins.
- The invariant that survives every install path: knowledge lives in the
  repository under `knowledge-base/`, never under `.claude/`.

## Details

The ADOPT path is what makes the engines safe to re-run. Because each engine is
self-contained — its own constitution, `config.json`, state file, and lock — an
upgrade replaces scripts and hooks while leaving the two things that cannot be
regenerated: the `daily/` logs, which are the source code in the compiler model,
and `knowledge/`, the compiled output. The seed scripts' refusal to run with
unrelated working-tree changes and the write guard on output targets point the
same way; see [[concepts/hook-safety-invariants]].

The credential requirement is a consequence of distribution rather than of
design. An engine running inside an interactive Claude Code session inherits
that session's context, but its background stages are ordinary subprocesses
calling the Claude Agent SDK on their own account, and a plugin shipped by a
third party is not sanctioned to spend the user's subscription credentials. The
practical effect is that the automatic background compile silently produces
nothing in an environment where neither variable is set, while the interactive
`SessionStart` context injection — which makes no API call — keeps working. It
is a different concern from the tenancy coupling in
[[concepts/claude-credentials-and-tenancy]], which is about the GrillMe product,
but the two share a shape: which credential is present decides what is allowed
to run.

Version drift across engines has a documentation cost that is already visible.
`knowledge-base/CLAUDE.md` still describes `VERSION` as `"1"`, three hooks, and
an empty base, none of which hold after the v3 upgrade and the first compile —
the learner maintains that file, and the compiler does not touch it.

## Related Concepts

- [[concepts/kb-researcher-directive]] — what engine version 3 added
- [[concepts/documentation-harness]] — the engines being versioned
- [[concepts/hook-safety-invariants]] — the write and registration rules an
  upgrade must preserve
- [[concepts/claude-credentials-and-tenancy]] — the product-side credential
  switch, a separate question with the same shape

## Sources

- [[daily/2026-08-27.md]] — the plugin upgrade session, the ADOPT/refresh
  decision, the credential requirement, and the open upgrades for the other two
  engines
- `knowledge-base/VERSION` — currently `3`
- `knowledge-base/config.json` — the local config an upgrade leaves in place
