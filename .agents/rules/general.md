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

## Architecture
- Do NOT create ad-hoc scripts in the root directory. Use the `scripts/` directory.
- All new agent capabilities MUST be implemented as a "Skill" in the `.agents/skills/` directory.
- A symlink `.agent` -> `.agents` is maintained for IDE compatibility (Antigravity).
- Every `SKILL.md` file MUST contain a valid YAML frontmatter with `name` and `description`.

## Communication
- When proposing major changes, update the `docs/framework-design.md` if applicable.
- Always check the current `AGENTS.md` before starting a new task to understand the latest project norms.

## Automation
- Use the provided scripts in `scripts/` for framework maintenance tasks.
- If a workflow exists in `.agents/workflows/` for a task, prioritize using it.
