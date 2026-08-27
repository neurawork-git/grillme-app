---
title: "Agent State Lives in Postgres"
aliases: [no-sdk-session-persistence, stateless-sdk-session]
tags: [architecture, decision, state, spec]
sources:
  - ".claude/spec.md"
created: 2026-08-20
updated: 2026-08-20
---

# Agent State Lives in Postgres

The Claude Agent SDK ships its own sessions whose state lives in the CLI's
filesystem. GrillMe deliberately does **not** use that persistence. Postgres is
the only source of truth: every interview round starts a fresh SDK session and is
handed the decision tree plus the history again as prompt input.

## Key Points

- `resume=<session_id>` is not used, and `.claude/` needs no persistent volume.
- The SDK session is treated as a disposable computation step, not as memory.
- The decision tree as JSON in Postgres is in any case what the final artefact is
  generated from, deterministically.
- The extra input tokens per round are absorbed by prompt caching.

## Details

The rationale recorded in the spec is that three things all break on
file-based session state: container restarts, resuming a session after days, and
later multi-user operation. Any one of them would force the state out of the
filesystem eventually, so the design does it from the start.

The trade the decision accepts is explicit. Re-sending the tree and the history
on every round costs input tokens that a resumed session would not; the spec
answers that with prompt caching rather than pretending the cost is zero. What
is gained is that the durable representation — the tree — is the same artefact
the output document is generated from, so there is no second, hidden state to
keep in sync with it.

This is also why images are re-sent on every follow-up call rather than being
"remembered" by the session: with no session continuity, everything the agent
needs must be in the prompt that round.

## Related Concepts

- [[concepts/grill-decision-tree]] — the state that replaces the SDK session
- [[concepts/grillme-architecture]] — where Postgres sits in the stack
- [[connections/agent-state-and-decision-tree]] — why the two decisions only
  work as a pair

## Sources

- `.claude/spec.md` — §3.1 "Agent-State lebt in Postgres", §5.3 image handling
