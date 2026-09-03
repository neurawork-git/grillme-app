---
title: "Plugin Distribution and Per-Engine Versions"
aliases: [neurawork-cc-harness, engine-version, adopt-refresh-install]
tags: [harness, install, versioning, credentials]
sources:
  - "daily/2026-08-27.md"
  - "knowledge-base/VERSION"
  - "knowledge-base/config.json"
  - "claudemd-lerner/VERSION"
  - "compliance-base/VERSION"
  - "stack-base/VERSION"
created: 2026-08-27
updated: 2026-09-03
---

# Plugin Distribution and Per-Engine Versions

The harness engines are installed into a repository from the
`neurawork-cc-harness` Claude Code plugin, and each engine carries its **own**
version number in a `VERSION` file rather than sharing one harness version. Four
engines are installed here, at three different versions: `claudemd-lerner` 5,
`compliance-base` 5, `knowledge-base` 3, and `stack-base` 2 — the last a fresh
install, the first two upgraded from 1 and 2 over the course of 2026-08-27.

## Key Points

- Installing over an existing engine is an **ADOPT/refresh**, not a fresh
  install: the existing `knowledge-base/` directory is reused and nothing it
  already contains is overwritten. Compiled articles, daily logs, and the local
  `config.json` survive an upgrade.
- Versions are per engine and drift on purpose — the four installed here sit at
  three different numbers, so "the harness version" is not a meaningful quantity
  in this repository.
- An ADOPT install is **detected**, not asked about: `existing_ldir` in the recon
  JSON tells the installer to reuse the existing directory name and its config
  rather than re-prompting. Recon's *suggestions* can be overridden — the
  learner's `claudemd_depth` was kept at 2 against a suggested 1, because the
  repo genuinely has subdirectory `CLAUDE.md` files.
- **Six of 41 `_shared` tests fail in a consumer repo.** Upstream's
  `test_manifest.py` and `test_version_check.py` expect `hooks/hooks.json`,
  `.claude-plugin/plugin.json` and `hooks/version-check.py` at the repository
  root; they are plugin-repo tests vendored into engine copies and can never
  pass outside the plugin repo. An upstream packaging bug, not an install
  failure.
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

The refresh path is also where the vendored-test bug is visible on disk, and it
is not uniform across engines. Engine 5 of the compliance compiler *deletes*
`_shared/tests/test_manifest.py` and `test_version_check.py` — they are no longer
part of that version, which is an expected removal rather than a failure — and
`stack-base` shipped without them. Both files are nonetheless still present in
`claudemd-lerner/_shared/tests/` and `knowledge-base/_shared/tests/`, so
"a fix to one `_shared/` copy must be applied to all of them" now covers four
copies, which do not agree.

Two operational habits follow from an upgrade session rather than from the
installers. Seeding can be skipped outright when the tree is clean and the engine
is already installed — only the non-destructive refresh is needed. And the
background rounds of the learner and the knowledge compiler keep writing files
*after* a commit, so `git status` is a moving target during an install session:
either wait for the round to finish or the commit split gets messy. The
2026-08-27 upgrades were split deliberately into an engine-upgrade commit
(`c78355e`) and a separate commit for the documentation files a background round
had written (`3ccead5`).

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
- [[concepts/stack-compiler]] — the fourth engine, installed fresh rather than
  adopted

## Sources

- [[daily/2026-08-27.md]] — the four install sessions: the ADOPT/refresh
  decision, the credential requirement, `existing_ldir` detection, the kept
  `claudemd_depth: 2`, the skipped seeding, the vendored plugin-repo tests and
  their removal at engine 5, and the moving `git status` during background rounds
- `knowledge-base/VERSION`, `claudemd-lerner/VERSION`,
  `compliance-base/VERSION`, `stack-base/VERSION` — `3`, `5`, `5`, `2`
- `knowledge-base/config.json` — the local config an upgrade leaves in place
