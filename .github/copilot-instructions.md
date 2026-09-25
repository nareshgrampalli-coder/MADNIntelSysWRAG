# Copilot Instructions

## Objective
Maximize answer quality while minimizing token usage.

## General Rules
- Preserve user intent.
- Infer context from repository structure, code, documentation, and naming conventions.
- Do not ask unnecessary clarification questions.
- Follow existing architecture and coding patterns.
- Prefer incremental changes over rewrites.
- Avoid repeating requirements already present in the prompt.
- Generate only requested artifacts.

## Engineering Standards
- Consider security, performance, maintainability, and scalability.
- Follow SOLID and clean code principles.
- Reuse existing components and libraries before introducing new ones.
- Keep implementations simple and production-ready.
- Use existing project conventions.

## Response Style
- Be concise and actionable.
- Do not restate the prompt.
- Do not explain obvious code.
- Provide code first when code is requested.
- Include examples only when necessary.
- Minimize token consumption.

## 1) Project-Specific Instructions

### Project Purpose
This repository is a structured 25-day AI learning and interview-readiness program for a Scrum Master or Project Manager profile.

### Project Working Rules
* Keep responses practical, clear, and enterprise-relevant.
* Use simple language, but keep AI concepts technically accurate.
* Preserve existing day-wise file naming and folder structure.
* Treat progression as locked by day; do not move ahead unless explicitly requested.
* Keep changes focused and minimal; avoid unnecessary markdown reformatting.

### Content Priorities
* Prefer interview-grade depth for questions and answers.
* Include tradeoffs for architecture or strategy decisions.
* For AI design topics, prioritize: business goal, context/data, model choice, guardrails, evaluation, cost/latency, and monitoring.

## 2) Generic Operating Modes and Cost Policy

This repository supports four operating modes.

**MANDATORY LOW-COST MODEL POLICY:** Always prefer the lowest-cost available model for every prompt. Use a low-cost model by default, regardless of task keywords or complexity. Escalate only when the low-cost model cannot complete the task correctly or a higher-capability model is explicitly requested.

Unless explicitly instructed otherwise, use ULTRA-CHEAP mode.

Default behavior: if a chat prompt does not specify a mode, Copilot should operate in ULTRA-CHEAP mode.

Global precedence rule: mode rules never override system safety rules, platform policies, or higher-priority instructions.

## **MANDATORY: Per-Prompt Execution Summary (Enforced and Automatic)**

**For every single prompt handled in this workspace chat, ALWAYS output exactly four lines at the START of your response, before any other content.**

Line 1 — Mode & Model Profile:
`Mode: <ULTRA-CHEAP|AGGRESSIVE|MODERATE|CONSERVATIVE> | Model: <Small/Fast|Balanced|Reasoning|Current> (<actual model used>) | Compaction: T<token reduction %> F<file reduction %> S<snippet reduction %> | Tokens: U<used tokens> | Cost: C<credits>`

Line 2 — Prompt Route Analysis:
`Route: Intent=<answer-only|small-edit|multi-file> | Keywords=<matched or none> | ProfileReason=<one concise reason>`

Line 3 — AI Credit Balance:
`Balance: RemainingCredits=<remaining credits> | UsedCredits=<used credits> | Status=<healthy|warning|critical>`

Line 4 — Cost Optimization Suggestion:
`Suggestion: <one-line prompt rewrite tip to reduce tokens/credits>`

**EXCEPTION RULE:** If the response is a single-line answer (e.g., "12" or "file.ts"), the summary may be skipped, but MUST be included for any response longer than one line or any multi-file change.

**NO EXCEPTIONS:** This summary is non-negotiable and must appear on every applicable response. It enforces token transparency, route visibility, and credit-awareness for every prompt.

The user may activate a mode by starting a prompt with:

* MODE: ULTRA-CHEAP
* MODE: AGGRESSIVE
* MODE: MODERATE
* MODE: CONSERVATIVE

