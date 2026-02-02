---
description: Structured debugging process to identify and fix bugs
---

# Workflow: Debug

Cuando el usuario use `/debug <problema>`, no adivines. Sigue este proceso científico:

1. **Entender**: Analiza el reporte del error y los archivos implicados.
2. **Reproducir**: 
   - Busca o escribe un test unitario que falle debido a este error.
   - Si no es posible, identifica la secuencia exacta de pasos/datos que causan el fallo.
3. **Hipótesis**: Formula una teoría de por qué ocurre el error.
4. **Experimento**:
   - Aplica una solución mínima.
   - Ejecuta los tests o verifica la lógica.
5. **Verificación**: Confirma que el error ha desaparecido y que NO has roto nada más (regression testing).
6. **Lección**: Si el error fue por un malentendido de la arquitectura, sugiere actualizar las reglas del proyecto (`.agents/rules/`).

// turbo
