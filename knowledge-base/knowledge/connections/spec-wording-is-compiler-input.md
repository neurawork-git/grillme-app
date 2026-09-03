---
title: "Connection: The Spec Is Compiler Input, So Its Wording Has Costs"
connects:
  - "concepts/grillme-compliance-scope"
  - "concepts/claude-credentials-and-tenancy"
  - "concepts/grillme-app-repository"
sources:
  - "daily/2026-08-27.md"
  - "stack-base/AGENTS.md"
  - ".claude/spec.md"
created: 2026-09-03
updated: 2026-09-03
---

# Connection: The Spec Is Compiler Input, So Its Wording Has Costs

## The Connection

`.claude/spec.md` was written as a document for humans: the GrillMe v1 decisions
plus the reasoning behind each one. Two engines now read it as *input*. The
knowledge compiler grounds its GrillMe articles in it, and the stack compiler
scopes GrillMe's entire compliance surface from it — `stack-base`'s state file
records `.claude/spec.md` as the product description, hashed to
`60ac023d83a582c0`. A sentence in that file is therefore not only a claim; it is
a value the passes compute against.

## Key Insight

The non-obvious part is which direction the checking ran. The compliance
challenge agent's only permitted evidence is a verbatim quote from the product
description — it may not reason from the regulation — so it cannot check the
product against GDPR. What it can do, and did, is check the description against
*itself*: it quoted a line about a shared Claude key serving several users to
refute a claim that elastic-scaling capacity planning did not apply. A
compliance-scoping tool thus surfaced a **contradiction internal to the spec**
between §3.3's shared-key wording and v1's single-user premise. It found a
documentation bug, and the fix was a documentation change: shared-key mode moved
to phase 2 in three places, which is why
[[concepts/claude-credentials-and-tenancy]] now reads differently.

The second half of the insight is the price list. Ambiguous prose cost a $1.60
run that wrote nothing, and re-wording changed the compliance surface itself —
DPO designation and governance was excluded by the first pass and applicable
after the sharpening. There is no override switch for accepting a capability
against a challenge, so the description is the *only* control surface: the way to
change a scoping outcome is to say something different, and truer, about the
product.

That inverts the usual reading of
[[connections/harness-outputs-are-the-only-executable]]. That article notes that
in a repository with no application source, every architectural fact here is a
*specified* fact rather than a verified one. The compliance pass shows the
converse: with no code to inspect, prose is what gets compiled, so prose gets
the scrutiny code would normally receive — and the parts of the spec no one had
re-read since 2026-08-20 are exactly where a machine reader found the
inconsistency.

## Evidence

- `stack-base/scripts/state.json` names `.claude/spec.md` as the product and
  records the hash the decisions in `stack.json` cite as `scoped_from`.
- `stack-base/AGENTS.md`, challenge rules 1-2: refute only from the product
  description, and only with a verbatim quote carried in `evidence`.
- The 2026-08-27 log: the first run's refutation of
  `soc2/capacity-planning-elastic-scaling` "mit einer Spec-Zeile über geteilten
  Schlüssel", the decision to sharpen the spec rather than accept the capability
  because no override exists, and the note that scoping results depend
  noticeably on the spec's formulation.
- `.claude/spec.md` §3.3 now states that v1 runs solely on the operator's own
  credential and that a shared key for several people is phase 2 and *not
  startable* in v1; §10 lists the shared key under the deferred items.
- The scoping reasons written into `stack.json` quote product properties —
  Postgres as single source of truth, MinIO holding screenshots, the gamification
  counter as the only automated evaluation — each traceable to a spec sentence.

## Related Concepts

- [[concepts/grillme-compliance-scope]]
- [[concepts/claude-credentials-and-tenancy]]
- [[concepts/grillme-app-repository]]
- [[concepts/stack-compiler]] — the passes that consume the description
- [[connections/harness-outputs-are-the-only-executable]] — the reading this
  inverts
