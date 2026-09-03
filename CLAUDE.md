# CLAUDE.md — grillme-app

## Project Purpose

`grillme-app` is a git repository that currently contains **no application
source**. Its `README.md` holds only the project title. The product itself — an
interview agent that grills an idea into a requirements document — is specified
in German in `.claude/spec.md`, which is also the *product description of record*
the stack compiler scopes against.

What is checked in today is the NeuraWork Claude Code harness: self-contained,
per-repo engines installed from the `neurawork-cc-harness` plugin (0.6.0).

- **`claudemd-lerner/`** (engine 5) — the *learner*. Keeps this CLAUDE.md
  hierarchy and the `docs/` tree current from session logs.
- **`knowledge-base/`** (engine 3) — the *knowledge compiler*. Builds and
  maintains a structured, queryable wiki under `knowledge-base/knowledge/`.
- **`compliance-base/`** (engine 5) — the *compliance compiler*. Extracts
  GDPR/SOC 2/ISO 27001 prose into a machine-readable constraint catalog, derives
  capabilities from it, and validates PRP plans against it. It also owns
  `catalog/stack.json` and is its only writer.
- **`stack-base/`** (engine 2) — the *stack compiler*. Decides which of those
  capabilities apply to this product, ranks the candidate components, records the
  chosen one, and gates documents against the result.

All are installed as subdirectories of the repo they serve, and all write
their outputs **inside this repository, never under `.claude/`**.

## Commands

The engines are `uv`-managed Python packages (`requires-python >= 3.12`). Every
command below is run from the repository root. After installing or upgrading an
engine, sync its dependencies:

```bash
uv sync --directory knowledge-base
uv sync --directory claudemd-lerner
uv sync --directory compliance-base
uv sync --directory stack-base
```

Compile, query, update, seed, extract, scope, rank and deep validate call the
Claude Agent SDK and therefore need `ANTHROPIC_API_KEY` or
`CLAUDE_CODE_OAUTH_TOKEN` in the environment; capture (the hooks and
scaffolding), the inline prechecks and the whole of `st-select` work without
either. **Subscription credentials are not sanctioned for third-party plugins** —
use a real API key or OAuth token.

The plugin also exposes the engines as skills and slash commands — invoke them
**fully qualified** (`/neurawork-cc-harness:kc-compile`,
`neurawork-cc-harness:knowledge-compiler`) so they resolve regardless of what
else is enabled.

### claudemd-lerner (CLAUDE.md + docs/)

```bash
# Seed/refresh the whole doc tree from the repo itself (foreground, run once)
uv run --directory claudemd-lerner python scripts/seed.py

# Apply new/changed daily logs to CLAUDE.md + docs/
uv run --directory claudemd-lerner python scripts/update.py
uv run --directory claudemd-lerner python scripts/update.py --all
uv run --directory claudemd-lerner python scripts/update.py --dry-run

# Distil one captured session into daily/<date>.md (normally hook-spawned)
uv run --directory claudemd-lerner python scripts/flush.py <context_file.md> <session_id>
```

### knowledge-base (knowledge wiki)

```bash
# Seed the initial articles from the repo itself (foreground, run once)
uv run --directory knowledge-base python scripts/seed.py

# Compile daily logs into articles
uv run --directory knowledge-base python scripts/compile.py
uv run --directory knowledge-base python scripts/compile.py --all
uv run --directory knowledge-base python scripts/compile.py --file daily/2026-06-18.md
uv run --directory knowledge-base python scripts/compile.py --dry-run

# Ask the base a question (index-guided retrieval)
uv run --directory knowledge-base python scripts/query.py "How do we handle auth redirects?"
uv run --directory knowledge-base python scripts/query.py "What is our error strategy?" --file-back

# Health checks -> knowledge-base/reports/lint-<date>.md
uv run --directory knowledge-base python scripts/lint.py
uv run --directory knowledge-base python scripts/lint.py --structural-only
```

`lint.py` exits `1` when any **error**-severity issue is found, `0` otherwise.
A new knowledge article must be registered in `knowledge-base/knowledge/index.md`
or `lint.py` fails.

