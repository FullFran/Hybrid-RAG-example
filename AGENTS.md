# Agent Guide for Hybrid-RAG-Agent
# Purpose: concise, repo-specific rules for agentic coding tools.

## Fast Commands (UV)
- Setup venv + deps: `uv venv && uv sync`
- Install editable (if needed): `uv pip install -e .`
- Run CLI (chat): `uv run python -m src.endpoints.cli.main`
- Run ingestion: `uv run python -m src.endpoints.cli.ingest -d ./documents`
- Lint (repo): `uv run ruff check .`
- Lint (single file): `uv run ruff check src/services/rag_service.py`
- Format (repo): `uv run black .`
- Format (single file): `uv run black src/services/agent_service.py`
- Tests (all): `uv run pytest -v`
- Tests (single file): `uv run pytest tests/test_rag_service.py`
- Tests (single test): `uv run pytest tests/test_rag_service.py::test_text_only_search`

## Build Notes
- No dedicated build step is defined; package metadata lives in `pyproject.toml`.
- If you need a wheel/sdist, use `uv build` (only when explicitly requested).

## Runtime Entry Points
- CLI main: `src/endpoints/cli/main.py`
- CLI ingestion: `src/endpoints/cli/ingest.py`
- App wiring: `src/bootstrap.py`

## Repo Architecture (Clean RAG)
- Domain layer: `src/core/` (Pydantic schemas + interfaces, no infra deps).
- Application layer: `src/services/` (business logic, orchestration).
- Infrastructure: `src/infrastructure/` (Mongo/Supabase/OpenAI/Docling).
- Endpoints: `src/endpoints/` (CLI entry points via Rich).

## Configuration
- Environment lives in `.env` (see `.env.example`).
- Settings should flow through `src/settings.py` (Pydantic Settings).
- Never hardcode provider keys or connection strings.

## Architecture Rules (from `.agent/rules/architecture.md`)
- Code against interfaces in `src/core/interfaces/`.
- Services receive dependencies via constructor injection.
- Infrastructure code stays in `src/infrastructure/` only.
- No ad-hoc scripts in repo root; use `scripts/`.

## Code Style (Python)
- Python 3.10+ only; keep code type-safe and explicit.
- Type hints are required for all functions and methods.
- Prefer Pydantic models for data structures and DTOs.
- Imports order: standard library, third-party, local; blank line between groups.
- Prefer absolute imports like `from src.core...`.
- Naming:
  - Classes: `PascalCase`.
  - Functions/vars: `snake_case`.
  - Constants: `UPPER_SNAKE_CASE`.
  - Modules/files: `snake_case`.
- Keep functions small and single-purpose; favor clarity over cleverness.

## Formatting + Linting Expectations
- Use Black for formatting and Ruff for linting.
- Keep lines reasonably short; prefer readability over dense expressions.
- Do not reformat unrelated files.

## Async + I/O Rules
- All I/O must be async (Mongo, embeddings, LLM calls, file ops).
- Always `await` async calls; avoid sync wrappers.
- Use `asyncio` for concurrency when needed.
- Clean up resources (`close()` or context managers) where appropriate.

## Data Modeling Conventions
- Core schemas live in `src/core/schemas/` and are Pydantic models.
- Use DTOs in `src/core/dtos/` for cross-layer communication.
- When persisting Pydantic models, use `.model_dump(exclude={"id"}, by_alias=True)`.
- Avoid mutating SearchHit objects in RRF; create new instances.

## Error Handling + Logging
- Catch specific exceptions; avoid bare `except`.
- Log with context: `logger.exception(...)` for unexpected failures.
- Raise clear, typed errors (ValueError, ConnectionFailure, etc.).
- Mongo aggregation errors should follow patterns in `.claude/reference/mongodb-patterns.md`.
- Prefer returning safe, user-facing messages when no hits are found.

## Testing
- Tests live in `tests/` mirroring `src/` structure.
- Use pytest + pytest-asyncio for async tests.
- Mark async tests with `@pytest.mark.asyncio`.
- Favor mocks in `tests/conftest.py` for external services.
- Keep tests deterministic; do not hit real external APIs by default.

## Documentation Rules (from `.agent/rules/`)
- New technical docs go in `docs/` only.
- Use clear Markdown headings and lists; keep docs under ~500 lines.
- Use backticks for file names, directories, and commands.
- Avoid duplicating global rules in nested `AGENTS.md` files.

## Skill System (Agentic Rules)
- Prefer modular skills in `.agent/skills/` for new capabilities.
- If a workflow exists in `.agent/workflows/`, use it.
- Auto-invoke skills when triggers match:
  - New skills: `skill-creator`.
  - New workflows: `workflow-creator`.
  - Skill metadata sync: run `scripts/sync-skills.sh`.
  - Technical docs: `docs-standard`.
  - RAG DB changes: `supabase` or `mongodb` skills.

## Core Mandates (from prior AGENTS.md)
- Modularity first: favor skills in `.agent/skills/` over ad-hoc scripts.
- Context hygiene: follow `.agent/rules/docs-culture.md` for documentation standards.
- Proactive skill loading: check available skills and load when relevant.

## Essential Skills (quick reference)
- `docs-standard`: technical documentation standard.
- `skill-creator`: bootstrap new skills.
- `mermaid-diagrams`: architecture diagrams.
- `supabase` / `mongodb`: DB-specific RAG logic.
- `docling`: ingestion and parsing workflows.

## Service Orchestration Conventions
- Services orchestrate flows using interfaces, not concrete implementations.
- Injection happens in `src/bootstrap.py`; do not bypass it.
- Keep provider-specific logic out of `src/services/`.

## Repository Conventions Observed
- Logging via `logging.getLogger(__name__)`.
- Pydantic models use `.model_dump(...)` with `by_alias=True` when persisting.
- RRF logic should avoid mutating original hits.
- CLI uses Rich; keep UX clean and streaming-friendly.

## RAG Behavior Guidelines
- Query reformulation lives in services, not endpoints.
- RRF must create new `SearchHit` instances (no in-place mutation).
- Preserve `semantic_score` and `text_score` on fused results.
- Context building should respect max lengths to avoid prompt bloat.

## Secrets and Safety
- Never commit `.env` or credential files.
- Prefer `.env.example` for documenting required variables.
- Keep external API calls behind interfaces for testability.

## Behavior Triggers (Legacy Guide)
- RAG ingestion or retrieval changes: load `docling` + DB skill.
- Repetitive actions: propose a workflow in `.agent/workflows/`.

## Interaction Style for Agents
- Be concise and direct; run safe commands proactively.
- Validate changes with appropriate tests or checks.
- Keep context hygiene; avoid unnecessary docstrings.

## External Rules Files
- Cursor rules: none found in `.cursor/rules/` or `.cursorrules`.
- Copilot rules: none found in `.github/copilot-instructions.md`.
