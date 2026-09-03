---
title: "The Stack Compiler"
aliases: [stack-base, scope-rank-select, st-hooks, applicability-pass]
tags: [harness, compliance, stack, tooling]
sources:
  - "daily/2026-08-27.md"
  - "stack-base/AGENTS.md"
  - "stack-base/config.json"
  - "stack-base/scripts/scope.py"
  - "stack-base/scripts/rank.py"
  - "stack-base/scripts/selection.py"
  - "stack-base/scripts/validate.py"
  - "stack-base/hooks/st-post-tooluse.py"
created: 2026-09-03
updated: 2026-09-03
---

# The Stack Compiler

`stack-base/` is a fourth engine, installed fresh in this repository on
2026-08-27. It narrows the compliance capability catalog to **one** product: a
*scoping* pass decides per capability whether this product must implement it at
all, a *ranking* pass orders that capability's catalog components best-fit-first,
a *selection* pass records the component a human chose, and a *gate* pass checks
a written PRD or PRP plan against what was recorded. The engine owns no data
artefact of its own — every write goes through `compliance-base/scripts/stack.py`.

## Key Points

- Four fixed terms, and the ownership split behind them: **capability** and
  **component** belong to [[concepts/compliance-compiler]], while
  **applicability** (does this product need it) and **ranking** (in what order do
  its components fit) are this engine's output. Ranking is an ordering, never a
  selection.
- **No agent ever picks a component.** `selection.py` runs no agent at all: it
  renders the recorded ranking as a markdown sheet, a human writes the choice,
  and a deterministic gate checks it against the closed option pool before the
  write. It needs no API key and makes no network call.
- `scope` and `rank` fan out one agent per framework, bounded by
  `max_concurrency` (12), each writing its own `.shards/` file; both **skip
  entirely** when the product description is unchanged since the recorded run,
  and `--all` overrides that skip.
- **Adversarial only where an LLM adds something.** `scope.py` runs a CHALLENGE
  agent against every "not applicable" claim; `rank.py` runs none, because its
  checkable claims (the pool matches, the licences satisfy the policy) are set
  math, which `rank_lib.ranking_gate` decides more reliably than a second model.
- `scope`, `rank` and the deep `validate` need `ANTHROPIC_API_KEY` or an OAuth
  token; `selection` and the inline hook precheck do not.
- `scripts/selection.py` is deliberately **not** named `select.py`: `scripts/` is
  first on `sys.path`, so a module named `select` shadows the stdlib `select`
  that `selectors` — and through it `asyncio` — imports, breaking `scope.py` and
  `rank.py` at import time.

## Details

The pipeline is ordered by data dependency, which is what makes one of its
commands unnecessary here: `co-capabilities` would re-derive the capability
catalog, but that catalog was already derived on 2026-07-23, so the live sequence
is `scope` → `rank` → `select`. `st-rank` cannot run first because it reads the
`applicable` flags that only `scope` writes.

Scoping is **all-or-nothing**, and deliberately so. The key set handed to the
agents is closed: every capability must get an explicit decision, a
"not applicable" must name the property of *this* product that makes it
unnecessary, and cost or effort is never grounds for a drop. The constitution
states the asymmetry outright — an unnecessary capability costs a component
choice, a wrongly dropped one costs a compliance breach, so *when in doubt,
applicable*. A single refuted claim therefore fails the whole run and writes
nothing, exiting 0 while leaving the catalog untouched; see
[[concepts/grillme-compliance-scope]] for what that looked like in practice.

The challenge pass may refute **only from the product description**, and only
with a verbatim quote carried in `evidence` — outside knowledge about the
regulation is not evidence about this product, and a merely thin reason is not a
refutation. That single rule is what turns the product description into compiler
input rather than background reading.

`hooks/st-post-tooluse.py` joins `compliance-base`'s hook in the existing
`PostToolUse` group (matcher `Write|Edit|MultiEdit`, 15s) and never interacts
with it: different install directory, different reports directory, and a
different question — component identity rather than constraint coverage. The
inline `gate_lib` precheck runs under a second with no key, reporting which
catalog components a document names and what `stack.json` says about each;
`validate.py` is spawned detached only when the document's content actually
changed and the stack carries choices to enforce. As in the compliance engine,
the agent judges intent — does the document *propose* a component or merely
mention one — while the script owns the set math and the exit code. This repo's
`validate_mode` is `warn` for both `prd` and `plan`, and an undecided capability
is pending work, never a violation.

## Related Concepts

- [[concepts/compliance-compiler]] — the sibling engine that owns capabilities,
  components, and the `stack.json` schema
- [[concepts/grillme-compliance-scope]] — the recorded result of running this
  engine against the GrillMe spec
- [[concepts/framework-filter-not-enforced]] — the `--scaffold` gotcha this
  engine's pipeline has to work around
- [[concepts/documentation-harness]] — the engines it was installed beside
- [[concepts/hook-safety-invariants]] — the hook conventions its `st-` hook obeys
- [[concepts/harness-plugin-and-engine-versions]] — how it was installed and
  versioned

## Sources

- [[daily/2026-08-27.md]] — the FRESH install (`stack-base/`, `st-` hooks merged,
  `PRP_HOME` left untouched), the 68-capability / 0-scoped / 0-chosen starting
  state, which passes need a key, and the pass sequence to run
- `stack-base/AGENTS.md` — the four terms, scoping / challenge / ranking / gate
  rules, and the boundaries
- `stack-base/scripts/*.py` — module docstrings for scope, rank, selection, and
  validate
- `stack-base/config.json` — `compliance_dir`, `max_concurrency`, `product_file`,
  `validate_mode`
- `stack-base/hooks/st-post-tooluse.py` — the inline precheck and the detached
  deep check
