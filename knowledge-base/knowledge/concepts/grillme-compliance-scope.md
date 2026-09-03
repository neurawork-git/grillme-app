---
title: "GrillMe's Scoped Compliance Stack"
aliases: [st-scope-run, scoped-stack-json, challenge-refutation]
tags: [compliance, stack, spec, decision]
sources:
  - "daily/2026-08-27.md"
  - "compliance-base/catalog/stack.json"
  - "compliance-base/reports/stack-gaps-2026-08-27.md"
  - "stack-base/scripts/state.json"
created: 2026-09-03
updated: 2026-09-03
---

# GrillMe's Scoped Compliance Stack

On 2026-08-27 the [[concepts/stack-compiler]] was run against GrillMe, using
`.claude/spec.md` itself as the product description. The recorded result is 25
GDPR capabilities in `compliance-base/catalog/stack.json`, of which **24 are
applicable** and one — `gdpr/automated-decision-making-profiling-safeguards`
(Art. 22) — is scoped out with a reason. No component has been chosen for any of
them yet.

## Key Points

- Two runs, $1.60 then $0.69 (`stack-base/scripts/state.json` records a
  cumulative $2.29). The **first run wrote nothing**: it exited 0 but the
  challenge agent refuted a "not applicable" claim, and scoping is all-or-nothing.
- The refutation was correct. The claim dropped
  `soc2/capacity-planning-elastic-scaling`; the challenge agent quoted a line of
  the spec about a shared Claude key serving several users, which contradicted it.
- The fix went **into the spec, not the tool**: shared-key mode was deferred to
  phase 2 in three places (§3.3, the `token_usage` table row, §10). There is no
  override switch for accepting a capability against a challenge, so sharpening
  the description was the only path — see
  [[concepts/claude-credentials-and-tenancy]].
- **Scoping results move with the spec's wording.** DPO designation and
  governance was excluded by the first run and is applicable after the
  sharpening; the second run's decisions all carry
  `scoped_from: "60ac023d83a582c0"`, the hash of the description they were made
  against.
- `compliance-base/reports/stack-gaps-2026-08-27.md` states the current position
  plainly: **24 of 24 applicable mandatory-linked capabilities have no chosen
  component**, which is the normal starting state, not a regression.

## Details

The scoping reasons written into `stack.json` are specific to this product rather
than generic regulation prose, which is what the constitution demands. The
accountability entry names the operator running the Compose stack as controller
and handing session content to Anthropic and Deepgram; the backup entry names
Postgres as the declared single source of truth plus MinIO holding the
screenshots. The one exclusion argues from what the agent actually does: it asks
interview questions and generates a Markdown artefact from the decision tree, and
the only automated evaluation of the user is the gamification counter of completed
sessions and answered questions, which produces no legal or similarly significant
effect. That reason leans on two facts documented in
[[concepts/grill-decision-tree]] and [[concepts/grillme-v1-scope]].

The run also crossed a catalog decision. `capabilities.json` was first reduced to
GDPR alone (2,127 deletions) and then, on request, **reverted** — the catalog
keeps all three frameworks and filtering is to happen at processing time. The
scoped `stack.json` with its 25 GDPR keys survived that revert, because
`rank.py` checks only the product hash and not the capabilities hash. The
practical consequence for this repository is a standing rule against
`stack.py --scaffold`, which would immediately write the 43 orphaned
soc2/iso27001 keys back; see
[[concepts/framework-filter-not-enforced]].

Two habits paid off and are recorded as such: checking `git status` before a
destructive catalog edit — the clean commit `8d5e406` made undoing the reduction
trivial — and reading a failed-but-zero-exit run as a real finding rather than a
tool malfunction.

## Related Concepts

- [[concepts/stack-compiler]] — the engine that produced this record
- [[concepts/compliance-compiler]] — the catalog and the schema owner behind it
- [[concepts/framework-filter-not-enforced]] — why `--scaffold` is off limits here
- [[concepts/claude-credentials-and-tenancy]] — the spec section the challenge
  agent forced open
- [[connections/spec-wording-is-compiler-input]] — the general lesson this run
  taught

## Sources

- [[daily/2026-08-27.md]] — both runs and their cost, the refuted claim and its
  evidence, the catalog reduction and revert, the hash that survived it, and the
  standing no-`--scaffold` rule
- `compliance-base/catalog/stack.json` — 25 GDPR keys with `applicable`,
  `applicability_reason` and `scoped_from`, all `chosen: null`
- `compliance-base/reports/stack-gaps-2026-08-27.md` — 25 capabilities, 1 not
  applicable, 24 unchosen, with the option pool per capability
- `stack-base/scripts/state.json` — the product hash, the product path
  (`.claude/spec.md`), and the cumulative cost
