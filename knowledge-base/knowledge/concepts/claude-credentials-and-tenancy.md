---
title: "Claude Credentials and the Tenancy Coupling"
aliases: [oauth-token-vs-api-key, multi-user-coupling]
tags: [decision, security, privacy, spec]
sources:
  - ".claude/spec.md"
created: 2026-08-20
updated: 2026-08-20
---

# Claude Credentials and the Tenancy Coupling

The backend reaches Claude through a provider interface with two
implementations, both present from day one: a `CLAUDE_CODE_OAUTH_TOKEN` created
once on the host with `claude setup-token`, and an `ANTHROPIC_API_KEY`. Multi-user
operation is **hard-coupled** to the API-key implementation and must not be
startable with a subscription token.

## Key Points

- `~/.claude` is deliberately **not** mounted into the container: that couples
  the container to host state and breaks at the first re-login. The token goes
  into the Compose stack's `.env` instead.
- On a consumer or team subscription there is no data-processing agreement with
  Anthropic, so a second person feeding in data turns a terms-of-use question
  into a data-protection one as well.
- While only the operator uses the instance there is no third-party data subject,
  so the subscription token is purely a terms question.
- The schema reserves an optional, encrypted `user.anthropic_api_key` column from
  the start so each user can later supply their own key.
- With a shared key, token consumption is logged per session (`token_usage`).

## Details

The coupling is stated as an enforcement requirement, not a guideline: the
multi-user mode is bound to the API-key implementation and *must not be
startable* with a subscription token. That turns a legal boundary into a
startup-time check, which is the only place it can be reliably held once the
product is hosted.

The same boundary is drawn a second time in the spec's privacy chapter, about
transcription and speech providers rather than Claude: free tiers typically
permit the provider to use submitted data for training and come without a
data-processing agreement. Irrelevant for single-operator use, mandatory paid
tiers for any operation with third-party users. The spec calls this the same cut
as the Claude credentials and says both switches are thrown together.

Everything else in the privacy chapter follows the same "build the technical
preconditions in v1, do the paperwork at hosting time" split: cascading account
deletion, JSON session export, audio deletion after transcription, and a
processing register in the repository are v1; data-processing agreements, the
privacy policy, technical and organisational measures, and third-country
transfer documentation come with hosting.

## Related Concepts

- [[concepts/grillme-architecture]] — where the provider interface sits
- [[concepts/grillme-v1-scope]] — v1 is single-user by design
- [[concepts/input-channels]] — the speech providers under the same free-tier
  caveat
- [[connections/free-tier-tenancy-boundary]] — the single switch behind both

## Sources

- `.claude/spec.md` — §3.3 credentials, §8 data protection and free-tier
  warning, §9 `user` and `token_usage` tables
