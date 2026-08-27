---
title: "GrillMe v1 Scope"
aliases: [grillme-product-scope, v1-umfang]
tags: [product, spec, scope]
sources:
  - ".claude/spec.md"
created: 2026-08-20
updated: 2026-08-20
---

# GrillMe v1 Scope

GrillMe turns a structured requirements interview — question, recommendation,
answer, next round — into a web application with accounts, history, and several
input channels. The interview exists today only as an agent skill on the command
line. In v1 a user logs in, creates a session, picks an output format, gets
grilled, and confirms completion, which produces the artefact.

## Key Points

- Screens in v1: login, session list, chat, export. The gamification status is a
  small header indicator with no page of its own.
- Operation in v1: `docker compose up` on the user's own machine, one user; the
  architecture is built so hosted multi-user operation can follow without
  touching the data model or storage.
- Output formats live as `prompt_template` rows in Postgres; each entry pairs an
  output template with an interview focus. Starter set: `Spec (Markdown)`,
  `User Stories`, `Tickets`, `PRD`. The format is chosen when the session is
  created.
- System prompt-library entries are copyable but not overwritable, so a user's
  own variant cannot destroy the original. v1 ships them as seed data; a
  management UI is deferred.
- Gamification counts a **completed** session — confirmed closure with a
  generated artefact — never the mere creation of one, so points cannot be
  farmed by clicking.

## Details

The problem statement in the spec is that an idea arrives as a spark, not as a
requirements list; whoever writes it down immediately writes down the obvious
and misses the decisions hanging off it. A structured interview forces
consideration of exactly those branches. GrillMe's contribution over the
command-line skill is that it must also *produce an artefact* in the chosen
format at the end — a Markdown document and, depending on the format, one or
more tickets.

The interview itself is vendored: the `grilling` skill from `mattpocock-skills`
(MIT, verified in `.claude-plugin/plugin.json`) is copied into the repository
including its copyright notice and then developed into a GrillMe-specific
variant.

Gamification uses two axes with thresholds and names in a seed table, adjustable
without a code change: completed sessions at 1 / 5 / 10 / 25 / 50 (`Anzünder`,
`Kohlenflüsterer`, `Grillmeister`, …) and answered questions at 50 / 250 / 1000.
Sticker assets are fixed rather than generated, to avoid a third vendor, a
per-user cost, and unpredictable quality for pure decoration.

Explicitly deferred to phase 2: full-duplex voice with interruption, ticket
creation directly as GitHub issues (v1 exports Markdown files), a management UI
for the prompt library, replacing old images with textual descriptions to save
tokens, and multi-user operation and hosting.

## Related Concepts

- [[concepts/grillme-app-repository]] — where this specification lives
- [[concepts/grillme-architecture]] — the components that implement this scope
- [[concepts/grill-decision-tree]] — what drives the interview and its closure
- [[concepts/input-channels]] — text, voice, and screenshots
- [[concepts/claude-credentials-and-tenancy]] — the switch that gates multi-user
  operation

## Sources

- `.claude/spec.md` — §1 problem, §2 product scope, §4.1 skill provenance,
  §6 prompt library, §7 gamification, §10 phase-2 list
