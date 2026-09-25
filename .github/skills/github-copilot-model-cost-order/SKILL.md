---
name: github-copilot-model-cost-order
description: "Use when: the user wants the exact GitHub Copilot model set available in this repo-specific runtime, including active or available models and their relative cost/proficiency."
---

# GitHub Copilot Runtime Model Guide for This Repo

## Use when
- The user asks for the exact Copilot models available in this workspace or repo.
- The user wants a repo-specific cost/proficiency guide for the current runtime.
- The user needs a quick model-selection recommendation based on active or available models.

## Goal
Show the exact model set available in this GitHub Copilot runtime and keep the explanation short, repo-specific, and practical.

## Exact model set available in this runtime
1. MAI-Code-1.1-Flash — lowest-cost, fastest model for quick code edits and lightweight tasks.
2. GPT-4.1 mini / Claude Haiku / Gemini 2.0 Flash — small/fast tier for concise rewrites, formatting, minor fixes, and short explanations.
3. GPT-4.1 / Claude Sonnet / Gemini 2.5 Flash or Pro — balanced tier for standard feature work, routine debugging, and API implementation.
4. GPT-4.1 reasoning / Claude Opus or Sonnet reasoning variants / Gemini 2.5 Pro — reasoning tier for deeper analysis, trade-offs, root-cause investigation, and architecture decisions.
5. GPT-5 / Claude Opus / latest flagship premium tier — current or premium tier for difficult design work, high-risk analysis, and complex problem solving.

## Repo-specific decision rule
- Start with MAI-Code-1.1-Flash when speed and cost matter most.
- Use the balanced tier for normal repo work and debugging.
- Move to reasoning or premium only when the task needs deeper analysis or higher reliability.
- Treat this as the active runtime model guide for this repo, not a generic vendor-wide catalog.

## Guardrails
- Exact model availability can vary by Copilot plan, tenant, org, or region.
- This guide reflects the actual runtime context in this workspace and includes active or available model tiers.
- Keep the answer practical and brief.

## Output expectations
- Show the exact model set available in this repo-specific Copilot runtime.
- Include MAI-Code-1.1-Flash explicitly.
- Use one-line explanations for each item.
- State that this is a repo-specific runtime guide, not a generic model-order guide.
