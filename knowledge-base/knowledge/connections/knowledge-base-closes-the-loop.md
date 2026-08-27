---
title: "Connection: The Compiled Base Becomes a Session Input"
connects:
  - "concepts/kb-researcher-directive"
  - "concepts/index-guided-retrieval"
  - "concepts/knowledge-article-schema"
sources:
  - "daily/2026-08-27.md"
  - "knowledge-base/scripts/research_directive.py"
created: 2026-08-27
updated: 2026-08-27
---

# Connection: The Compiled Base Becomes a Session Input

## The Connection

Until engine version 3 the knowledge base was a terminal artefact: sessions
produced daily logs, the compiler produced articles, and a human asked
`query.py` a question when they thought to. The `kb-researcher` directive closes
that circuit. A research workflow now automatically pulls the compiled base back
into the session that is about to generate the next daily log, alongside the
code explorer, the behaviour analyst, and the web researcher.

## Key Insight

The loop changes what the schema rules are *for*. "Every article links to at
least two others", the `missing_backlink` and `orphan_page` lint checks, and the
insistence that connection articles are rare but real read, at seed time, as
editorial hygiene — a tidy wiki. Once an agent traverses the base under a
directive that says *index first, then walk backlinks*, those rules become the
retrieval mechanism itself. A `connections/` article with no inbound link is not
untidy; it is **invisible**, since the directive states plainly that connection
articles are reachable no other way. `missing_backlink` is filed as a mere
*suggestion* severity in `lint.py`, the weakest level there is — which is now
the check with the most direct effect on whether compiled knowledge is ever
read.

The second consequence runs the other way. The base is no longer only as good as
its articles; it is as good as the articles an agent can *reach in one hop from
the index*. That makes the one-line index summary a load-bearing sentence rather
than a courtesy, and it gives the "prefer UPDATE over CREATE" rule a second
justification beyond the compile-prompt cost argued in
[[connections/compile-prompt-ceiling]]: a fact split across two thin
near-duplicates is a fact an index-first traversal may only half-find.

## Evidence

- `scripts/research_directive.py` states the traversal contract verbatim: the
  agent's report "must cite full article paths, and must walk BACKLINKS after
  the index — `connections/` articles are reachable no other way."
- The directive is delivered on both entry paths into a research skill — typed
  slash command and model-invoked `Skill` tool call — so the pull is automatic
  rather than something a user has to remember.
- The directive names the three prp-core agents explicitly so the base is placed
  *among* the research axes rather than substituted for one; the knowledge base
  is positioned as the source for "prior findings, decisions and gotchas that
  exist nowhere else".
- `AGENTS.md` requires every article to link to at least two others and treats
  the index as "the retrieval mechanism"; `lint.py` grades a missing backlink as
  a suggestion and an orphan page as a warning.

## Related Concepts

- [[concepts/kb-researcher-directive]]
- [[concepts/index-guided-retrieval]]
- [[concepts/knowledge-article-schema]]
- [[concepts/llm-as-compiler-model]] — the analogy this loop extends
