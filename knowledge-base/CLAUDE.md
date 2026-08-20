# CLAUDE.md — knowledge-base

Per-repo, self-building knowledge base compiled from Claude Code sessions.
Package name: `neurawork-knowledge`. See the root [CLAUDE.md](../CLAUDE.md) for
the repo-wide picture and [AGENTS.md](AGENTS.md) for the article schema the
compiler LLM must follow.

Unlike `claudemd-lerner`, this engine writes **entirely inside its own
directory** — everything it produces lands under `knowledge-base/knowledge/`.
`scripts/config.py` therefore has no `REPO_ROOT` split: `ROOT_DIR` (overridable
via the `KNOWLEDGE_ROOT` env var) is both the machinery root and the output root.

## Commands

```bash
uv run --directory knowledge-base python scripts/seed.py           # first install
uv run --directory knowledge-base python scripts/compile.py        # changed logs
uv run --directory knowledge-base python scripts/compile.py --all
uv run --directory knowledge-base python scripts/compile.py --file daily/2026-06-18.md
uv run --directory knowledge-base python scripts/compile.py --dry-run
uv run --directory knowledge-base python scripts/query.py "your question"
uv run --directory knowledge-base python scripts/query.py "your question" --file-back
uv run --directory knowledge-base python scripts/lint.py
uv run --directory knowledge-base python scripts/lint.py --structural-only
uv run --directory knowledge-base python -m unittest discover -s _shared/tests -t .
```

`scripts/flush.py` takes positional args and is normally hook-spawned:

```bash
uv run --directory knowledge-base python scripts/flush.py <context_file.md> <session_id>
```

## Configuration (`config.json`)

| Key | Current value | Default | Meaning |
|---|---|---|---|
| `knowledge_dir` | `knowledge-base` | `knowledge-base` | This engine's directory name |
| `model` | `""` | `""` | Empty means "let the SDK choose" (passed as `None`) |
| `compile_age_hours` | `6` | `6` | Age gate before `SessionStart` spawns a compile |

## Layout

```
knowledge-base/
├── AGENTS.md              constitution — article formats, compile/query/lint rules
├── VERSION                "1"
├── config.json
├── pyproject.toml         deps: claude-agent-sdk, python-dotenv, tzdata
├── hooks/
│   ├── session-start.py   inject knowledge/index.md; maybe spawn a compile
│   ├── session-end.py     capture transcript -> spawn flush.py
│   └── pre-compact.py     same, before auto-compaction
├── scripts/
│   ├── seed.py            build the first articles from the repo itself
│   ├── compile.py         daily logs -> concept/connection articles
│   ├── query.py           index-guided Q&A, optional --file-back
│   ├── lint.py            7 health checks -> reports/lint-<date>.md
│   ├── flush.py           distil one session into daily/<date>.md
│   ├── config.py          paths + config
│   ├── utils.py           state, hashing, wikilink/index helpers, should_compile()
│   └── seed_prompt.txt    seed instructions prepended to AGENTS.md
├── knowledge/
│   └── index.md           master catalog (currently header-only — nothing compiled yet)
└── _shared/               stdlib helpers + unittest suite (see root CLAUDE.md)
```

`knowledge/` is **tracked**. Runtime artifacts, all gitignored and created on
demand: `daily/`, `reports/`, `knowledge/log.md`, `scripts/state.json`,
`scripts/last-compile.json`, `scripts/last-flush.json`,
`scripts/kc-compile.lock`, `scripts/flush.log`, and the transient
`scripts/session-flush-*.md` / `scripts/flush-context-*.md` context files.

Note the asymmetry: `knowledge/index.md` is versioned but `knowledge/log.md` is
not, even though `AGENTS.md` treats both as knowledge-base files. The build log
is local noise; the index is the retrieval mechanism and must be shared.

## Current State

The base is **empty** — `knowledge/index.md` contains only its table header, and
`concepts/`, `connections/`, `qa/` do not exist yet. `compile.py` and `seed.py`
create them as needed. Do not hand-author articles: run `seed.py` once, then let
`compile.py` maintain the base.

## Local Conventions

- **Hook filenames are unprefixed** (`session-start.py`, `session-end.py`,
  `pre-compact.py`); the learner's equivalents carry a `cl-` prefix.
- **The lock file is `kc-compile.lock`** (the learner's is `cl-update.lock`) so
  the two engines never contend.
- **Wikilinks are repo-relative from `knowledge/`, without `.md`**:
  `[[concepts/slug]]`, `[[connections/slug]]`. Daily-log references are the one
  exception — they keep the extension (`[[daily/2026-06-18.md]]`) because a log
  is a source, not an article. `lint.py` special-cases the `daily/` prefix in
  both `check_broken_links` and `check_missing_backlinks`.
- **Frontmatter minimum**: `title`, `sources`, `created`, `updated`. Every
  article cites its daily log(s) in `sources:` *and* in a `## Sources` section,
  and links to at least two other articles.
- **3–7 concepts per log, no more.** Quality over volume; prefer updating an
  existing article and appending to its `sources:` over creating a
  near-duplicate.
- **Connection articles are rare by design** — only for genuinely non-obvious
  links between concepts that already have articles.
- **`scripts/` is on `sys.path`, not a package** — flat imports
  (`from config import ...`, `from utils import ...`); `seed.py` and `flush.py`
  insert the engine dir for `_shared`, hooks insert both the engine dir and
  `scripts/`.

## Lint Checks

Six structural checks (free, instant) plus one LLM check. Severities drive the
exit code: **any `error` makes `lint.py` exit 1**.

| Check | Severity | Trigger |
|---|---|---|
| `broken_link` | error | `[[link]]` whose target article is missing |
| `contradiction` | warning (error if the LLM call itself fails) | Conflicting claims across articles |
| `orphan_page` | warning | No inbound links to the article |
| `orphan_source` | warning | A daily log that was never compiled |
| `stale_article` | warning | A daily log's hash changed since it was compiled |
| `missing_backlink` | suggestion (auto-fixable) | A→B exists but B→A does not |
| `sparse_article` | suggestion | Fewer than 200 words |

`--structural-only` skips the contradiction check — use it when you want a fast,
zero-cost pass.

## Gotchas

- **`compile.py` is spawned with `--all`.** `session-start.py` runs
  `scripts/compile.py --all`, so a background run recompiles every daily log.
- **`compile.py` and `query.py` do not import `_shared`** and rely on `uv run
  --directory` for their working directory; only `seed.py` and `flush.py` insert
  the engine dir on `sys.path` explicitly.
- **`compile.py` inlines every existing article into the prompt.** Prompt size
  grows with the base — the same scaling limit `AGENTS.md` cites for the index
  (~2,000 articles / ~2M tokens) applies here first.
- **`--file` resolution is forgiving**: a bare name is looked up in `daily/`,
  then relative to `ROOT_DIR`; a miss exits 1 with `Error: <file> not found`.
- **`query.py` returns errors as its answer string.** An SDK failure yields
  `"Error querying knowledge base: …"` printed as if it were the answer, not a
  non-zero exit. Check the text, not the exit code.
- **`--file-back` widens the tool set.** Without it `query.py` is read-only
  (`Read`, `Glob`, `Grep`); with it, `Write` and `Edit` are added and the LLM is
  told to file a `knowledge/qa/` article, add an index row, and append to
  `knowledge/log.md`.
- **The seed writes only under `knowledge/`** and aborts if `git status
  --porcelain` shows changes outside this directory.
- **`should_compile()` in `utils.py` is pure** (no SDK, no I/O) so the hook and
  the tests can both call it cheaply. A missing `last-compile.json` counts as
  infinitely old.
