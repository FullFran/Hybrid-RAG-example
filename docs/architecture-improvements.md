# Architectural Improvement Plan (Alan's Philosophy)

This document outlines the architectural "technical debt" and improvement roadmap for the Hybrid RAG Agent, based on **Software Architecture principles** (Separation of Concerns, Boundary Management, and Stability).

> "Architecture is the faculty of facilitating change." — Alan

## 1. Identified Architectural "Sins"

### A. Boundary Leakage (Domain Contamination)
In `src/core/schemas/document.py`, the domain entity is coupled with infrastructure details:
- **The Issue**: `id: Optional[str] = Field(None, alias="_id")`. 
- **The Sin**: The Domain layer knows about MongoDB's internal naming convention (`_id`).
- **The Consequence**: If we switch to PostgreSQL or another DB, the Domain must be modified, violating the **Principle of Stability**.

### B. Framework Coupling in the Core
The core entities use `pydantic`.
- **The Issue**: `BaseModel` and `Field` are imported directly into the Domain.
- **The Sin**: The most stable layer of the system (Core) depends on an external library (Infrastructure).
- **The Consequence**: A breaking change in Pydantic or a decision to switch validation libraries would require a full refactor of the business logic.

### C. Delivery Format Leakage
The `AgentService` defines the `SEARCH_TOOL` using the specific JSON schema required by OpenAI.
- **The Issue**: The logic of **how** a tool is described for an LLM is mixed with the **orchestration** of the tool.
- **The Sin**: Violated the **Independence of AI Providers**.
- **The Consequence**: Adding support for Anthropic or a local model with a different tool-calling format would require modifying the Application layer.

### D. Missing DTO Layer
The system passes Domain entities (`Chunk`, `SearchHit`) directly to the Endpoints (CLI).
- **The Issue**: No separation between internal data representation and external API/CLI contracts.
- **The Sin**: Endpoints are tightly coupled to the internal data structure.
- **The Consequence**: Changing the database schema (e.g., adding a field to `Chunk`) might accidentally break the CLI output format.

---

## 2. Strategic Roadmap (The Plan)

### Phase 1: Clean the Core (High Priority)
- [ ] **Decouple Identity**: Remove `alias="_id"` from domain schemas. Use a Mapper in `src/infrastructure/database/` to handle the conversion.
- [ ] **Pure Domain**: Investigate moving towards pure Python dataclasses for the Core, using Pydantic only at the boundaries (Infrastructure/Endpoints) for validation.

### Phase 2: Tool Abstraction (Stability)
- [ ] **Define a Tool Port**: Create a domain-agnostic `ITool` interface.
- [ ] **Move Tool Schemas**: Move the OpenAI-specific JSON definition to `src/infrastructure/llm/`. The `AgentService` should only request a tool by its intent, not its format.

### Phase 3: Enforce DTOs (Boundary Management)
- [ ] **Create Response DTOs**: Define specific objects in `src/core/dtos/` for the data that actually goes to the user.
- [ ] **Implement Mappers**: Ensure services return DTOs to endpoints, protecting the Domain entities from external exposure.

### Phase 4: Configuration Granularity
- [ ] **Interface-based Config**: Instead of passing the whole `Settings` object, inject specific configurations into adapters. An LLM adapter should only receive `LLMSettings`.

---

## 3. Architectural Vision

The goal is to move from a "Clean-ish" architecture to a **Strict Hexagonal/Clean Architecture** where:
1. **The Core is a Fortress**: No dependencies, no knowledge of DBs, no knowledge of LLM formats.
2. **Infrastructure is a Detail**: Switching from Mongo to Postgres or from OpenAI to Claude should be a matter of adding a new adapter, not rewriting services.
3. **Delivery is Decoupled**: The CLI is just one way to talk to the system. The system shouldn't care if it's a terminal, a Slack bot, or a REST API.

---

*This plan is a living document. Every refactor should move us closer to these principles.*
