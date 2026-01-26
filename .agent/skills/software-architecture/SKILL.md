---
name: software-architecture
description: Guide architecture decisions, document tradeoffs, and align designs with system goals and constraints.
license: MIT
metadata:
  author: OpenCode
  version: "1.0"
---

# Software Architecture

## When to use
- Making system-level decisions or introducing new subsystems.
- Evaluating tradeoffs (performance, maintainability, scalability, cost).
- Updating or creating architecture documentation in `docs/`.

## Core guidance
- Start from business goals and quality attributes.
- Capture tradeoffs explicitly and keep decisions reversible when possible.
- Prefer interfaces and contracts to isolate volatility.
- Keep architecture diagrams and docs concise and up to date.

## Do
- Document major decisions in `docs/` with rationale and constraints.
- Use explicit interfaces in `src/core/interfaces/` to decouple subsystems.
- Keep new subsystems aligned with Clean Architecture layers.

## Don't
- Add cross-layer dependencies to "move faster".
- Introduce new providers without contracts or tests.
- Let docs drift from actual wiring in `src/bootstrap.py`.

## Anti-patterns seen
- Architecture decisions living only in code comments or PRs.
- Skipping tradeoff discussion when introducing new infra.
- Layer boundaries eroding due to quick fixes.

## Repo anchors
- `docs/architecture.md`
- `docs/framework-design.md` (if present)
- `src/bootstrap.py`

## References
- https://the-amazing-gentleman-programming-book.vercel.app/es/book/Chapter18_Software-Architecture
