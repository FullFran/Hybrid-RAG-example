---
description: Perform a deep code review of pending changes
---

# Workflow: Review

Cuando el usuario use `/review`, actúa como un Senior Architect y sigue estos pasos:

1. **Obtener Cambios**: Analiza los diffs de los archivos modificados.
   ```bash
   git diff --cached
   # Si no hay nada staged:
   git diff
   ```

2. **Análisis Crítico**: Revisa cada cambio buscando:
   - **Seguridad**: ¿Hay API keys, contraseñas o datos sensibles expuestos?
   - **Lógica**: ¿Hay posibles bugs, edge cases no manejados o condiciones de carrera?
   - **Estilo**: ¿Se sigue la arquitectura del proyecto (ESM, async/await, etc.)?
   - **Documentación**: ¿Se han actualizado los comentarios o docs necesarios?

3. **Reporte**: Presenta tus hallazgos de forma constructiva:
   - ✅ Lo que está bien.
   - ⚠️ Riesgos potenciales.
   - 🛑 Bloqueos (errores graves).

4. **Sugerencias**: Proporciona fragmentos de código para las mejoras sugeridas.

// turbo
