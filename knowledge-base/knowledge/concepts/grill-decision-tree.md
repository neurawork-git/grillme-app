---
title: "Grill Decision Tree and Session Closure"
aliases: [decision-tree, frontier, session-completion]
tags: [product, agent, decision, spec]
sources:
  - ".claude/spec.md"
created: 2026-08-20
updated: 2026-08-20
---

# Grill Decision Tree and Session Closure

The interview is driven by a decision tree stored as JSON in Postgres. Nodes are
decisions carrying a status (open / decided), a question, a recommendation, and
an answer. The *frontier* — every decision whose prerequisites are settled — is
recomputed each round. A session ends when the agent reports an empty frontier
and the user explicitly confirms.

## Key Points

- Without a persistent tree the agent loses track of what is still open in long
  sessions and asks in circles — exactly the failure mode the application exists
  to avoid.
- Closure is a deliberate two-step: the agent *reports*, the user *confirms*. A
  language model left to decide alone stops too early.
- The confirmation click triggers artefact generation and is the event that
  counts for gamification.
- Unconfirmed sessions stay open and resumable.
- The tree is persisted as the `decision_node` table (question, recommendation,
  answer, status, parent node).

## Details

The tree is doing two jobs at once. As agent input it is the memory that the
discarded SDK session no longer provides — see
[[concepts/agent-state-in-postgres]]. As product data it is the deterministic
input from which the final artefact is generated in the chosen output format.
Because both jobs read the same JSON, the document the user exports and the
state the agent reasons over cannot drift apart.

The frontier concept keeps the interview ordered without hard-coding a
questionnaire: the agent is not told "ask question 7 next", it is given the set
of decisions whose prerequisites are resolved and picks from there. This is what
makes the tree recomputable rather than a fixed script.

Making completion an explicit user action also makes the gamification
trustworthy. Because only a confirmed, artefact-producing session counts, the
counter cannot be inflated by creating sessions.

## Related Concepts

- [[concepts/agent-state-in-postgres]] — the tree is what makes stateless rounds
  possible
- [[concepts/grillme-v1-scope]] — closure produces the chosen output format
- [[connections/agent-state-and-decision-tree]] — the pairing spelled out

## Sources

- `.claude/spec.md` — §4.2 decision tree, §4.3 session closure, §7 gamification,
  §9 `decision_node` table
