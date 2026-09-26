---
name: update-all-markdown-docs
description: "Use when: update design documents, refresh architecture and workflow docs, align README and markdown files, standardize documentation across the repository."
---

# Update Design and Markdown Documentation

## Use when
- The user asks to update design documents or architecture notes.
- One or more Markdown files need alignment with the current system design, workflows, or implementation.
- README, architecture, sequence, workflow, ADR, or operational docs are outdated or inconsistent.
- The task is documentation-focused but tied to real code and product behavior.

## Scope
- Applies to Markdown files matching `**/*.md` in the workspace.
- Includes design-oriented files such as `README.md`, `docs/architecture.md`, `docs/workflow.md`, `docs/sequence.md`, and `docs/adr/**`.
- Keeps project-specific structure and naming conventions intact.

## Standard workflow
1. Review the relevant design or reference docs and the current implementation they describe.
2. Identify stale architecture, workflow, sequence, or operational details.
3. Update only the affected files, keeping scope narrow and evidence-based.
4. Preserve the project’s intended structure, technical language, and domain terminology.
5. Keep design content concise, accurate, and traceable to the current app and repository structure.
6. Avoid formatting-only churn unless the task explicitly requires a doc refresh.

## Guardrails
- Do not invent product behavior, architecture choices, or deployment flow not supported by the codebase.
- Do not mix open-IPO and past-IPO implementation notes into design docs unless explicitly required.
- Preserve important commands, assumptions, and operational context.
- Prefer factual updates over broad rewrites.
- If a design doc is clearly out of date, reconcile it with the current repository layout and implementation.

## Typical tasks
- Refresh architecture and system-overview documentation
- Update workflow, sequence, or integration diagrams and narrative text
- Clarify deployment and operational guidance
- Align ADR records with current implementation decisions
- Fix documented assumptions that no longer match code behavior

## Example
```bash
# review relevant docs and design files
find docs -name "*.md" -o -name "README.md"
```

## Output expectations
- Summarize which design or Markdown files were updated.
- Mention the key factual corrections or clarifications made.
- Call out any files left unchanged because they already matched current behavior.
