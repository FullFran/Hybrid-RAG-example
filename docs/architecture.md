# Target Architecture: Clean RAG with ReAct Agent

This document defines the **Clean Architecture** for the RAG system with a real ReAct agent.

## 1. Design Principles

- **Independence of Frameworks**: Business logic does not depend on external libraries.
- **Testability**: Business rules testable without database or LLM.
- **Independence of UI**: CLI can be replaced with API without affecting core.
- **Independence of Database**: Switch MongoDB to Supabase without touching RAG logic.
- **Independence of Ingestion**: Parsing and chunking strategies swappable via interfaces.

## 2. Layer Structure

### A. Domain Layer (`src/core/`)

Pure data models and abstract contracts:

- **Schemas**: `Document`, `Chunk`, `SearchHit`
- **Interfaces**: `IRepository`, `ILLMProvider`, `IEmbedder`, `IParser`, `IChunker`
- **Exceptions**: Domain-specific errors

### B. Application Layer (`src/services/`)

Business logic orchestration:

| Service | Responsibility |
|---------|----------------|
| `AgentService` | ReAct agent with iterative tool use |
| `RAGService` | Hybrid search and generation |
| `IngestService` | Document processing pipeline |
| `ContextBuilder` | Context assembly with diversity limits |

### C. Infrastructure Layer (`src/infrastructure/`)

Concrete implementations:

| Category | Implementations |
|----------|-----------------|
| Database | `MongoRepository`, `SupabaseRepository` |
| LLM | `OpenAILLMProvider` |
| Embeddings | `OpenAIEmbedder` |
| Ingestion | `DoclingParser`, `DoclingChunker` |

### D. Endpoints Layer (`src/endpoints/`)

User interfaces:

- **CLI**: Rich-based terminal interface
- **API**: (Future) FastAPI endpoints

## 3. Architecture Diagram (C4 Level 2)

```mermaid
flowchart TB
    User((User))

    subgraph Endpoints["Endpoints Layer"]
        CLI["CLI (Rich)"]
    end

    subgraph Services["Application Layer"]
        Agent["AgentService<br/>(ReAct Loop)"]
        RAG["RAGService"]
        Ingest["IngestService"]
        Context["ContextBuilder"]
    end

    subgraph Core["Domain Layer - Interfaces"]
        direction LR
        IRepo([IRepository])
        ILLM([ILLMProvider])
        IEmb([IEmbedder])
        IParser([IParser])
        IChunker([IChunker])
    end

    subgraph Infra["Infrastructure Layer"]
        direction TB
        subgraph DBs["Database Providers"]
            Mongo[(MongoRepository)]
            Supa[(SupabaseRepository)]
        end
        subgraph AI["AI Providers"]
            OAILLM["OpenAILLMProvider"]
            OAIEmb["OpenAIEmbedder"]
        end
        subgraph Parsing["Ingestion Providers"]
            DocParser["DoclingParser"]
            DocChunker["DoclingChunker"]
        end
    end

    User --> CLI
    CLI --> Agent
    Agent --> RAG
    RAG --> Context
    CLI --> Ingest

    RAG -.-> IRepo
    RAG -.-> ILLM
    RAG -.-> IEmb
    Agent -.-> ILLM
    Ingest -.-> IRepo
    Ingest -.-> IEmb
    Ingest -.-> IParser
    Ingest -.-> IChunker

    IRepo -.-> Mongo
    IRepo -.-> Supa
    ILLM -.-> OAILLM
    IEmb -.-> OAIEmb
    IParser -.-> DocParser
    IChunker -.-> DocChunker

    %% Layer styling
    style Endpoints fill:#2d3436,stroke:#636e72,color:#dfe6e9
    style Services fill:#0984e3,stroke:#74b9ff,color:#fff
    style Core fill:#6c5ce7,stroke:#a29bfe,color:#fff
    style Infra fill:#00b894,stroke:#55efc4,color:#fff
    style DBs fill:#00cec9,stroke:#81ecec,color:#2d3436
    style AI fill:#e17055,stroke:#fab1a0,color:#fff
    style Parsing fill:#fdcb6e,stroke:#f39c12,color:#2d3436
```

## 4. Query Flow (ReAct Agent)

```mermaid
sequenceDiagram
    autonumber
    participant U as User
    participant CLI as CLI
    participant Agent as AgentService
    participant RAG as RAGService
    participant LLM as ILLMProvider

    U->>CLI: Enter query
    CLI->>Agent: chat(query)
    activate Agent

    loop ReAct Loop (max 3 steps)
        Agent->>LLM: generate_with_tools(scratchpad)
        
        alt Tool call: search_documents
            Agent->>RAG: search(query)
            RAG-->>Agent: SearchHit[]
            Note over Agent: Append observation to scratchpad
        else Response with FINAL:
            Agent->>Agent: Extract final answer
            Agent-->>CLI: AgentResult
        end
    end

    deactivate Agent
    CLI-->>U: Display answer + sources
```

## 5. Ingestion Flow

```mermaid
sequenceDiagram
    autonumber
    participant U as User
    participant CLI as CLI/Ingest
    participant Svc as IngestService
    participant Parser as IParser
    participant Chunker as IChunker
    participant Emb as IEmbedder
    participant Repo as IRepository

    U->>CLI: Run ingestion
    CLI->>Svc: ingest_file(path)
    activate Svc

    Svc->>Parser: parse(file_path)
    Parser-->>Svc: (content, raw_doc)
    
    Svc->>Chunker: chunk_document(content, raw_doc)
    Chunker-->>Svc: RawChunk[]

    Svc->>Emb: get_embeddings(texts)
    Emb-->>Svc: vectors[]

    Svc->>Repo: save_document(doc)
    Repo-->>Svc: doc_id

    Svc->>Repo: save_chunks(chunks)
    Repo-->>Svc: success

    deactivate Svc
    Svc-->>CLI: Ingestion complete
```

## 6. Folder Organization

```
src/
├── core/
│   ├── schemas/           # Document, Chunk, SearchHit
│   ├── dtos/              # Data Transfer Objects
│   ├── interfaces/        # Abstract contracts
│   │   ├── repository.py
│   │   ├── llm.py
│   │   ├── embedder.py
│   │   ├── parser.py
│   │   └── chunker.py
│   ├── exceptions.py      # Domain errors
│   └── prompts.py         # System prompts
├── services/
│   ├── agent_service.py   # ReAct Agent
│   ├── rag_service.py     # Hybrid Search + Generation
│   ├── ingest_service.py  # Document Processing
│   └── context_builder.py # Context Assembly
├── infrastructure/
│   ├── database/
│   │   ├── mongo_repository.py
│   │   └── supabase_repository.py
│   ├── llm/
│   │   └── openai_provider.py
│   ├── embeddings/
│   │   └── openai_embedder.py
│   └── ingestion/
│       ├── docling_parser.py
│       └── docling_chunker.py
├── endpoints/
│   └── cli/
│       ├── main.py
│       └── ingest.py
├── bootstrap.py           # Dependency injection
└── settings.py            # Configuration
```

## 7. Related Documentation

| Document | Description |
|----------|-------------|
| [Agent Service](agent-service.md) | ReAct loop implementation details |
| [RAG Service](rag-service.md) | Hybrid search and generation |
| [Context](context.md) | System context (C4 Level 1) |