### compliance-base (constraint catalog + plan validation)

```bash
# Slash commands (preferred)
/neurawork-cc-harness:co-extract          # (re)extract the framework catalog
/neurawork-cc-harness:co-capabilities     # derive capabilities from constraints
/neurawork-cc-harness:co-validate <plan>  # validate one PRP plan

# stack.json is written only through this script — never by hand, never by stack-base
uv run --directory compliance-base python scripts/stack.py --scaffold
```

### stack-base (capability scoping, ranking, selection)

The passes run in a fixed order — **scope → rank → select → validate**:

```bash
/neurawork-cc-harness:st-scope            # which capabilities apply, and why not
/neurawork-cc-harness:st-rank             # order each capability's components
/neurawork-cc-harness:st-select           # record the chosen component (--apply)
/neurawork-cc-harness:st-validate <doc>   # gate a PRD/plan against the recorded stack

# Direct invocation; --product overrides the default <stack_dir>/product.md
uv run --directory stack-base python scripts/scope.py --product .claude/spec.md
uv run --directory stack-base python scripts/rank.py
uv run --directory stack-base python scripts/selection.py --dry-run
```

### Test

The `_shared/` tests are stdlib `unittest`, no test runner is declared as a
dependency — **there is no pytest anywhere in this repo**:

```bash
uv run --directory claudemd-lerner python -m unittest discover -s _shared/tests -t .
uv run --directory knowledge-base  python -m unittest discover -s _shared/tests -t .
uv run --directory compliance-base python -m unittest discover -s _shared/tests -t .
uv run --directory stack-base      python -m unittest discover -s _shared/tests -t .
```

`claudemd-lerner` and `knowledge-base` each report 6 of 41 tests erroring **by
design**: `_shared/tests/test_manifest.py` and `test_version_check.py` are
plugin-repo tests that were vendored into those two engine copies and look for
`hooks/hooks.json`, `.claude-plugin/plugin.json` and `hooks/version-check.py` at
the repository root. This is an upstream packaging bug, not an install failure —
engine 5 dropped both files, which is why `compliance-base` and `stack-base` do
not carry them.

### Lint

Both `pyproject.toml` files configure Ruff (`[tool.ruff] line-length = 100`).
Ruff is **not** a declared dependency of either package — run it from your own
environment; it picks up the config from the package directory it is pointed at.

## Architecture

```
grillme-app/
├── README.md
├── CLAUDE.md                  ← this file (learner output)
├── docs/                      ← long-form guides (learner output)
├── .claude/
│   ├── settings.json          ← hook registration (NEVER written by the engines)
│   ├── spec.md                ← the GrillMe product spec (scoping input of record)
│   └── PRPs/                  ← PRP_HOME: prp-core writes prds/ and plans/ here
├── claudemd-lerner/           ← learner engine (see its CLAUDE.md)
├── knowledge-base/            ← knowledge compiler (see its CLAUDE.md)
├── compliance-base/           ← compliance compiler (see its CLAUDE.md)
└── stack-base/                ← stack compiler (see its CLAUDE.md)
```

`PRP_HOME` is set to `.claude/PRPs` in `.claude/settings.json` so prp-core writes
plans into this repository instead of `~/.prp`. Validation covers both
`.claude/PRPs/plans/*.plan.md` and the `PRP_HOME` store layout
`.claude/PRPs/<repo>-<hash>/plans/*.plan.md`.

The learner and the knowledge compiler share the same three-stage shape:

1. **Capture** — `SessionEnd` and `PreCompact` hooks read the Claude Code JSONL
   transcript, extract the recent turns, write them to a context file, and
   `Popen` a background `flush.py`. No API calls happen in the hook itself.
2. **Distil** — `scripts/flush.py` makes a text-only Claude Agent SDK call that
   condenses the session into an entry appended to `<engine>/daily/<date>.md`
   (append-only source of truth; gitignored).
