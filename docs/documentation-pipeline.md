# The Documentation Pipeline

How a Claude Code session in this repository becomes durable documentation. This
is the design deep-dive; the operational summary lives in the root
[CLAUDE.md](../CLAUDE.md), and hook-level troubleshooting in
[hooks-runbook.md](hooks-runbook.md).

## The Compiler Analogy

Both engines are built on the same mental model, stated at the top of each
`AGENTS.md`:

```
daily/        source code   — raw session logs, append-only, never rewritten
LLM           compiler      — reads logs + the live repo, emits/edits output
knowledge/    executable    — the structured, queryable knowledge base
CLAUDE.md     executable    — the conventions the agent reads first
docs/         executable    — longer-form guides and design docs
lint          test suite    — structural + semantic health checks
query         runtime       — answering questions from the base
```

The consequence that matters: **documentation is never organised by hand.**
Sessions produce logs, the LLM does the synthesis, and the outputs are
regenerated (surgically edited, never rewritten) from those logs plus the live
repository. Hand-editing an output file is allowed — the learner is instructed to
preserve hand-written content — but hand-*organising* the tree defeats the design.

## Stage 1 — Capture (no API calls)

`SessionEnd` and `PreCompact` fire the same short program, once per engine:

1. `recursion_guard()` — exit 0 immediately if `CLAUDE_INVOKED_BY` is set.
2. `read_hook_input()` — parse the JSON payload from stdin. Windows can send
   unescaped backslashes in paths, so a failed `json.loads` is retried once with
   backslashes doubled; any remaining failure yields `{}` rather than an
   exception.
3. Bail out unless `transcript_path` is a non-empty string pointing at an
   existing file. `PreCompact` in particular is documented to sometimes pass an
   empty `transcript_path`.
4. `extract_turns()` — stream the JSONL transcript, keep only `user`/`assistant`
   text (flattening list-shaped `content` into its `text` blocks), take the last
   30 turns, and truncate to 15,000 characters *from the end*, snapping forward
   to the next `\n**` so the context never starts mid-turn.
5. Bail out if the result is empty or has fewer than `MIN_TURNS_TO_FLUSH` turns
   — 1 for SessionEnd, 5 for PreCompact.
6. Write the turns to `<engine>/scripts/<prefix><session_id>-<stamp>.md`
   (`session-flush-` for SessionEnd, `flush-context-` for PreCompact) and
   `Popen` `flush.py` against it with `stdout`/`stderr` sent to `DEVNULL`.

The whole stage is local and fast — the hook's configured timeout is 10 seconds,
and no network call happens inside it.

## Stage 2 — Distil (`flush.py`)

`flush.py` sets `CLAUDE_INVOKED_BY=neurawork_cc_harness` **at module top level,
before importing anything SDK-related**, then makes a single text-only SDK call
(`allowed_tools=[]`, `max_turns=2`) asking for a concise daily-log entry.

The learner's prompt asks for these sections, omitting any that would be empty:
`**Context:**`, `**Conventions / Architecture:**`, `**Decisions Made:**`,
`**Commands:**`, `**Lessons Learned:**`. The compiler's variant asks for
`**Key Exchanges:**` and `**Action Items:**` instead of commands. Both explicitly
instruct the model to skip routine tool calls, file reads, and trivial
back-and-forth.

Three outcomes:

| Response | Effect |
|---|---|
| Contains `FLUSH_OK`, or is blank | Nothing appended; logged as `Result: FLUSH_OK` |
| Contains `FLUSH_ERROR` | Appended to the daily log under a `Memory Flush` heading, and logged at ERROR |
| Anything else | Appended under a `Session` heading with an `HH:MM` timestamp |

Appending goes through `assert_in_repo_not_dotclaude()` first; a guard violation
is logged and the write is dropped, never raised. The daily log is created with a
`# Daily Log: YYYY-MM-DD` / `## Sessions` header on first write. The input
context file is `unlink`ed on every exit path.

