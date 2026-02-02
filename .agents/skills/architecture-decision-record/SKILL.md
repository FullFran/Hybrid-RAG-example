---
name: architecture-decision-record
description: Help the team document and maintain Architecture Decision Records (ADRs).
---

# Architecture Decision Record (ADR) Skill

Esta skill permite al agente ayudar al equipo a documentar decisiones técnicas importantes para mantener un rastro histórico de la arquitectura.

## Cuándo usar
- Al elegir una nueva base de datos o framework.
- Al cambiar un patrón de diseño global (ej: pasar de REST a GraphQL).
- Al establecer convenciones de código obligatorias.

## Estructura del ADR
Los archivos deben guardarse en `docs/adr/NNNN-nombre-descriptivo.md` con:
1. **Título**: Breve y claro.
2. **Estatus**: Propuesto, Aceptado, Superado o Rechazado.
3. **Contexto**: ¿Cuál es el problema y qué opciones hay?
4. **Decisión**: ¿Qué se ha elegido y por qué?
5. **Consecuencias**: ¿Qué ganamos y qué perdemos con esto?

## Proceso
1. Ayuda al usuario a articular la decisión.
2. Genera el markdown siguiendo la plantilla.
3. Asegúrate de que el número sea correlativo al último ADR en `docs/adr/`.
4. Ejecuta `npm run sync` si la decisión afecta al framework de agentes.
