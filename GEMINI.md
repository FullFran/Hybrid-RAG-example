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

| Skill           | Description                                                                  | URL                                                                          |
| --------------- | ---------------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| `docs-standard` | Standard for creating technical documentation in this repository.            | [.agent/skills/docs-standard/SKILL.md](.agent/skills/docs-standard/SKILL.md) |
| `skill-creator` | Create and initialize new Antigravity Skills following the project standard. | [.agent/skills/skill-creator/SKILL.md](.agent/skills/skill-creator/SKILL.md) |

## Auto-invoke Rules

Cuando realices las siguientes tareas, DEBES cargar la skill correspondiente para asegurar el cumplimiento cultural:

| Action                      | Skill to invoke          | Trigger                                   |
| --------------------------- | ------------------------ | ----------------------------------------- |
| Creación de nuevas skills   | `skill-creator`          | "Necesito crear una nueva habilidad"      |
| Sincronización de metadatos | `scripts/sync-skills.sh` | "Actualiza el índice de skills"           |
| Documentación técnica       | `docs-standard`          | "Escribe un nuevo documento en docs/"     |
| Implementación RAG          | `architecture.md`        | "Implementa una nueva funcionalidad"      |
| Operaciones MongoDB         | `mongodb.md`             | "Realiza una consulta a la base de datos" |

## Technical Stack

- Environment: Linux / Bash
- Standards: `AGENTS.md`, `agentskills.io`
- Tools: Google Antigravity IDE
- Core: Pydantic AI, MongoDB (Atlas), Docling (Whisper Turbo)