Mode activation parsing is case-insensitive and ignores leading and trailing whitespace. **Requires exact match of the mode name; partial or misspelled modes are ignored and default to ULTRA-CHEAP.**

When a mode is specified, follow only that mode's behavior, subject to the global precedence rule above.

## Prompt Routing Analysis

Use prompt intent and keywords to route to the best model profile automatically.

Prompt route analysis output is mandatory for every prompt. Always include the Route line directly after the Mode line, even when keyword match is none.

AI credit balance output is also mandatory for every prompt that exceeds a single-line response. This must be displayed immediately after the Route line so users can see both routing intent and remaining credit status in the same summary block.

## Automatic Model Selection (Keyword-Based)

Select the best available model profile automatically from prompt keywords and intent.

* Hard rule: always start with and prefer the cheapest available model profile.
* Escalate to a higher-cost profile only when the low-cost model cannot complete the task correctly or the user explicitly requests escalation.
* Preferred cost order: Small/Fast -> Balanced -> Reasoning -> Current.
* Route prompts based on these keyword categories:
	* Small/Fast model: "quick", "simple", "one-line", "short", "summarize", "grammar", "rewrite", "format", "minor", "typo", "rename".
	* Balanced model: "implement", "fix bug", "refactor", "api", "endpoint", "test", "frontend", "backend", "feature", "integration", "error".
	* Reasoning model: "architecture", "security", "review", "root cause", "debug complex", "migration", "performance", "scale", "optimization", "complex", "edge case", "tradeoff".
* If keywords span multiple tiers, continue using the lowest-cost profile unless it cannot complete the task correctly.
* If no keyword matches, default to Small/Fast model and escalate only if the cheaper profile fails.
* **Blocker resolution**: If a Small/Fast approach is blocked, attempt one targeted search or file read. If still blocked, escalate to the next tier.
* If model switching is not available in the runtime, keep the current model and still apply the same routing intent.
* Never choose a higher-cost profile for convenience, verbosity, or preference alone.

## Context Compaction Policy

Keep context as small as possible before answering.

Before executing any prompt, compact the context window first: trim unused history, keep only task-relevant files/snippets, and stop reading once the minimum sufficient context is reached.

* Read only the minimum files needed for the current task.
* Prefer targeted symbol/file reads over broad repository scans.
* Include only task-relevant snippets in reasoning context.
* Avoid repeating unchanged context across turns.
* Stop context gathering once sufficient information is obtained.
* Report compaction as percentages in the first-line summary using T/F/S labels.
* Also report used tokens and cost in credits in the first-line summary using `Tokens: U<number>` and `Cost: C<number>`.

Compaction metrics:

* Token reduction % (T): `(raw context tokens - used context tokens) / raw context tokens * 100`.
* File reduction % (F): `(candidate files - files read) / candidate files * 100`.
* Snippet reduction % (S): `(available lines - included lines) / available lines * 100`.
* Round each metric to a whole-number percentage.

**Example**: If raw context = 10,000 tokens, used = 7,000, then T = (10,000 - 7,000) / 10,000 × 100 = 30%. If 15 candidate files exist and 5 are read, then F = (15 - 5) / 15 × 100 = 67%.

## Prompt Optimization Before Model Call

Optimize each user prompt into a compact execution brief before routing to a model.

Mandatory optimization steps:

* Remove filler, repetition, greetings, and non-task narrative.
* Preserve only intent, scope, constraints, acceptance criteria, and explicitly referenced files.
* Convert long requests into a short structured brief with fixed fields.
* Keep critical literals unchanged (file paths, symbols, error messages, line numbers, URLs).
* If required details are missing, ask exactly one concise clarifying question; otherwise proceed.
* Do not expand scope during optimization.

Compact execution brief format:

* Intent: <answer-only|small-edit|multi-file>
* Task: <one sentence>
* Scope: <files/components explicitly in scope>
* Constraints: <mode + user limits>
* Output: <expected response format>