3. **Synthesise** — `scripts/update.py` (learner) or `scripts/compile.py`
   (compiler) feeds the daily logs plus the live repository to the SDK, which
   edits the output files directly with `Read/Write/Edit/Glob/Grep` under
   `permission_mode="acceptEdits"`.

`SessionStart` does two things per engine: injects current context
(`additionalContext`) and, behind an age gate, spawns stage 3 in the background.

The knowledge compiler registers two further, capture-unrelated hooks —
`UserPromptSubmit` and `PreToolUse` (matcher `Skill`) — which inject a directive
telling the session to spawn `kb-researcher` as a **fourth research axis** next
to prp-core's `codebase-explorer`, `codebase-analyst` and `web-researcher`, so
PRDs and plans start from what the repo already learned. See
[docs/hooks-runbook.md](docs/hooks-runbook.md).

The compliance and stack compilers share a different shape — a chain of passes
over one artifact:

```
frameworks → constraints → capabilities → applicability → ranking → selection → gate
  (prose)     co-extract   co-capabilities  st-scope       st-rank    st-select   st-validate
```

Everything from `applicability` rightwards is stored in
`compliance-base/catalog/stack.json`. `stack-base` owns **no data artifact of its
own**: every write goes through `compliance-base/scripts/stack.py`, the single
schema owner. The validate gate only ever *reads* the recorded stack.

### Major components

| Path | Role |
|---|---|
| `claudemd-lerner/AGENTS.md` | Constitution the learner LLM follows (where things go, update/seed rules) |
| `claudemd-lerner/config.json` | `claudemd_depth`, `docs_dir`, `language`, `excluded_dirs`, `update_age_hours`, `model` |
| `claudemd-lerner/hooks/cl-*.py` | SessionStart / SessionEnd / PreCompact entrypoints |
| `claudemd-lerner/scripts/` | `seed.py`, `update.py`, `flush.py`, `config.py`, `utils.py` |
| `knowledge-base/AGENTS.md` | Constitution the compiler LLM follows (article formats, compile/query/lint rules) |
| `knowledge-base/config.json` | `knowledge_dir`, `compile_age_hours`, `model`, `research_directive`, `research_skill_match`, `research_prompt_match` |
| `knowledge-base/hooks/*.py` | SessionStart / SessionEnd / PreCompact plus the two research-directive entrypoints |
| `knowledge-base/scripts/` | `seed.py`, `compile.py`, `query.py`, `lint.py`, `flush.py`, `research_directive.py`, `config.py`, `utils.py` |
| `compliance-base/AGENTS.md` | Constitution for catalog extraction and PRP-plan validation |
| `compliance-base/catalog/` | `<framework>.json` constraints, `capabilities.json`/`.md`, `index.md`, and `stack.json` |
| `compliance-base/scripts/stack.py` | **Single schema owner of `catalog/stack.json`** — scaffold, apply-scope/ranking/selection, gap report |
| `stack-base/AGENTS.md` | Constitution the scoping, challenge and ranking agents follow |
| `stack-base/scripts/` | `scope.py`, `rank.py`, `selection.py`, `validate.py` plus their `*_lib.py` halves and `gate_lib.py` |
| `knowledge-base/knowledge/index.md` | Master catalog — read first by both the compiler and the query engine |
| `<engine>/_shared/` | Stdlib-only helpers, vendored identically into every engine |

### `_shared/` helpers (identical in every engine)

| Module | Responsibility |
|---|---|
| `hookio.py` | Hook stdin parsing (with a Windows backslash retry), `recursion_guard()`, `child_env()` |
| `gitctx.py` | Worktree detection and main-checkout resolution; never raises |
| `repo_guard.py` | `assert_in_repo_not_dotclaude()` — the in-repo / not-`.claude/` write guard |
| `transcript.py` | `extract_turns()` — JSONL transcript → last N markdown turns |
| `settings.py` | `merge_hooks()` — idempotent hook registration into `.claude/settings.json` |
| `recon.py` | Install-time read-only recon, emits a `RECON_JSON`-delimited blob |

