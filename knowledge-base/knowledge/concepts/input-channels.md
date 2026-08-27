---
title: "Input Channels: Text, Voice, Images"
aliases: [voice-mode, transcriber-speaker, screenshots]
tags: [product, voice, spec, providers]
sources:
  - ".claude/spec.md"
created: 2026-08-20
updated: 2026-08-20
---

# Input Channels: Text, Voice, Images

GrillMe accepts a grilling session in text, in speech, or with screenshots, all
into one history. Text mode puts dictated speech into the input field as
editable text that is sent manually; voice mode sends recognised speech straight
out and has the agent answer with speech as well. The mode is switchable at any
point mid-session.

## Key Points

- A session-wide mode lock would repeatedly push the user into the wrong mode: a
  long grilling has hard thinking passages one wants to speak and precise
  answers ("Q4: b") one wants to type.
- Editable transcripts in text mode are a correctness feature, not a
  convenience — a misrecognised word creates a wrong node in the decision tree
  and costs whole rounds later.
- v1 voice dialogue is **turn-based** (pause detection → audio to backend →
  transcription → agent → speech output), roughly two to four seconds per turn.
- **Audio is deleted after successful transcription**; only the text remains.
- Screenshots go to MinIO, stay part of the history permanently, and are re-sent
  on every follow-up call.

## Details

Speech-to-text and text-to-speech both sit behind interfaces (`Transcriber`,
`Speaker`) with several interchangeable implementations, so choosing a provider
is a configuration decision rather than a rebuild. The default is Deepgram for
both — Nova-3 for transcription, Aura-2 for speech output — chosen for one
vendor, one key, one credit balance ($200 to start, $0.0043/min transcription,
$0.030 per 1,000 characters of speech output), and because Aura-2 handles
German.

Alternatives are foreseen behind the same interfaces: Groq
`whisper-large-v3-turbo` (permanently free at 2,000 requests/day and 7,200 audio
seconds/hour, $0.04/h after), AssemblyAI Universal-3.5 Pro (best cloud accuracy
at 7.69 WER against Nova-3's 12.22, $50 starting credit ≈ 185 h),
faster-whisper locally (no key, audio never leaves the machine), and Piper
locally for speech output. ElevenLabs is ruled out: 10,000 characters a month,
no commercial rights on the free tier, and mandatory attribution. The
interchangeability is not an end in itself — German with English technical
vocabulary is the hard case, and which provider handles it best is decided on
real recordings, not benchmarks.

Deleting audio is justified as making an entire data-protection chapter moot
instead of managing it: voice recordings are the most sensitive data category in
the system and are not needed once transcribed. Images take the opposite
approach and are kept, because a screenshot is often the core of a requirement
and the agent must not have forgotten it by round eight; if image tokens ever
hurt, the planned optimisation is replacing older images with their textual
description — not in v1.

Full duplex with interruption mid-sentence is phase 2. Anthropic offers no
realtime speech API, so transcription and speech output would have to be
streamed separately and orchestrated by hand; whether that is worth it shows
only after some real sessions.

## Related Concepts

- [[concepts/grillme-architecture]] — where the interfaces and MinIO sit
- [[concepts/grillme-v1-scope]] — the session flow these channels feed
- [[concepts/claude-credentials-and-tenancy]] — the same free-tier caveat
  applies to these providers
- [[connections/free-tier-tenancy-boundary]] — one switch governs both

## Sources

- `.claude/spec.md` — §5.1 modes, §5.2 voice dialogue, §5.3 images,
  §5.4 provider selection and audio deletion, §8 free-tier warning
