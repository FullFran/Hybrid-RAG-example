---
description: create-skill automated workflow
---

# Workflow: Create Skill

This workflow automates the process of creating a new AI Skill.

## Steps

1. Ask the agent to define the new skill's name and purpose.
   // turbo
2. Create the directory: `mkdir -p .agent/skills/<skill-name>`
3. Initialize the `SKILL.md` file using the `skill-creator` template.
   // turbo
4. Run the sync script: `./scripts/sync-skills.sh`
5. Verify the new skill appears in `AGENTS.md`.
