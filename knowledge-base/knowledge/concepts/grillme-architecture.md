---
title: "GrillMe Architecture"
aliases: [grillme-stack, ag-ui-architecture]
tags: [architecture, stack, spec]
sources:
  - ".claude/spec.md"
created: 2026-08-20
updated: 2026-08-20
---

# GrillMe Architecture

The specified stack is a Next.js + React frontend using CopilotKit as an AG-UI
client, talking over SSE (the AG-UI protocol) to a FastAPI backend that drives
the Claude Agent SDK. Postgres is the single source of truth for state, history,
and the decision tree; MinIO stores images; speech-to-text and text-to-speech sit
behind `Transcriber` and `Speaker` interfaces. All components run as services in
one Docker Compose stack.

## Key Points

- Chain from the backend to the model: `claude-agent-sdk` → Claude Code CLI as a
  subprocess → Claude API.
- Transport is AG-UI via `ag-ui-claude-agent-sdk`, the official AG-UI
  integration for the Python Claude Agent SDK; the frontend speaks the same
  protocol through CopilotKit.
- The AG-UI package version is **pinned to 0.1.0** because it is early; the
  adapter is small enough to vendor and maintain in-house if necessary.
- Authentication is email + password (Argon2) in Postgres with a session cookie.
  There is no public signup — users are created by a CLI command.
- Every user-scoped table carries a `user_id` from day one, even while only one
  user exists.

## Details

The backend wiring named in the spec is minimal: construct a
`ClaudeAgentAdapter(name="grill_agent", options={"model": "claude-opus-5"})` and
register it with `add_claude_fastapi_endpoint(app=app, adapter=adapter,
path="/grill")`. What that integration brings — streaming of tool arguments,
`adapter.interrupt()`, frontend tools with a human-in-the-loop stop,
bidirectional state sync, and context injection — is precisely the set of
building blocks a hand-rolled SSE layer would spend weeks reproducing.

The login decision was made against two alternatives: OIDC against an external
provider was judged overkill for a local stack, and having no login at all would
mean retrofitting authentication later including a data migration.

The sketched data model has nine tables: `user` (Argon2 hash, optional encrypted
`anthropic_api_key`), `session` (owner, format reference, status, completion
timestamp), `message` (role, text, mode, image references), `decision_node`,
`image` (MinIO object key), `prompt_template`, `artifact`, `achievement`, and
`token_usage` for per-session cost control.

Privacy requirements are built into the architecture from the start rather than
retrofitted: account deletion cascades across all data explicitly including the
MinIO objects, session export as JSON, deletion of audio after transcription,
and a processing register maintained as a document in the repository. The
rationale given is that deletion and export touch every schema and storage path,
so they are cheap as a starting constraint and expensive later.

## Related Concepts

- [[concepts/grillme-v1-scope]] — the product these components serve
- [[concepts/agent-state-in-postgres]] — why the SDK's own session store is
  bypassed
- [[concepts/input-channels]] — the Transcriber/Speaker interfaces and MinIO
- [[concepts/claude-credentials-and-tenancy]] — how the backend authenticates to
  Claude
- [[concepts/grillme-app-repository]] — the repository this stack is specified in

## Sources

- `.claude/spec.md` — §3 architecture diagram, §3.2 AG-UI transport, §3.4 login,
  §8 privacy, §9 data model sketch
