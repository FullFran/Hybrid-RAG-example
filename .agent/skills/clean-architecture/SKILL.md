---
name: clean-architecture
description: Apply Clean Architecture boundaries, dependency rules, and layer responsibilities when designing or changing code in this repository.
license: MIT
metadata:
  author: OpenCode
  version: "1.0"
---

# Clean Architecture

## When to use
- Designing new modules or services in `src/core/`, `src/services/`, or `src/infrastructure/`.
- Refactoring to reduce coupling between layers.
- Reviewing changes that might violate dependency direction.

## Core guidance
- Domain layer (`src/core/`) must be independent of infrastructure.
- Services orchestrate using interfaces from `src/core/interfaces/`.
- Dependency injection happens in `src/bootstrap.py`.
- Keep provider-specific code in `src/infrastructure/` only.
- Prefer small, single-purpose classes and functions.

## Do
- Add new provider logic under `src/infrastructure/` and expose it via an interface.
- Keep orchestration in `src/services/` and call interfaces only.
- Place shared data models in `src/core/schemas/` or DTOs in `src/core/dtos/`.

## Don't
- Import infrastructure classes in `src/core/` or `src/services/`.
- Add direct SDK calls (OpenAI/Mongo/Supabase) outside `src/infrastructure/`.
- Bypass `src/bootstrap.py` for wiring dependencies.

## Anti-patterns seen
- Services instantiating concrete repositories or providers.
- Endpoint layer containing business rules or query reformulation.
- Infra logic leaking into core schemas or interfaces.

## Repo anchors
- `src/core/interfaces/`
- `src/services/`
- `src/infrastructure/`
- `src/bootstrap.py`

## References
- https://the-amazing-gentleman-programming-book.vercel.app/es/book/Chapter07_Clean_Architecture
