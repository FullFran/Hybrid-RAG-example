---
description: Create architecture diagrams using the mermaid-diagrams skill
---

# Workflow: Document Architecture

Automates the creation of Mermaid diagrams for documenting a service or component.

## Steps

1. Load the mermaid-diagrams skill:

   ```bash
   cat .agent/skills/mermaid-diagrams/SKILL.md
   ```

   // turbo

2. Identify the target file to document (e.g., `src/services/my_service.py`).

3. Read the target file outline to understand its structure:

   ```bash
   # Review methods and classes
   ```

   // turbo

4. Create a new documentation file in `docs/` with:

   - **Sequence Diagram**: For the primary use case flow
   - **Component Diagram**: For static dependencies
   - Follow the styling guidelines from the skill

5. Verify the diagrams render correctly:

   - Open in VS Code Markdown Preview (`Ctrl+Shift+V`)
   - Or test at https://mermaid.live

6. Link the new doc from the main architecture file if applicable.
