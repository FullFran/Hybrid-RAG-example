---
name: workflow-creator
description: Create new Antigravity workflows to automate repetitive tasks. Use this when the user wants to formalize a multi-step process into an automated workflow.
license: MIT
---

# Workflow Creator Skill

This skill allows the agent to create structured workflows for Antigravity.

## Workflow Format
Workflows are markdown files in `.agents/workflows/` that follow this structure:

\`\`\`markdown
---
description: [short title]
---
# Workflow: [Name]

[Steps...]
// turbo
[Step that involves a run_command can be auto-run if annotated with // turbo]
\`\`\`

## Process
1. **Define Task**: Identify the sequence of steps.
2. **Create File**: `.agents/workflows/<workflow-name>.md`
3. **Annotate**: Use `// turbo` for safe command steps.
4. **Sync**: Ejecuta `npm run sync` para que el nuevo workflow aparezca en la documentación global.
5. **Enable**: Informa al usuario que debe ejecutar `npm run init` si quiere habilitar el comando en agentes no-automáticos (como Cursor o Copilot).
