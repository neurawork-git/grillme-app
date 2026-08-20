# CLAUDE.md — claudemd-lerner

Per-repo learner that keeps the repository's **CLAUDE.md hierarchy and `docs/`
tree** current from Claude Code sessions. Package name:
`neurawork-claudemd-lerner`. See the root [CLAUDE.md](../CLAUDE.md) for the
repo-wide picture.

## The Critical Path Split

`scripts/config.py` draws the line this whole engine depends on:

- `ROOT_DIR` (`<repo>/claudemd-lerner`) holds **only machinery** — hooks,
  scripts, `_shared/`, `daily/`.
- `REPO_ROOT` (`ROOT_DIR.parent`) is where the **outputs** live —
  `<repo>/CLAUDE.md` and `<repo>/docs/`.

`ROOT_DIR` defaults to this directory but is overridden by the `LERNER_ROOT`
environment variable, which the capture hooks set when redirecting output out of
a git worktree into the main checkout. Never hardcode either path; import
`ROOT_DIR`, `REPO_ROOT`, `CLAUDEMD_FILE`, and `docs_dir()` from `config.py`.

## Commands

```bash
uv run --directory claudemd-lerner python scripts/seed.py       # first install
uv run --directory claudemd-lerner python scripts/update.py     # changed logs
uv run --directory claudemd-lerner python scripts/update.py --all
uv run --directory claudemd-lerner python scripts/update.py --dry-run
uv run --directory claudemd-lerner python -m unittest discover -s _shared/tests -t .
```

`scripts/flush.py` takes positional args and is normally hook-spawned:

```bash
uv run --directory claudemd-lerner python scripts/flush.py <context_file.md> <session_id>
```

## Configuration (`config.json`)

Merged over `DEFAULT_CFG` in `scripts/config.py`; `load_cfg()` never raises, so a
malformed file silently falls back to the defaults.

| Key | Current value | Default | Meaning |
|---|---|---|---|
| `lerner_dir` | `claudemd-lerner` | `claudemd-lerner` | This engine's directory name |
| `model` | `""` | `""` | Empty means "let the SDK choose" (passed as `None`) |
| `update_age_hours` | `6` | `6` | Age gate before `SessionStart` spawns an update |
| `claudemd_depth` | `2` | `1` | `1` = root CLAUDE.md only; `2` = root + immediate subdirs |
| `docs_dir` | `docs` | `docs` | Long-form docs dir, relative to `REPO_ROOT` |
| `language` | `en` | `en` | Language for all generated prose |
| `excluded_dirs` | `node_modules`, `.venv`, `dist`, `build`, `.git` | same | Never read, never written |

**`claudemd_depth` is enforced in code**, not just in the prompt:
`update.py::_list_claudemd_files` keeps a `CLAUDE.md` only when
`len(rel.parts) - 1 <= max(depth - 1, 0)`, and additionally skips any path whose
parent parts are excluded or start with a dot.

## Layout

```
claudemd-lerner/
├── AGENTS.md              constitution — read in full before seeding or updating
├── VERSION                "1"
├── config.json
├── pyproject.toml         deps: claude-agent-sdk, python-dotenv, tzdata
├── hooks/
│   ├── cl-session-start.py   inject CLAUDE.md + docs listing; maybe spawn update
│   ├── cl-session-end.py     capture transcript -> spawn flush.py
│   └── cl-pre-compact.py     same, before auto-compaction
├── scripts/
│   ├── seed.py            build/refresh the whole doc tree from the repo
│   ├── update.py          apply daily logs to CLAUDE.md + docs/
│   ├── flush.py           distil one session into daily/<date>.md
│   ├── config.py          paths + config (the ROOT_DIR / REPO_ROOT split)
│   ├── utils.py           state, hashing, log listing, should_update()
│   └── seed_prompt.txt    seed instructions prepended to AGENTS.md
└── _shared/               stdlib helpers + unittest suite (see root CLAUDE.md)
```

Runtime artifacts, all gitignored and created on demand: `daily/`,
`scripts/state.json`, `scripts/last-update.json`, `scripts/last-flush.json`,
`scripts/cl-update.lock`, `scripts/flush.log`, and the transient
`scripts/session-flush-*.md` / `scripts/flush-context-*.md` context files.

## Local Conventions

- **Hook filenames are prefixed `cl-`.** The knowledge-base engine uses the
  unprefixed names (`session-start.py`, …); the prefix keeps the two
  distinguishable in `.claude/settings.json` and in `ps` output.
- **The lock file is `cl-update.lock`** (the compiler's is `kc-compile.lock`) so
  the two engines never contend.
- **`scripts/` is on `sys.path`, not a package.** Scripts import each other
  flat (`from config import ...`, `from utils import ...`). Entrypoints that
  also need `_shared` insert the engine dir themselves:
  `sys.path.insert(0, str(Path(__file__).resolve().parent.parent))`. Hooks
  insert both the engine dir and `scripts/`.
- **`flush.py` sets `CLAUDE_INVOKED_BY` before importing the SDK**, at module
  top level, with a comment saying why. Keep that ordering — setting it later
  would leave a window where a nested session runs the hooks.
- **`flush.py` is text-only**: `allowed_tools=[]`, `max_turns=2`. It returns the
  literal `FLUSH_OK` when nothing is worth saving, and `FLUSH_ERROR: ...` on an
  SDK failure — the error case *is* appended to the daily log (under a "Memory
  Flush" section) so failures stay visible.
- **`flush.py` logs to `scripts/flush.log`**, never to stdout: the hooks spawn it
  with `stdout=DEVNULL, stderr=DEVNULL`, so `logging` is the only way to see what
  happened.
- **60-second flush dedup.** `scripts/last-flush.json` suppresses a second flush
  for the same `session_id` within `DEDUP_WINDOW_SECONDS`, because SessionEnd and
  PreCompact can fire back to back.
- **Different turn thresholds by hook**: `cl-session-end.py` flushes from
  `MIN_TURNS_TO_FLUSH = 1`, `cl-pre-compact.py` from `5` — a compaction only
  matters if the session was already substantial.
- **Context files are consumed**: `flush.py` `unlink`s its input on every exit
  path, including the skip paths.

## Gotchas

- **`update.py` is spawned with `--all`, not bare.** `cl-session-start.py` runs
  `scripts/update.py --all`, so a background run re-applies every daily log
  rather than only the changed ones.
- **`update.py` does not add `_shared` to `sys.path`** the way `seed.py` and
  `flush.py` do — it relies on being launched via `uv run --directory` from the
  engine root. Invoking it from elsewhere can break `from _shared.repo_guard
  import ...`.
- **The SDK call swallows its own text.** `update_one()` iterates
  `AssistantMessage` blocks and deliberately does nothing with them (`pass  # the
  LLM edits files directly`); only the cost is printed. To debug a run, look at
  the resulting file diffs, not at stdout.
- **A failed `update_one()` returns `0.0` and does not record state**, so the log
  stays "changed" and will be retried on the next run.
- **`seed.py` and `update.py` both re-assert the write guard** on `CLAUDE.md` and
  `docs_dir()` before doing anything, and print `Refusing to …` instead of
  raising. Keep that pattern for any new entrypoint that writes docs.
- **`should_update()` in `utils.py` is pure** (no SDK, no I/O) precisely so the
  hook and the tests can both call it cheaply. A missing `last-update.json`
  counts as infinitely old.
