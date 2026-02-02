---
description: Initialize the RAG project environment
---

1. Create Environment File

```bash
cp .env.example .env
```

2. Install Dependencies

```bash
uv sync
```

3. Initialize Ingestion (if data is provided)

```bash
uv run python -m src.ingestion.ingest -d ./documents
```

4. Start the Chat CLI

```bash
uv run python -m src.endpoints.cli.main
```
