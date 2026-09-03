---
title: "The frameworks Filter Is Never Enforced"
aliases: [issue-46, no-scaffold-rule, orphaned-stack-keys]
tags: [compliance, gotcha, tooling, bug]
sources:
  - "daily/2026-08-27.md"
  - "compliance-base/config.json"
  - "compliance-base/scripts/stack.py"
  - "compliance-base/catalog/stack.json"
created: 2026-09-03
updated: 2026-09-03
---

# The frameworks Filter Is Never Enforced

`compliance-base/config.json` sets `"frameworks": ["gdpr"]`, but that setting
governs extraction only. `scripts/stack.py --scaffold` reads its framework set
from `catalog/capabilities.json` instead, so SOC 2 and ISO 27001 keys land in
`catalog/stack.json` regardless. The gap is filed upstream as
[issue #46](https://github.com/neurawork-git/howtobuildsoftware2026/issues/46),
"config.json `frameworks` is never enforced", and until it closes this repository
does not run `--scaffold` at all.

## Key Points

- The catalog is **kept complete on purpose**: all three frameworks stay in
  `capabilities.json`, and filtering is meant to happen when a pass processes it.
  An earlier reduction of the file to GDPR alone was reverted for that reason.
- `stack.json` currently holds only the 25 GDPR keys. A `--scaffold` run would
  rewrite the 43 orphaned soc2/iso27001 keys back in immediately, and neither
  `/st-rank` nor `/st-select` needs it — so the workaround is simply not to run it.
- The fix was pursued **upstream rather than locally**: a bug report instead of a
  local patch or a pruned catalog. A proposed `--prune` flag was withdrawn from
  the issue because pruning contradicts the keep-the-whole-catalog line.
- `--scaffold` is not destructive by design — it recomputes the machine-owned
  fields (`capability`, `framework`, `mandatory_linked`, `options`) each run and
  carries the decision-owned ones (`chosen`, `applicable`, `applicability_reason`,
  `scoped_from`, `ranked`, …) over by key, reporting keys the catalog no longer
  knows before dropping them. The problem is only *which* keys the catalog is
  taken to contain.
- `config.json` carries a second, separate list, `validate_frameworks` (empty
  here), so "which frameworks are active" is already more than one switch.

## Details

The reason the mismatch is easy to miss is that both files are legitimate inputs.
`capabilities.json` is the derived capability catalog and the natural source for
"which capabilities exist"; `config.json` is where an operator declares which
frameworks this product is being held to. `--scaffold` needs the first to build
rows and the second to decide which rows belong — and only consults the first.
The visible symptom is not an error but a `stack.json` that is quietly wider than
the configuration says, which then propagates: a scoping pass over that file
spends agent time and money deciding capabilities for frameworks nobody activated.

That is exactly what happened on the first scoping run described in
[[concepts/grillme-compliance-scope]], where 68 capabilities across three
frameworks were scoped for $1.60 and the run then failed on a SOC 2 capability
that was not supposed to be in scope in the first place. The narrower second run
covered 25.

The standing rule is therefore local and specific: no `--scaffold` in this
repository while #46 is open. It is worth noting what that costs — a genuinely
new capability added to the catalog will not appear in `stack.json` until the
rule is lifted, so the rule has to be revisited whenever
[[concepts/compliance-compiler]]'s catalog is regenerated.

## Related Concepts

- [[concepts/compliance-compiler]] — the engine that owns both files
- [[concepts/stack-compiler]] — the passes that read `stack.json` and do not need
  `--scaffold`
- [[concepts/grillme-compliance-scope]] — the run where the mismatch surfaced

## Sources

- [[daily/2026-08-27.md]] — that `--scaffold` reads frameworks from
  `capabilities.json` and not `config.json`, the no-`--scaffold` rule, the issue
  filed upstream, and the withdrawn `--prune` proposal
- `compliance-base/config.json` — `"frameworks": ["gdpr"]` and the empty
  `validate_frameworks`
- `compliance-base/scripts/stack.py` — the `--scaffold` contract: machine-owned
  fields recomputed, decision-owned fields carried over, orphans reported
- `compliance-base/catalog/stack.json` — currently 25 GDPR keys only
