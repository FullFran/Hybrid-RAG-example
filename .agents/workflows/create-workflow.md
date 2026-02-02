---
description: Automated workflow to create a new slash command workflow
---

# Workflow: Create Workflow

Cuando el usuario use `/create-workflow`, sigue estos pasos:

1. **Planear**: Pregunta qué pasos debe automatizar el nuevo workflow y cómo se llamará (nombre para el slash command).
2. **Crear**: Escribe el archivo `.agents/workflows/<nombre>.md`. 
   - Debe incluir frontmatter con una descripción breve.
   - Debe listar los pasos de forma clara.
3. **Sincronizar**: Ejecuta `npm run sync` para que el nuevo comando sea reconocido.
4. **Habilitar**: Recuerda al usuario que debe ejecutar `npm run init` si quiere habilitar el comando en otros agentes (Copilot, Cursor, etc.).

// turbo
