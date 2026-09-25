# Standardized LLM Prompt Template

Use this template when asking the model to make changes in this repository. It keeps the request compact, scoped, and aligned with the project’s patterns.

## Prompt format

```text
MODE: <ULTRA-CHEAP|AGGRESSIVE|MODERATE|CONSERVATIVE>
Intent: <answer-only|small-edit|multi-file>
Task: <one sentence describing the requested fix or feature>
Scope: <exact file(s) or modules involved>
Constraints:
- <keep output concise>
- <do not broaden scope>
- <preserve existing architecture and naming patterns>
- <do not refactor unrelated code>
- <do not add dependencies unless necessary>
- <do not change behavior outside the requested area>
- <if auto model selection is enabled, use the lowest-cost model first and only escalate when needed>
Acceptance criteria:
- <what must be true after the change>
- <what must remain unchanged>
Output: <brief result format, e.g. patched file(s), short explanation, or validation result>
```

## Project-specific rules

- Keep changes focused to the requested feature or bug.
- Preserve the current page structure and route separation:
  - open-IPO logic stays in open-IPO context
  - past-issues logic stays in past-issues context
  - shared helpers may stay only when truly common
- Prefer minimal, direct edits over large rewrites.
- Follow existing file naming conventions and the repository’s app structure under `web/app` and `web/lib`.
- If a change affects UI behavior, make sure the header, content, and summary logic match the correct page context.
- When the environment auto-selects a model, prefer the lowest-cost available model first; escalate only if the cheaper model cannot complete the task correctly.
- Validate only with the smallest relevant command when needed.

## Good example prompts

### Bug fix

```text
MODE: AGGRESSIVE
Intent: small-edit
Task: Fix the past-issues page so it shows only recent closed/listed IPOs from the last 30 days.
Scope: web/lib/ipo-data.ts, web/app/IpoDashboard.tsx
Constraints:
- keep open-IPO and past-IPO logic separate
- no unrelated refactor
- do not mix open-IPO copy into past-issues content
Acceptance criteria:
- past page only shows recent closed/listed IPOs
- open page remains open-only
- no stale or placeholder values
Output: concise summary plus files changed
```

### Feature work

```text
MODE: MODERATE
Intent: multi-file
Task: Add a summary card for recent past IPO performance without changing the open-IPO page behavior.
Scope: web/app/past-issues/page.tsx, web/app/IpoDashboard.tsx, web/lib/ipo-data.ts
Constraints:
- preserve current dashboard layout
- use existing component patterns
- do not alter open-IPO logic
Acceptance criteria:
- card reflects only past IPO metrics
- no open-IPO content appears in past view
- build passes
Output: changed files and verification result
```

### Documentation or refactor request

```text
MODE: ULTRA-CHEAP
Intent: small-edit
Task: Update the modularization skill to require functionality-based file names for extracted components.
Scope: .github/skills/component-modularization/SKILL.md
Constraints:
- keep wording concise
- preserve project conventions
- no unrelated changes
Output: updated skill text only
```

## Output quality guardrails

- Do not ask for unnecessary clarification when the task is clear.
- Remove filler, repetition, and unrelated narrative.
- Keep the output actionable and direct.
- If the task is code-related, prefer exact file names and minimal implementation details.
- If the task is documentation-related, keep the update scoped and stable.

## Quick user checklist

Before sending a prompt, confirm:

- [ ] The task is specific and scoped.
- [ ] Files or modules are named.
- [ ] Constraints are clear.
- [ ] Acceptance criteria are explicit.
- [ ] Output format is defined.
- [ ] The request does not broaden beyond the current task.
- [ ] If auto model selection is enabled, the prompt prefers the lowest-cost model first.
