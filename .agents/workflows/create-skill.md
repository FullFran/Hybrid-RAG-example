---
description: Automated workflow to create a new AI Skill
---

# Workflow: Create Skill

Cuando el usuario use `/create-skill`, sigue estos pasos:

1. **Definir**: Pregunta el nombre de la skill (en minúsculas y con guiones) y una breve descripción si no la han proporcionado.
2. **Estructura**: Crea el directorio `.agents/skills/<skill-name>/`.
3. **Inicializar**: Escribe el archivo `.agents/skills/<skill-name>/SKILL.md` con el frontmatter YAML correcto (name, description, license: MIT).
   - Usa la skill `skill-creator` como referencia para el contenido.
4. **Sincronizar**: Ejecuta `npm run sync` para actualizar la documentación global.
5. **Confirmar**: Informa al usuario que la skill ha sido creada y sincronizada.

// turbo
