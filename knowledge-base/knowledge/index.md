# Knowledge Base Index

| Article | Summary | Compiled From | Updated |
|---------|---------|---------------|---------|
| [[concepts/grillme-app-repository]] | What `grillme-app` holds today: no application source, the GrillMe v1 spec, and three harness engines | CLAUDE.md, README.md, .claude/spec.md, .claude/settings.json | 2026-08-20 |
| [[concepts/grillme-v1-scope]] | The GrillMe product in v1 — screens, single-user Compose operation, prompt library, gamification, deferred items | .claude/spec.md | 2026-08-20 |
| [[concepts/grillme-architecture]] | Next.js/CopilotKit → FastAPI/AG-UI → Claude Agent SDK, with Postgres, MinIO, and speech interfaces | .claude/spec.md | 2026-08-20 |
| [[concepts/agent-state-in-postgres]] | The SDK's own session persistence is bypassed; Postgres is the only source of truth and every round starts fresh | .claude/spec.md | 2026-08-20 |
| [[concepts/grill-decision-tree]] | The JSON decision tree, the per-round frontier, and user-confirmed session closure | .claude/spec.md | 2026-08-20 |
| [[concepts/input-channels]] | Text, voice, and screenshots in one history; Transcriber/Speaker providers and audio deletion | .claude/spec.md | 2026-08-20 |
| [[concepts/claude-credentials-and-tenancy]] | OAuth token vs. API key, and why multi-user operation is hard-coupled to the key | .claude/spec.md | 2026-08-20 |
| [[concepts/documentation-harness]] | The NeuraWork engines installed here — learner, knowledge compiler, and vendored `_shared/` | CLAUDE.md, docs/documentation-pipeline.md, engine CLAUDE.md + AGENTS.md | 2026-08-20 |
| [[concepts/llm-as-compiler-model]] | `daily/` is source, the LLM is the compiler, the docs are the executable | CLAUDE.md, docs/documentation-pipeline.md, both AGENTS.md | 2026-08-20 |
| [[concepts/capture-distil-synthesise-pipeline]] | The three stages a session passes through, plus seeding as stage 0 | CLAUDE.md, docs/documentation-pipeline.md, docs/hooks-runbook.md | 2026-08-20 |
| [[concepts/hook-safety-invariants]] | Never under `.claude/`, never crash a session, atomic writes, recursion guard | CLAUDE.md, docs/hooks-runbook.md, docs/documentation-pipeline.md | 2026-08-20 |
| [[concepts/background-spawn-gate]] | The four conditions for an automatic background run, and worktree behaviour | docs/hooks-runbook.md, CLAUDE.md, engine CLAUDE.md files | 2026-08-20 |
| [[concepts/knowledge-article-schema]] | Article kinds, frontmatter, wikilink rules, index/log roles, and the lint checks | knowledge-base/AGENTS.md, knowledge-base/CLAUDE.md | 2026-08-20 |
| [[concepts/index-guided-retrieval]] | Why the base uses a curated index instead of RAG, and how `query.py` behaves | knowledge-base/AGENTS.md, docs/documentation-pipeline.md, CLAUDE.md | 2026-08-20 |
| [[concepts/compliance-compiler]] | `compliance-base/` — framework constraints, derived capabilities, and PRP plan validation | compliance-base/AGENTS.md, catalog/, config.json, hooks + scripts | 2026-08-20 |
| [[connections/agent-state-and-decision-tree]] | Discarding SDK sessions and persisting the tree are one decision seen twice | .claude/spec.md | 2026-08-20 |
| [[connections/free-tier-tenancy-boundary]] | Claude credentials and speech-provider tiers are governed by the same single switch | .claude/spec.md | 2026-08-20 |
| [[connections/harness-outputs-are-the-only-executable]] | With no app source, the harness's documentation is the repo's only compiled artefact | CLAUDE.md, README.md, .claude/spec.md, knowledge-base/CLAUDE.md | 2026-08-20 |
| [[connections/compile-prompt-ceiling]] | The ~2,000-article limit is argued for queries but reached by `compile.py` first | docs/documentation-pipeline.md, knowledge-base/CLAUDE.md, knowledge-base/AGENTS.md | 2026-08-20 |
