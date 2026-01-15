# Repository Guidelines

## Overview

This repository contains an AI-assisted programming framework designed to optimize the collaboration between human developers and AI agents.

## Core Principles

1. **Machine-Readable Documentation**: Priority is given to structured `.md` files that agents can easily parse (max 500 lines per file).
2. **Modular Architecture**: Use nested `AGENTS.md` in subdirectories for granular context.
3. **Skill-Based Competence**: Capabilities are organized into modular "skills" following the `agentskills.io` standard.
4. **Auto-Invocation**: Agents are explicitly instructed on when to load specific skills via triggers.

## Project Structure

- `docs/`: Technical documentation and research.
- `.agent/`: Antigravity-specific configuration.
  - `skills/`: Reusable agent competencies.
  - `rules/`: Project behavioral guidelines.
  - `workflows/`: Automated task sequences.
- `scripts/`: Tooling for framework setup and maintenance.

## Available Skills

| Skill | Description | URL |
|-------|-------------|-----|
| `docling` | Expert guidance on document processing with Docling and audio transcription with Whisper. | [.agent/skills/docling/SKILL.md](.agent/skills/docling/SKILL.md) |
| `docs-standard` | Standard for creating technical documentation in this repository. | [.agent/skills/docs-standard/SKILL.md](.agent/skills/docs-standard/SKILL.md) |
| `mongodb` | Expert guidance on MongoDB implementation for RAG, including aggregation pipelines and search patterns. | [.agent/skills/mongodb/SKILL.md](.agent/skills/mongodb/SKILL.md) |
| `pydantic-ai` | Expert guidance on building agents and tools with Pydantic AI. | [.agent/skills/pydantic-ai/SKILL.md](.agent/skills/pydantic-ai/SKILL.md) |
| `skill-creator` | Create and initialize new Antigravity Skills following the project standard. | [.agent/skills/skill-creator/SKILL.md](.agent/skills/skill-creator/SKILL.md) |
| `supabase` | Expert guidance on Supabase/PostgreSQL implementation for RAG, including pgvector semantic search and full-text search. | [.agent/skills/supabase/SKILL.md](.agent/skills/supabase/SKILL.md) |
| `workflow-creator` |  | [.agent/skills/workflow-creator/SKILL.md](.agent/skills/workflow-creator/SKILL.md) |
## Auto-invoke Rules

Cuando realices las siguientes tareas, DEBES cargar la skill correspondiente para asegurar el cumplimiento cultural:

| Creación de nuevas skills | `skill-creator` | "Necesito crear una nueva habilidad" |
| Creación de nuevos workflows | `workflow-creator` | "Necesito crear un nuevo workflow" |
| Sincronización de metadatos | `scripts/sync-skills.sh` | "Actualiza el índice de skills" |
| Documentación técnica | `docs-standard` | "Escribe un nuevo documento en docs/" |

## Technical Stack

- Environment: Linux / Bash
- Standards: `AGENTS.md`, `agentskills.io`
- Tools: Google Antigravity IDE
