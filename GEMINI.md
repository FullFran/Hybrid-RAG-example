# Hybrid RAG Agent - Developer Dashboard

This repository contains a modular Hybrid RAG (Retrieval-Augmented Generation) framework supporting both **MongoDB Atlas** and **Supabase**.

## 🚀 Quick Start

| Area               | Description                    | Entry Point                                                                                                |
| ------------------ | ------------------------------ | ---------------------------------------------------------------------------------------------------------- |
| **Core logic**     | Service and RAG coordination   | [src/services/](file:///home/franblakia/blakia/blakiaxhagalink/Hybrid-RAG-Agent/src/services/)             |
| **Ingestion**      | Document parsing and embedding | [src/ingestion/](file:///home/franblakia/blakia/blakiaxhagalink/Hybrid-RAG-Agent/src/ingestion/)           |
| **Infrastructure** | Database and LLM adapters      | [src/infrastructure/](file:///home/franblakia/blakia/blakiaxhagalink/Hybrid-RAG-Agent/src/infrastructure/) |
| **Examples**       | Usage patterns and notebooks   | [examples/](file:///home/franblakia/blakia/blakiaxhagalink/Hybrid-RAG-Agent/examples/)                     |

## 🛠️ Key Commands

- **Initialize Environment**: `uv venv && uv sync` (using `uv` for speed).
- **Setup Agents**: `./scripts/setup-agents.sh`
- **Manual Ingestion**: `python -m src.ingestion.ingest --file data/sample.pdf`
- **Debug DB**: `python debug_db.py`

## ⚙️ Configuration Recap

The project uses `.env` for configuration. Key variables:

- `DB_TYPE`: `mongo` (default) or `supabase`.
- `LLM_MODEL`: e.g., `gpt-4o` or compatible.
- `EMBEDDING_MODEL`: e.g., `text-embedding-3-small`.

> [!TIP]
> Check [src/settings.py](file:///home/franblakia/blakia/blakiaxhagalink/Hybrid-RAG-Agent/src/settings.py) for the full list of available settings.

## 🏗️ Architecture Overview

The system follows a standard hexagonal/service-based architecture:

1. **Ingestion Layer**: `Docling` parsers -> Chunks -> `OpenAI/Compatible` Embeddings.
2. **Storage Layer**: `pgvector` (Supabase) or `Atlas Vector Search` (MongoDB).
3. **Service Layer**: Coordinate search and LLM generation.
4. **Endpoint Layer**: Python/CLI access points.
