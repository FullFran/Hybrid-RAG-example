# Agent Culture & Behavior Guide

Welcome, Agent. This file defines your role and interaction style within this repository.

## Core Mandates

1.  **Modularity First**: Favor modular skills in `.agent/skills/` over monolithic scripts.
2.  **Context Hygiene**: Refer to `.agent/rules/docs-culture.md` for documentation standards. Don't clutter the codebase with redundant docstrings.
3.  **Proactive Skill Loading**: Check the `Available Skills` table below and load tools as soon as a relevant task is identified.

## Interaction Style

- **Conciseness**: Avoid verbose explanations. Use markdown artifacts for complex plans.
- **Directness**: If a command is safe (e.g., `git status`, `ls`, `pytest`), run it proactively.
- **Validation**: Always verify changes by running relevant scripts or checking directory structures.

## Essential Skills

| Skill                  | Purpose               | URL                                                                                             |
| ---------------------- | --------------------- | ----------------------------------------------------------------------------------------------- |
| `docs-standard`        | Tech writing standard | [.agent/skills/docs-standard/SKILL.md](.agent/skills/docs-standard/SKILL.md)                    |
| `skill-creator`        | Bootstrap new skills  | [.agent/skills/skill-creator/SKILL.md](.agent/skills/skill-creator/SKILL.md)                    |
| `supabase` / `mongodb` | DB-specific RAG logic | [Skills Folder](file:///home/franblakia/blakia/blakiaxhagalink/Hybrid-RAG-Agent/.agent/skills/) |

## Behavior Triggers

- **RAG Implementation**: When modifying ingestion or retrieval, load `docling` and the relevant DB skill.
- **Process Automation**: If you see a repetitive pattern, offer to create a workflow in `.agent/workflows/`.