A 60-second dedup window keyed on `session_id` (`scripts/last-flush.json`)
prevents a double entry when SessionEnd and PreCompact fire back to back.

Because the hooks discard stdout and stderr, `scripts/flush.log` is the only
record of what stage 2 did.

## Stage 3 — Synthesise

### The learner: `update.py`

Builds one prompt per daily log containing the full `AGENTS.md` schema, the
resolved configuration, the list of existing in-depth `CLAUDE.md` files, the list
of existing `docs/` files, and the log itself. The task text instructs the model
to ground every change in the live repository via `Read`/`Glob`/`Grep`, to prefer
`Edit` over rewrite, to route durable repo-wide facts to the root `CLAUDE.md`,
area-specific facts to an in-depth area file, and long explanations to `docs/` —
and to make **no edits at all** if nothing in the log warrants a doc change.

The SDK runs with `permission_mode="acceptEdits"`, `max_turns=30`,
`setting_sources=[]`, and `strict_mcp_config=True` — a deliberately hermetic
environment: the run does not inherit the repo's own Claude Code settings or MCP
servers.

### The compiler: `compile.py`

Same shape, but the prompt carries the current `index.md` plus the **full text of
every existing article**, and the task is to extract 3–7 concepts, prefer
updating over creating, then update `index.md` and append to `log.md`.

### Incrementality

Both track `{log_name: {hash, timestamp, cost_usd}}` in `scripts/state.json`,
where `hash` is the first 16 hex chars of the log's SHA-256. A log is reprocessed
when its hash is absent or differs. `--all` bypasses the check; `--dry-run` lists
what would be processed and exits.

State is saved **after each log**, so an interrupted multi-log run keeps the work
it already paid for. A failed run returns cost `0.0` and records nothing, leaving
the log marked changed for the next attempt.

## Stage 0 — Seeding

Run once at install time, in the foreground. Both `seed.py` scripts:

1. Refuse to run outside a git repository.
2. Refuse to run when `git status --porcelain` shows changes outside their own
   engine directory — a seed must never write over uncommitted work. Changes
   *inside* the engine dir are fine, since installing it is what made them.
3. Re-assert the write guard on their output targets.
4. Assemble repo context — README (first 8,000 chars), existing `CLAUDE.md`
   files, the `docs/` listing (capped at 50 entries), and the non-hidden,
   non-excluded top-level entries — and hand it to the SDK with `max_turns=40`.
5. Stamp `last-update.json` / `last-compile.json` so the SessionStart gate does
   not immediately fire a background run.

The seed prompts are the strictest in the system: *write only the allowed
targets, never under `.claude/`, update an existing root `CLAUDE.md` surgically,
and use only facts grounded in files actually read.*

## Cost and Model Selection

Every SDK call reads `cfg["model"]` and passes `cfg.get("model") or None`, so the
empty-string default defers to the SDK. Costs come from
`ResultMessage.total_cost_usd` and accumulate in `state["total_cost"]`;
`update.py` and `compile.py` print a per-log cost and a run total, `flush.py`
logs its cost to `flush.log`, and `query.py` folds its cost into the same state
counter alongside `query_count`.

## Why No RAG

At repo scale — tens to a few hundred articles — an LLM reasoning over a curated
`index.md` beats vector similarity: embeddings match similar *words*, the LLM
matches relevant *meaning*. Index-guided retrieval is the design, and `query.py`
implements it directly: read the index, pick 3–10 articles, read them in full,
answer with `[[wikilink]]` citations, and say so plainly when the base does not
have the answer.

The stated limit: past roughly 2,000 articles / ~2M tokens the index stops
fitting in context, and a keyword + semantic search layer should be added. Until
then — no embeddings, no chunking, no vector store.

In practice `compile.py` hits this ceiling before `query.py` does, because it
inlines every existing article into its prompt rather than just the index.
