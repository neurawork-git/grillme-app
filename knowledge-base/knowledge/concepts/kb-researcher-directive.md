---
title: "The kb-researcher Directive and Its Two Trigger Paths"
aliases: [kb-researcher, research-directive, fourth-research-axis, pre-skill-hook]
tags: [harness, hooks, retrieval, research]
sources:
  - "daily/2026-08-27.md"
  - "knowledge-base/hooks/user-prompt-submit.py"
  - "knowledge-base/hooks/pre-skill.py"
  - "knowledge-base/scripts/research_directive.py"
  - ".claude/settings.json"
created: 2026-08-27
updated: 2026-08-27
---

# The kb-researcher Directive and Its Two Trigger Paths

Knowledge-compiler engine version 3 adds a second job to the engine: besides
producing articles, it now injects a directive telling the running session to
spawn `neurawork-cc-harness:kb-researcher` as a **fourth research axis** during
PRP research workflows. The directive is delivered by two hooks —
`UserPromptSubmit` and `PreToolUse` with `matcher: "Skill"` — because a research
skill can be entered by two paths and no single hook event sees both.

## Key Points

- **Two paths, two hooks.** A slash command the user types is expanded into the
  prompt and never routed as a tool call, so only `UserPromptSubmit` sees it;
  a skill Claude invokes itself arrives as `tool_name: "Skill"` with
  `tool_input {"skill": "<plugin>:<name>"}` and no new prompt, so only
  `PreToolUse` sees it. Both were probed on Claude Code 2.1.234 (2026-08-18).
- Both hooks render the **same string** from `scripts/research_directive.py`
  rather than duplicating the wording, because the two halves disagreeing about
  which workflow counts as research is exactly the class of bug the module's
  comments record.
- The axis is positioned, not substituted: the directive names
  `prp-core:codebase-explorer` (where code lives),
  `prp-core:codebase-analyst` (how it behaves) and `prp-core:web-researcher`
  (what external sources say), and asks for launch **in the same message** so
  all four run concurrently.
- It passes the resolved absolute knowledge directory verbatim so the agent
  never globs for it, and states a traversal contract: cite full article paths,
  and walk **backlinks** after the index, because `connections/` articles are
  reachable no other way.
- Matching is configurable per repo via `research_directive` (on by default),
  `research_skill_match` and `research_prompt_match`; a pattern that is empty or
  fails to compile falls back to the module default instead of raising or
  matching everything. This repo's `config.json` sets none of them.

## Details

The two default patterns are deliberately not the same regex. The skill pattern
`^([\w-]+:)?prp-(plan|prd|debug)$` makes the plugin prefix optional because
`tool_input["skill"]` is plugin-qualified, and is anchored at both ends so it
rejects `prp-core:prp-prd-update`, a real prp-core skill. The prompt pattern
is anchored at the start only — a mid-sentence "like /prp-prd does" is
discussion, not an invocation — and ends with a negative lookahead rather than
`\b`, since `-` is itself a word boundary and `\b` would wrongly match
`/prp-prd-update` and `/prp-plan-b`, making the two halves disagree.

Registration matters as much as matching. `pre-skill.py` sits in its **own**
`matcher: "Skill"` group in `.claude/settings.json`; placed in the catch-all
group it would spawn a process on every tool call in the session.
`UserPromptSubmit` has no matcher support at all and fires on every prompt in
the repo, which is why both hooks read no corpus files — the directive is a
static string and the config is one small file. The directive is also kept under
a self-imposed `MAX_DIRECTIVE_CHARS = 900`, a precaution against large
`additionalContext` payloads being offloaded to a preview; that threshold was
measured in a sibling repo, not this one.

Both hooks emit nothing at all — no stdout — when the trigger does not match or
the directive is disabled, and both end every path at exit 0. Their failure
modes are engine-specific enough to be documented at the top of each file; see
[[concepts/hook-safety-invariants]] for the exit-code rules they encode.

## Related Concepts

- [[concepts/hook-safety-invariants]] — why both hooks fail open and print only
  a JSON envelope
- [[concepts/index-guided-retrieval]] — the retrieval contract the directive
  hands to the agent
- [[concepts/documentation-harness]] — the engine that ships these hooks
- [[concepts/harness-plugin-and-engine-versions]] — the version that introduced
  them
- [[connections/knowledge-base-closes-the-loop]] — the compiler's output
  becoming a session input

## Sources

- [[daily/2026-08-27.md]] — that v3 adds the two hooks, why a single event
  cannot catch both paths, and that they spawn `kb-researcher` as a fourth axis
  alongside prp-core's three
- `knowledge-base/hooks/user-prompt-submit.py`,
  `knowledge-base/hooks/pre-skill.py` — the two entrypoints and their hard
  constraints
- `knowledge-base/scripts/research_directive.py` — the shared directive text,
  the two default patterns, and the reasoning behind each line
- `.claude/settings.json` — the `matcher: "Skill"` group and the 10s timeouts