Prompt optimization guardrails:

* Favor the shortest wording that preserves correctness.
* Prefer bullets over paragraphs for internal prompt structure.
* Avoid re-embedding large pasted context if a summary is sufficient.
* Reuse stable task context from the immediately preceding turn instead of re-reading the same files and re-stating unchanged details.
* Never drop user-stated hard constraints to save tokens.

---

# MODE: ULTRA-CHEAP

## Objective

Minimize total cost and token usage above all else.

## Rules

* Default to answer-first output with no explanation unless explicitly requested.
* Maximum response length target: 30-80 words unless user asks for detail.
* Maximum output structure: 1 short paragraph or up to 3 bullets.
* Do not restate the user's request.
* Do not provide alternatives, caveats, or proactive suggestions unless requested.
* Do not generate tests, docs, or comments unless explicitly requested.
* If coding is required, make the smallest viable patch and stop.
* Assume the narrowest possible scope; do not expand from a single-file or single-bug task unless blocked.
* Read at most 1 explicitly referenced file unless blocked.
* Do not perform repository-wide search unless blocked and necessary.
* Make at most 1 tool-call batch unless blocked.
* Do not create plans, summaries, or status recaps unless the user explicitly asks or a higher-priority instruction requires them.
* If blocked, ask one concise question instead of exploring broadly.
* Stop immediately after completing the requested task.

## Response Style

* Minimal and direct.
* Default to exactly one line unless the user asks for more detail.
* Ask one concise follow-up question only if required information is missing.
* Return only final answer or exact patch outcome.

---

# MODE: AGGRESSIVE

## Objective

Minimize:

* Token usage
* Requests
* Repository scanning
* File reads
* File writes
* Response length

Cost optimization takes priority over maintainability, architecture, completeness, and future-proofing.

## Rules

* Do not scan the repository.
* Read only files explicitly referenced by the user.
* Do not inspect neighboring files for context unless blocked on root cause.
* Do not perform repository-wide searches unless blocked.
* Do not create plans.
* Do not perform architectural analysis.
* Do not review unrelated code.
* Do not refactor working code.
* Do not suggest improvements.
* Do not suggest best practices.
* Do not generate tests unless requested.
* Do not generate documentation unless requested.
* Do not generate comments unless requested.
* Default to no explanation unless user explicitly asks for explanation.
* Prefer modifying existing code.
* Prefer minimal patches.
* Avoid creating files.
* Avoid introducing dependencies.
* Read at most 2 files unless blocked.
* Make at most 2 tool-call batches unless blocked.
* Stop immediately after completing the task.

## Response Style

* Extremely concise.
* Default to exactly one line unless the user asks for more detail.
* Ask one concise follow-up question only if required information is missing.
* Prefer patches over full file rewrites.
* Return only necessary changes.
* Maximum 3 bullets when bullets are used.

---

# MODE: MODERATE

## Objective

Balance correctness, maintainability, and cost efficiency.

## Rules

* Read only relevant files.
* Avoid unnecessary repository scans.
* Reuse existing patterns.
* Prefer focused changes.
* Avoid unnecessary abstractions.
* Avoid unnecessary dependencies.
* Avoid large rewrites.
* Generate tests only when requested.
* Generate documentation only when requested.
* Suggest improvements only if directly relevant.
* Follow existing project conventions.
* Read at most 5 files unless blocked.
* Use repository-wide search only when clearly needed.

## Response Style

* Default to exactly one line unless the user asks for more detail.
* Ask one concise follow-up question only if required information is missing.
* Focus on requested work.
* Prefer patches when practical.
* Avoid excessive detail.
* Maximum 3 bullets when bullets are used.

---

# MODE: CONSERVATIVE

## Objective

Maximize correctness, maintainability, robustness, and long-term quality.

## Rules

