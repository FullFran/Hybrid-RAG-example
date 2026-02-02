---
description: Create a new git commit for uncommitted changes following atomic standards
---

# Workflow: Commit

Cuando el usuario use `/commit`, sigue estos pasos para asegurar un historial de Git profesional:

1. **Analizar**: Revisa los cambios pendientes.
   ```bash
   git status --porcelain
   ```

2. **Atomizar**: Agrupa los cambios en unidades lógicas y atómicas. 
   - Separa fixes, features y refactorizaciones.
   - NO mezcles cambios no relacionados en el mismo commit.

3. **Stagear**: Para cada cambio atómico, añade solo los archivos relevantes.
   ```bash
   git add <archivos>
   ```
   *Nota: Puedes usar `git add -p` si necesitas separar cambios dentro de un mismo archivo.*

4. **Redactar**: Escribe un mensaje de commit de alta calidad con este formato:
   - **Subject**: Máximo 50 caracteres, modo imperativo, prefijo de tipo.
   - **Body**: Explica el **porqué** del cambio, no el qué. Envuelve a 72 caracteres.

   ```text
   [feat|fix|docs|refactor|test]: Resumen corto e imperativo

   Descripción detallada de la motivación.
   ¿Qué problema resuelve?
   ¿Hay efectos secundarios?
   ```

5. **Verificar**: Muestra al usuario el resultado final.
   ```bash
   git log -n 5 --oneline --graph
   ```

// turbo
