---
title: "Connection: Stateless SDK Sessions and the Decision Tree"
connects:
  - "concepts/agent-state-in-postgres"
  - "concepts/grill-decision-tree"
sources:
  - ".claude/spec.md"
created: 2026-08-20
updated: 2026-08-20
---

# Connection: Stateless SDK Sessions and the Decision Tree

## The Connection

Two decisions in the GrillMe spec are usually read separately — "don't use the
Claude Agent SDK's own session persistence" (§3.1) and "keep the interview state
as a JSON decision tree in Postgres" (§4.2). They are the same decision seen from
two sides. Throwing away the SDK session is only survivable because the tree
already carries everything a fresh session needs, and the tree is only worth
maintaining because the agent is re-prompted from it every round.

## Key Insight

The tree is not a cache of the conversation — it is the *replacement* for
conversational memory, and it is simultaneously the deterministic input for the
final artefact. That triple duty is what makes discarding session state cheap:
there is no second representation to keep in sync, so the state the agent reasons
over and the document the user exports cannot drift apart. A design that kept
SDK sessions *and* a tree would have to reconcile them.

The same insight explains a detail that looks unrelated: screenshots are re-sent
on every follow-up call (§5.3). With no session continuity, "the agent must not
have forgotten the screenshot by round eight" is not a memory-quality wish but a
structural requirement — anything not in this round's prompt does not exist.

## Evidence

- §3.1 states that Postgres is the only source of truth, that each round starts a
  fresh SDK session, and that `resume=<session_id>` is therefore unused and
  `.claude/` needs no persistent volume.
- §3.1 also names the tree as "what the final artefact is generated from
  deterministically anyway", making it pre-existing rather than extra cost, and
  points at prompt caching to absorb the repeated input tokens.
- §4.2 gives the failure mode the tree prevents: without it the agent loses track
  of what is still open in long sessions and asks in circles.
- §5.3 keeps images permanently in the history and re-sends them each call.

## Related Concepts

- [[concepts/agent-state-in-postgres]]
- [[concepts/grill-decision-tree]]