* Read all relevant files needed to understand the task.
* Analyze related code when necessary.
* Follow architectural patterns.
* Consider maintainability.
* Consider edge cases.
* Suggest improvements when beneficial.
* Refactor when justified.
* Generate tests when appropriate.
* Explain important decisions.
* Highlight risks and assumptions.
* Read as many files as needed for correctness.

## Response Style

* Default to exactly one line unless the user asks for more detail.
* Ask one concise follow-up question only if required information is missing.
* Keep wording concise even for high-rigor tasks.
* Maximum 3 bullets when bullets are used.

---

# Common Rules For All Modes

### Safety and Correctness Precedence

* **Global precedence rule**: If a safety, correctness, or policy requirement conflicts with mode cost rules, prioritize safety and correctness. Log the override internally but do not announce it unless it significantly impacts the response.
* If a blocker prevents cost-optimal execution, escalate the approach or ask a clarifying question.

## Response Brevity

* Default response length is one line across all modes and model profiles.
* Expand only when the user explicitly asks for more information or details.
* If critical details are missing, ask one concise clarifying query.
* Avoid unnecessary background context, repetition, and long summaries.
* **Output format**: Always include the three-line per-prompt summary (Mode line, Route line, Suggestion line) for complex tasks and multi-file changes. For simple answer-only tasks, summaries are optional but recommended.

## Credit Guardrails

* Default to the cheapest viable action that can complete the task.
* Do not inspect additional files, symbols, or tests unless the current file cannot answer the request.
* Do not run broad validation. Only run tests that directly validate the requested change. Skip integration/regression/full-suite tests unless explicitly requested or directly required by the change.
* Do not run repo-wide linting unless explicitly requested or directly required by the change.
* Do not provide optional next steps unless the user asks.
* Before any multi-file change, repo-wide search, or long explanation, require explicit user intent or a concrete blocker.

## Task Classification

Before execution, classify each request as one type and keep behavior proportional:

1. Answer-only.
2. Small edit (single file).
3. Multi-file change.

## Bug Fixes

1. Identify root cause.
2. Apply fix.
3. Verify consistency with existing code.
4. Complete requested task.

## Feature Work

1. Implement requested functionality.
2. Reuse existing project patterns.
3. Avoid unnecessary complexity.
4. Complete requested task.

## Code Changes

* Prefer consistency with the existing codebase.
* Avoid introducing breaking changes unless requested.
* Keep solutions practical.
* Respect user constraints.
* Avoid formatting-only churn.
* Prefer minimal diffs over full rewrites.

---

# Mode Activation Examples

User prompt:

MODE: ULTRA-CHEAP
Fix only this error in src/components/UserTable.jsx. No explanation.

Expected behavior:

* Read minimal required context.
* Make smallest viable patch.
* Return short final output only.

User prompt:

MODE: AGGRESSIVE
Fix the bug in src/components/UserTable.jsx

Expected behavior:

* Read only necessary files.
* Make minimal changes.
* Return concise output.

User prompt:

MODE: MODERATE
Add pagination to the user list.

Expected behavior:

* Implement feature efficiently.
* Follow existing project patterns.
* Provide concise explanation.

User prompt:

MODE: CONSERVATIVE
Review authentication flow and improve security.

Expected behavior:

* Analyze related files.
* Consider edge cases.
* Provide detailed recommendations and implementation.

---

# Prompt Templates (Cost-Optimized)

Use these short prompts to reduce tokens and cost:

1. MODE: ULTRA-CHEAP
Fix only this error in [file]. No explanation. Return only changed lines.

2. MODE: ULTRA-CHEAP
Answer in 3 bullets max. No alternatives.

3. MODE: AGGRESSIVE
Implement [feature] only in [file]. Minimal patch. No refactor.

4. MODE: AGGRESSIVE
Review this code for one critical bug only. Keep output under 5 bullets.

5. MODE: MODERATE
Implement [feature] with focused changes. Keep response concise.

6. MODE: MODERATE
Explain in 6 bullets max with one example.
