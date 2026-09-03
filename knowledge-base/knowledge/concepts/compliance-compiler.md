---
title: "The Compliance Compiler"
aliases: [compliance-base, constraint-catalog, capability-catalog]
tags: [harness, compliance, tooling]
sources:
  - "compliance-base/AGENTS.md"
  - "compliance-base/catalog/index.md"
  - "compliance-base/catalog/capabilities.md"
  - "compliance-base/config.json"
  - "compliance-base/hooks/co-post-tooluse.py"
  - "compliance-base/scripts/extract.py"
  - "compliance-base/scripts/capabilities.py"
  - "compliance-base/scripts/validate.py"
  - "compliance-base/scripts/precheck.py"
  - "compliance-base/scripts/stack.py"
  - ".claude/settings.json"
  - "daily/2026-08-27.md"
created: 2026-08-20
updated: 2026-09-03
---

# The Compliance Compiler

`compliance-base/` is a third engine installed in this repository, applying the
same compiler model to regulation: it turns dense GDPR, SOC 2, and ISO/IEC 27001
prose into an atomic, machine-readable catalog of *constraints*, derives
*capabilities* from them, and checks PRP plan files against both. Frameworks are
the source, shards are the work units, the LLM is the compiler, `catalog/` is the
executable, and `validate` is the runtime.

## Key Points

- **Copyright boundary, stated first in its `AGENTS.md`:** ISO/IEC 27001 and the
  AICPA SOC 2 Trust Services Criteria are copyrighted and must never be copied
  verbatim — store the official identifier and short title plus a paraphrased
  requirement. Never invent identifiers.
- A constraint is one atomic requirement with `id`, `framework`, `title`,
  `requirement`, `applies_when`, `check`, `source_ref`, and `mandatory`. IDs are
  **stable** across re-extractions.
- `extract.py` fans out one agent per shard bounded by `max_concurrency` (12 in
  `config.json`), each writing to its own `catalog/.shards/<framework>-<key>.json`
  — per-shard temp files so no two agents ever touch the same file.
- Registered as a `PostToolUse` hook (timeout 15s) in `.claude/settings.json`; it
  fast-exits unless the tool was a `Write`/`Edit`/`MultiEdit` to
  `.claude/PRPs/plans/*.plan.md`.
- **Advisory, not legal advice and not certification** — stated explicitly in the
  constitution's conventions.
- `scripts/stack.py` is the **single schema owner** for `catalog/stack.json`,
  with four entry points: `--scaffold` to (re)generate rows, and
  `--apply-scope` / `--apply-ranking` / `--apply-selection`, through which
  [[concepts/stack-compiler]] writes everything it decides. A plain run is
  report-only and always exits 0.
- The engine is at version 5 here, upgraded from 2 on 2026-08-27 without
  re-extraction: the catalog files were already present, so `--extract` was
  skipped and roughly 30 SDK agents plus their API cost avoided.

## Details

The catalog currently checked in reports 127 GDPR constraints (109 mandatory),
160 SOC 2 (111 mandatory), and 72 ISO 27001 (59 mandatory), generated
2026-07-02, plus a derived capability layer generated 2026-07-23 with 25 GDPR,
25 SOC 2, and 18 ISO 27001 capabilities covering 109/109, 111/111, and 59/59
mandatory constraints respectively. `config.json` currently enables only `gdpr`
for extraction and sets `validate_mode` to `warn`.

Constraints and capabilities answer different questions: constraints are "what
must be proven", capabilities are "what must be built", so a plan is checked at
both levels. `capabilities.py` clusters constraints per framework and maps each
capability to 2-4 current stack components, keeping cross-framework overlap
deliberately (each framework is audited on its own) and failing the run through a
deterministic set-math gate if any mandatory constraint is uncovered. The
capability catalog applies a license/cost policy: **in-product** components must
be self-hostable OSS under product-embeddable licenses (MIT / Apache-2.0 / BSD /
MPL-2.0), while **internal-infra** components may be copyleft or free-tier
proprietary as long as they cost nothing at the start. `stack.py` then records
which component was actually chosen per `<framework>/<capability-slug>` key,
recomputing machine-owned fields each run while carrying decision-owned fields
over. Each of its three `--apply-*` entry points refuses a partial or malformed
write: scoping must cover exactly the key set with a reason for every exclusion,
a ranking must name exactly a capability's own `options` once each with a
rationale, and a selection must name a component from that entry's pool. Only
selection is deliberately partial, because it is incremental human work — and an
omission there is visible in the next gap report rather than silent.

Two things about the current install are worth recording. `config.json` activates
`gdpr` alone, but that list is not enforced by `--scaffold`
([[concepts/framework-filter-not-enforced]]), and the framework filtering is
meant to happen at processing time — the catalog itself keeps all three
frameworks even where only one is active. And the gap report is a moving
document: `reports/stack-gaps-2026-08-27.md` first read 62 of 62 mandatory-linked
capabilities unchosen, and reads 24 of 24 after the product-scoping pass narrowed
`stack.json` to GDPR — see [[concepts/grillme-compliance-scope]].

Plan checking is split by speed. `precheck.py` is pure stdlib with no LLM and
runs inline in the hook (under a second), emitting an advisory summary as
`additionalContext`; the deep semantic check is delegated to `validate.py`, which
the hook spawns detached and which writes `reports/<plan-stem>.md` plus
`reports/<plan-stem>.capabilities.json`. The agent judges applicability but never
asserts the verdict — `validate.py` computes `applicable ∩ mandatory-linked −
declared` and exits non-zero when that set is non-empty. With
`validate_mode: "block"` the hook additionally returns a block decision when
mandatory constraints are unaddressed.

## Related Concepts

- [[concepts/documentation-harness]] — the sibling engines it is installed beside
- [[concepts/hook-safety-invariants]] — the same defensive hook conventions
- [[concepts/llm-as-compiler-model]] — the compiler analogy applied to regulation
- [[concepts/grillme-app-repository]] — the repository it is installed in
- [[concepts/stack-compiler]] — the engine that narrows its catalog to one
  product and writes through `stack.py`
- [[concepts/framework-filter-not-enforced]] — the `--scaffold` / `config.json`
  mismatch
- [[concepts/grillme-compliance-scope]] — what its catalog looks like once scoped
  for GrillMe

## Sources

- `compliance-base/AGENTS.md` — copyright boundary, constraint schema, extraction
  / validation / capability rules
- `compliance-base/catalog/index.md` — current constraint and capability counts
- `compliance-base/catalog/capabilities.md` — the OSS/cost licence policy
- `compliance-base/config.json` — frameworks, `max_concurrency`, `validate_mode`
- `compliance-base/hooks/co-post-tooluse.py` — PostToolUse trigger and blocking
- `compliance-base/scripts/*.py` — module docstrings for extract, capabilities,
  validate, precheck, stack, shards
- `compliance-base/scripts/stack.py` — the four entry points and their refusal
  conditions
- `.claude/settings.json` — hook registration; the `PostToolUse` group
  (matcher `Write|Edit|MultiEdit`) now carries `stack-base`'s hook alongside it
- [[daily/2026-08-27.md]] — the version 2 → 5 upgrade with extraction skipped,
  and the `frameworks` list kept at `gdpr` although catalog files for the other
  two frameworks exist on disk
