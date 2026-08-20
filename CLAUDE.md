# CLAUDE.md — grillme-app

## Project Purpose

`grillme-app` is a git repository that currently contains **no application
source**. Its `README.md` holds only the project title. What is checked in today
is the NeuraWork Claude Code documentation harness: two self-contained,
per-repo engines that turn Claude Code session transcripts into durable project
documentation.

- **`claudemd-lerner/`** — the *learner*. Keeps this CLAUDE.md hierarchy and the
  `docs/` tree current from session logs.
- **`knowledge-base/`** — the *knowledge compiler*. Builds and maintains a
  structured, queryable wiki under `knowledge-base/knowledge/`.

Both are installed as subdirectories of the repo they serve, and both write
their outputs **inside this repository, never under `.claude/`**.

## Commands

Both engines are `uv`-managed Python packages (`requires-python >= 3.12`). Every
command below is run from the repository root.

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

### Test

The `_shared/` tests are stdlib `unittest`, no test runner is declared as a
dependency:

```bash
uv run --directory claudemd-lerner python -m unittest discover -s _shared/tests -t .
uv run --directory knowledge-base  python -m unittest discover -s _shared/tests -t .
```

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
├── .claude/settings.json      ← hook registration (NEVER written by the engines)
├── claudemd-lerner/           ← learner engine (see its CLAUDE.md)
└── knowledge-base/            ← knowledge compiler (see its CLAUDE.md)
```

Both engines share the same three-stage shape:

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

### Major components

| Path | Role |
|---|---|
| `claudemd-lerner/AGENTS.md` | Constitution the learner LLM follows (where things go, update/seed rules) |
| `claudemd-lerner/config.json` | `claudemd_depth`, `docs_dir`, `language`, `excluded_dirs`, `update_age_hours`, `model` |
| `claudemd-lerner/hooks/cl-*.py` | SessionStart / SessionEnd / PreCompact entrypoints |
| `claudemd-lerner/scripts/` | `seed.py`, `update.py`, `flush.py`, `config.py`, `utils.py` |
| `knowledge-base/AGENTS.md` | Constitution the compiler LLM follows (article formats, compile/query/lint rules) |
| `knowledge-base/config.json` | `knowledge_dir`, `compile_age_hours`, `model` |
| `knowledge-base/hooks/*.py` | SessionStart / SessionEnd / PreCompact entrypoints |
| `knowledge-base/scripts/` | `seed.py`, `compile.py`, `query.py`, `lint.py`, `flush.py`, `config.py`, `utils.py` |
| `knowledge-base/knowledge/index.md` | Master catalog — read first by both the compiler and the query engine |
| `<engine>/_shared/` | Stdlib-only helpers, vendored identically into both engines |

### `_shared/` helpers (identical in both engines)

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

**`_shared/` is vendored, not shared at runtime.** Both engines carry a
byte-identical copy. This keeps each engine a self-contained, independently
installable unit at the cost of duplicating the helpers — **a fix to one copy
must be applied to both.**

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

**Recursion guard.** Any Claude Code the SDK spawns is marked with
`CLAUDE_INVOKED_BY=neurawork_cc_harness`; hooks see it and exit immediately, so
a background compile cannot re-trigger the hooks that started it.

**Seeds refuse to run on a dirty tree.** Both `seed.py` scripts abort if
`git status --porcelain` shows changes outside their own engine directory, so a
seed never writes over uncommitted work.

**Lineage.** The knowledge compiler is a repo-local implementation of the
LLM-as-compiler idea (Andrej Karpathy's LLM wiki, rebuilt openly by coleam00's
claude-memory-compiler); the learner adds the doc-maintenance pattern from
NeuraWork's own coding-suite learner. The designs are independent NeuraWork
work; only the underlying concept is shared.
