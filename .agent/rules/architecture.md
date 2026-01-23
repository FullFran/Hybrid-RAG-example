---
name: architecture
description: Rules for Clean RAG Architecture.
activation_mode: always_on
---

# Architecture Rules

All code MUST follow the Clean Architecture principles established for this RAG system.

## 🏛️ Layer Responsibilities

1. **Domain Layer (`src/core/`)**:

   - `schemas/`: Pure data models (Pydantic). No database logic.
   - `interfaces/`: Abstract base classes (ABC) defining contracts for external services.
   - `dtos/`: Data Transfer Objects for cross-layer communication.

2. **Application Layer (`src/services/`)**:

   - Contains business logic (e.g., `RAGService`, `IngestionService`).
   - Orchestrates flows using interfaces, NOT concrete implementations.
   - Responsible for: Query reformulation, RRF (Reciprocal Rank Fusion), and response synthesis.

3. **Infrastructure Layer (`src/infrastructure/`)**:

   - Concrete implementations of core interfaces (e.g., `MongoRepository`, `OpenAIProvider`).
   - External library dependencies (Motor, OpenAI, etc.) belong HERE.

4. **Endpoints Layer (`src/endpoints/`)**:
   - Entry points to the system (CLI, API).
   - CLI uses `Rich` for formatting and streaming.

## 🚀 Key Rules

- **Infrastructure Independence**: Always code against interfaces in `src/core/interfaces/`.
- **Dependency Injection**: Services must receive interface implementations via `__init__`.
- **Clean Registry**: Do NOT add ad-hoc scripts to the root. use `scripts/` or `src/endpoints/`.
- **Legacy Awareness**: Keep a clear distinction between MongoDB implementation and any legacy or alternative (Supabase) code.
