---
title: "Connection: Free Tiers and the Single-Tenant Boundary"
connects:
  - "concepts/claude-credentials-and-tenancy"
  - "concepts/input-channels"
sources:
  - ".claude/spec.md"
created: 2026-08-20
updated: 2026-08-20
---

# Connection: Free Tiers and the Single-Tenant Boundary

## The Connection

The credentials decision (§3.3) and the speech-provider selection (§5.4, §8) look
like separate procurement questions — one about Claude, one about transcription
and speech synthesis. The spec explicitly ties them together: free and
subscription tiers typically come without a data-processing agreement and permit
the provider to use submitted data for training, so **the same switch** governs
both. The spec's words: it is the same cut as the Claude credentials, and both
switches are thrown together.

## Key Insight

The line is not "paid vs. free" but "is there a third-party data subject". While
only the operator uses the instance there is no affected third party, so a
subscription token or a free STT tier is purely a terms-of-use question. The
moment a second person feeds data in, every one of those tiers becomes a
data-protection question at once — Claude, transcription, and speech output
together.

That is why the coupling is specified as an enforcement rule rather than a note:
multi-user operation is bound to the API-key implementation and **must not be
startable** with a subscription token. A boundary that flips several vendor
relationships simultaneously cannot be left to operator discipline. It also
explains why the encrypted `user.anthropic_api_key` column exists in the schema
before any second user does — the migration must not be what triggers the switch.

## Evidence

- §3.3: no data-processing agreement exists with Anthropic on a consumer or team
  subscription; single-operator use is a terms question only, and "as soon as a
  second person feeds in data, it is both".
- §8: the free-tier warning names training use and the missing processing
  agreement, calls it "derselbe Schnitt" as §3.3, and states that both switches
  are thrown together.
- §5.4 lists free and free-tier providers behind the `Transcriber`/`Speaker`
  interfaces (Groq's permanently free quota, faster-whisper and Piper locally),
  which is exactly the set the switch affects.
- §5.4 also removes one category from the question entirely by deleting audio
  after successful transcription.

## Related Concepts

- [[concepts/claude-credentials-and-tenancy]]
- [[concepts/input-channels]]
