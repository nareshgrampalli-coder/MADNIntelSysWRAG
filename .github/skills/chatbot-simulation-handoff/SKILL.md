---
name: chatbot-simulation-handoff
description: "Use when: simulating chatbot questions sequentially, concurrently, in randomized order, back-to-back, or as follow-ups; checking response grounding, completeness, category formatting, determinism, and producing a handoff record for another model."
argument-hint: "Question set, index/store, simulation modes, and optional report path"
---

# Chatbot Simulation Handoff

## Purpose
Run a read-only simulation of a chatbot question set across interaction modes, assess response quality against available indexed evidence, and produce a concise record another model can use to implement fixes.

## Execution Boundary
- Do not edit application code, tests, configuration, documentation, or indexed data.
- Do not run ingestion, reset/rebuild an index, or trigger any workflow that changes stored data.
- Do not implement recommendations. Record them as **unexecuted actions** for a follow-on model.
- Use the existing local index and configured query path. If unavailable, stop and record the blocker rather than fetching or creating data.
- Browser checks are read-only. Do not submit ingestion/reset controls. If chat is gated, report that the browser-level message path could not be exercised.
- Return the handoff report in the response. Write it to a file only when the user provides a destination.

## Default Question Set
Use the user's supplied questions when present. Otherwise use:
1. Summarize todays news in 3 bullet points.
2. Summarize in 3 bullet points for each category.
3. What is stock news today?
4. What happened in finance this week?
5. Which news should I focus on today?

Keep wording and punctuation identical across modes. Record any user-provided substitutions.

## Procedure
1. Record the date, repository revision when available, index/store path, embedding provider, indexed item count, and relevant response-rendering path. Do not expose secrets or credentials.
2. Run each question once in the listed order and capture the effective query, answer, grounding status, and citations.
3. Run the same questions concurrently with a bounded worker count. Use the same query engine and store only if they are designed for shared use; otherwise record the limitation and use independent instances where feasible.
4. Run the questions in a shuffled order using a recorded deterministic seed. Compare each result with the sequential baseline.
5. Run each question repeatedly back-to-back (two runs minimum). Compare answers, citations, and status.
6. Run the list as a conversation, passing prior user/assistant turns through the application's actual follow-up/context builder when available. Record the effective query for every turn. Do not call self-contained prompts true contextual follow-ups if their effective queries remain unchanged.
7. If the UI is already available without changing data, verify the same formatting path used by the chat renderer. Record whether a real browser submission was possible; do not bypass ingestion gates.
8. Review quality independently of mode consistency. For every answer check:
   - Evidence relevance and citation support; do not infer correctness from `grounded=True` alone.
   - Complete prose sentences and preserved terminal punctuation. Treat headline fragments separately, and flag mid-sentence truncation or ellipses.
   - Requested bullet count and preservation of category headings and boundaries.
   - Whether each story actually belongs to the displayed category.
   - Noise, duplicated content, stale dates, unsupported claims, or citation/answer mismatch.
9. Produce the handoff report using the template below. Separate verified facts, limitations, and recommended actions. Never claim general thread safety based only on one successful concurrent run.

## Comparison Rules
- Compare each question's complete result across sequential, concurrent, shuffled, and repeated runs. Include answer text, grounding/refusal status, and citation identity/order.
- A follow-up result may differ from a standalone result when prior context changes its effective query. Explain that difference rather than marking it nondeterministic.
- Report exact matches and mismatches; do not normalize away punctuation, missing bullets, category ordering, or citations.
- If answers are stable but irrelevant, incomplete, miscategorized, or unsupported, mark quality as failed even when determinism passes.

## Handoff Record

```markdown
# Chatbot Simulation Handoff

Date:
Revision:
Index/store and item count:
Embedding/query/rendering path:

## Questions and Modes
Questions:
- ...

Mode results:
- Sequential:
- Concurrent: worker count; match status; errors
- Random order: seed and order; match status
- Back-to-back: repeat count; match status
- Follow-up: effective queries; context changes; match status

## Response Findings
- Grounding/citation:
- Sentence completeness and punctuation:
- Bullet/category formatting:
- Relevance/category accuracy:
- Determinism:

## Verification Limits
- ...

## Recommended Actions for Another Model (Not Executed)
1. [Finding] -> [suggested file/symbol or investigation] -> [verification check]
```

## Reporting Guardrails
- Include enough representative answer text to make findings actionable; include all answers when the user requests a complete transcript.
- Keep personal data, credentials, and unrelated article content out of the report.
- Label uncertain causes as hypotheses and specify the evidence that would confirm them.
- End with an explicit status: **Ready for handoff**, **Handoff with unresolved quality issues**, or **Blocked**.
