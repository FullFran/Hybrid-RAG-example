# Documentation Culture & Standards

This rule defines the standards for documentation and agent interaction within this repository.

## Machine-Readable Documentation

- Priority is given to structured `.md` files that agents can easily parse.
- Files should aim for a maximum of 500 lines to ensure context window efficiency.
- Use semantic Markdown headers and lists.

## Modular Architecture

- Use nested `AGENTS.md` in subdirectories for granular, component-specific context.
- Avoid duplicating global rules in local `AGENTS.md` files; focus on what makes that specific subtree unique.

## Skill-Based Competence

- Capabilities are organized into modular "skills" following the `agentskills.io` standard.
- Agents should proactively check for relevant skills in `.agent/skills/`.

## Auto-Invocation Triggers

Agents MUST load the corresponding skill when the following triggers are detected:

| Action                       | Skill to invoke          | Trigger                               |
| ---------------------------- | ------------------------ | ------------------------------------- |
| Creación de nuevas skills    | `skill-creator`          | "Necesito crear una nueva habilidad"  |
| Creación de nuevos workflows | `workflow-creator`       | "Necesito crear un nuevo workflow"    |
| Sincronización de metadatos  | `scripts/sync-skills.sh` | "Actualiza el índice de skills"       |
| Documentación técnica        | `docs-standard`          | "Escribe un nuevo documento en docs/" |
| Implementación RAG           | `supabase` or `mongodb`  | Use when modifying db/search logic    |
