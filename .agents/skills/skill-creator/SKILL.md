---
name: skill-creator
description: Create and initialize new Agent Skills following the agentskills.io standard. Use this when you need to modularize a new capability for the AI agent.
license: MIT
metadata:
  standard: agentskills.io
  version: "1.1"
---

# Skill Creator

This skill guides the agent in creating a new Agent Skill following the official specification.

## Process
1. **Identify the Need**: Determine the specific competence to modularize.
2. **Naming**: Choose a name (1-64 chars, lowercase alphanumeric and hyphens only).
3. **Directory Structure**:
   - Create `.agents/skills/<skill-name>/`
   - (Optional) `.agents/skills/<skill-name>/scripts/` for executable code.
   - (Optional) `.agents/skills/<skill-name>/references/` for deep documentation.
   - (Optional) `.agents/skills/<skill-name>/assets/` for templates and static files.
4. **Initialize SKILL.md**:
   - MUST include YAML frontmatter with `name` and `description`.
   - Name MUST match the directory name.
   - Description MUST be under 1024 characters.
5. **Progressive Disclosure**: Keep `SKILL.md` under 500 lines. Move heavy technical details to `references/`.
6. **Sincronización Obligatoria**: Una vez creada la skill, DEBES ejecutar `npm run sync` para actualizar la documentación global del proyecto en `AGENTS.md`.

## Frontmatter Template
```yaml
---
name: <skill-name>
description: <Clear description of what it does and when to use it>
license: MIT
metadata:
  author: <your-name>
  version: "1.0"
---
```
