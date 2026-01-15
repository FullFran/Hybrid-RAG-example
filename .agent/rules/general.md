---
name: general
description: General project rules for AI assistance.
activation_mode: always_on
---

# General Project Rules

All AI agents working on this repository MUST adhere to the following rules:

## Documentation

- All new technical documentation must be placed in the `docs/` directory.
- Documentation files must use standard Markdown with clear heading hierarchies.
- Use backticks for file names, directory names, and terminal commands.

## Architecture & Implementation

- **Clean Architecture**: Follow the layers defined in `architecture.md`. Use interfaces from `src/core/interfaces/`.
- **MongoDB vs Supabase**: Prioritize MongoDB implementation in `src/infrastructure/database/mongo_repository.py`. Keep `SupabaseRepository` only for reference or if explicitly requested.
- **Reference Code**: Use `examples/` directory for PostgreSQL patterns, but DO NOT modify it. All new work must happen in `src/`.
- **Specific Rules**: Adhere to `mongodb.md`, `docling.md`, and `pydantic-ai.md` for technical implementations.

## Automation

- Use the provided scripts in `scripts/` for framework maintenance tasks.
- If a workflow exists in `.agent/workflows/` for a task, prioritize using it.
- **Rules Synchronization**: After adding or modifying rule files in `.agent/rules/`, update the summary in `GEMINI.md`.