Longer explanations live in [docs/documentation-pipeline.md](docs/documentation-pipeline.md)
and [docs/hooks-runbook.md](docs/hooks-runbook.md).

## Conventions

- **Python ≥ 3.12**, `from __future__ import annotations` at the top of every
  module, modern type hints (`str | None`, `list[Path]`).
- **Hooks and `_shared/` are pure stdlib.** The Claude Agent SDK is imported
  *lazily, inside the function that uses it* (see `scripts/flush.py`,
  `update.py`, `compile.py`) so hook startup stays cheap and import-time
  failures cannot break a session.
- **Hooks must never crash a session.** Call `recursion_guard()` before any
  heavy import, swallow errors around optional work, and keep the
  `additionalContext` print unconditional.
- **Atomic writes** for all state and settings files: write `*.tmp`, then
  `os.replace()`.
- **No hardcoded timezone.** Local time comes from
  `datetime.now(timezone.utc).astimezone()`; dates are ISO 8601 (`YYYY-MM-DD`),
  timestamps full ISO with offset.
- **File names** lowercase and hyphenated; documentation prose is factual,
  neutral, and instructive — these are docs an agent reads.
- **Markdown headings stay stable across updates** so diffs remain readable.
- **Marker blocks are owned by their tool.** Text between
  `<!-- owner:name BEGIN … -->` and `<!-- owner:name END -->` — such as the
  `neurawork-cc-harness:rules` block at the foot of this file — belongs to the tool
  that wrote it (`claudemd-lerner/scripts/markers.py` guards the learner's span).
  Read it, never reword or reorder it. The corollary: content *outside* the markers
  is hand-maintainable and is **not** kept in sync with it, so a fact stated in both
  places can silently drift — this file's `### Test` fence and the rules block's
  test list are exactly that pair.
- **Machinery is gitignored, outputs are tracked.** Each engine's `.gitignore`
  excludes `daily/`, `scripts/state.json`, the `last-*.json` stamps, the lock
  files, `*.log`, the transient `session-flush-*.md` / `flush-context-*.md`
  context files, `__pycache__/`, `.venv/`, and `uv.lock`.

## Key Decisions

**Documentation is never organised by hand.** Sessions produce append-only logs;
an LLM does the synthesis and upkeep. `daily/` is the source code, the LLM is
the compiler, `CLAUDE.md`/`docs/`/`knowledge/` are the executable output.

**Two engines, deliberately separate.** The learner maintains *only* the docs the
agent already reads (`CLAUDE.md`, `docs/`); it builds no wiki. The compiler
maintains *only* the wiki. Each has its own `AGENTS.md`, `config.json`, state,
and lock, so one can be installed without the other.

**`_shared/` is vendored, not shared at runtime.** Every engine carries its own
copy. This keeps each engine a self-contained, independently installable unit at
the cost of duplicating the helpers — **a fix to one copy must be applied to all
of them.** The copies are not in lockstep across engine versions: the two
documentation engines still ship `test_manifest.py` and `test_version_check.py`,
which engine 5 removed.

**Outputs never live under `.claude/`.** This is a hard product constraint,
enforced in code by `_shared/repo_guard.py`, re-checked at the top of
`seed.py`/`update.py`, and restated in both `AGENTS.md` files and every LLM
prompt. `.claude/` holds hook registration only.

**No RAG.** At repo scale (tens to a few hundred articles) an LLM reasoning over
a curated `index.md` beats vector similarity — embeddings match similar words,
the LLM matches relevant meaning. No embeddings, no chunking, no vector store
until a base passes roughly 2,000 articles / ~2M tokens.

**Prefer UPDATE over CREATE, and `Edit` over rewrite.** The learner edits docs
surgically to preserve hand-written content and keep diffs readable; the
compiler updates an existing article rather than creating a near-duplicate.

**Incremental by content hash.** `update.py` and `compile.py` track the first 16
hex chars of each daily log's SHA-256 in `scripts/state.json` and reprocess only
what changed.

**Background work is gated, locked, and worktree-aware.** `SessionStart` spawns a
background run only when the last run is at least `*_age_hours` old (default 6),
there is genuinely new daily content, no fresh lock is held, and the session is
in the main checkout — not a linked worktree. Capture from a worktree is
redirected into the main checkout so it survives `git worktree remove`.

**Hook filenames are prefixed, hook groups are shared deliberately.** All four
engines coexist in one `.claude/settings.json`, kept apart by a per-engine
filename prefix — `cl-` (learner), unprefixed (knowledge), `co-` (compliance),
`st-` (stack) — so an installer's `merge_hooks` recognises its own entry and never
overwrites another's. Groups are shared only where the engines genuinely want the
same event: `co-post-tooluse.py` and `st-post-tooluse.py` sit together under
`PostToolUse` with `matcher: "Write|Edit|MultiEdit"`. The knowledge compiler's
`PreToolUse` entry has its own `matcher: "Skill"` group — never `matcher: ""`,
which would spawn a process on every tool call.

**Runtime config is read live.** The knowledge compiler's `research_directive`
kill switch and the two match patterns live in `knowledge-base/config.json` and
are read on every hook invocation, so flipping them needs no installer re-run.
Disabling the switch stops the injection but keeps the hooks; removing the
feature entirely means deleting the two hook entries from `.claude/settings.json`.

**Recursion guard.** Any Claude Code the SDK spawns is marked with
`CLAUDE_INVOKED_BY=neurawork_cc_harness`; hooks see it and exit immediately, so
a background compile cannot re-trigger the hooks that started it.

**Seeds refuse to run on a dirty tree.** Both `seed.py` scripts abort if
`git status --porcelain` shows changes outside their own engine directory, so a
seed never writes over uncommitted work.

**The catalog stays complete; `config.json` filters at processing time.**
`compliance-base/catalog/capabilities.json` is the full catalog and keeps every
framework. Narrowing the active surface is what `frameworks` in `config.json` is
for (currently `["gdpr"]`) — never prune the catalog, which is lossy and
irreversible without git. Extraction for soc2/iso27001 has already been paid for;
the files stay.

**Copyright boundary.** ISO/IEC 27001 and the SOC 2 Trust Services Criteria are
copyrighted, so the catalog stores only official control identifiers, short
titles, and paraphrased requirements — never the source text.

**Partial selection is a feature.** `st-select` is deliberately partial: an
undecided capability stays a *counted gap* in the report rather than a silent
omission. The same asymmetry runs through the scoping rules — when in doubt, a
capability is applicable, because an unnecessary capability costs a component
choice while a wrongly-dropped one costs a compliance breach.

**Lineage.** The knowledge compiler is a repo-local implementation of the
LLM-as-compiler idea (Andrej Karpathy's LLM wiki, rebuilt openly by coleam00's
claude-memory-compiler); the learner adds the doc-maintenance pattern from
NeuraWork's own coding-suite learner. The designs are independent NeuraWork
work; only the underlying concept is shared.

<!-- neurawork-cc-harness:rules BEGIN (auto-managed — re-run /neurawork-cc-harness:nw-rules-init to refresh) -->
### Coding Discipline

- **Scope** — touch only what the request requires; leave neighbouring code, formatting and
  working sections alone. Remove only the orphans your change created; name pre-existing dead
  code instead of deleting it.
- **Simplicity** — write the minimum that solves the problem. No speculative features, no
  abstraction for a single use, no configurability nobody asked for.
- **Pull requests** — open and merge every PR with `/neurawork-cc-harness:nw-ship-pr`. Another
  PR skill or a bare `gh pr create` skips its review, validation and approval gates.
- **Evaluation first** — a behaviour change starts with a test that fails for the right reason.
  Done means that test passes, not that the code is written. Run:

```sh
uv run --directory claudemd-lerner python -m unittest discover -s _shared/tests -t .
uv run --directory knowledge-base python -m unittest discover -s _shared/tests -t .
uv run --directory compliance-base python -m unittest discover -s _shared/tests -t .
uv run --directory stack-base python -m unittest discover -s _shared/tests -t .
```
<!-- neurawork-cc-harness:rules END -->
