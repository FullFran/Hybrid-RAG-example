# Target Architecture: Clean RAG Architecture

This document defines the **Clean Architecture** and decoupled design for the RAG system. The goal is to allow interchangeability of providers (Database, LLM, Embeddings, Parsing) and organize code following principles of single responsibility and separation of concerns.

## 1. Design Principles

- **Independence of Frameworks**: Business logic should not depend on external libraries.
- **Testability**: Business rules can be tested without the database or LLM.
- **Independence of UI**: The interface (CLI or API) can change without affecting the core.
- **Independence of Database**: You can switch from MongoDB to Supabase without touching the RAG logic.
- **Independence of Ingestion**: Parsing and chunking strategies can be swapped via interfaces.

## 2. Layer Structure and Interfaces

The architecture is organized into the following contexts:

### A. Schemas (Domain Layer)

Defines base data models used throughout the system. They are pure and unaware of the database.

- `Document`: The original source document.
- `Chunk`: A document fragment with its content and metadata.
- `SearchMatch`: Represents a retrieved fragment with its relevance score.

### B. DTOs (Data Transfer Objects)

Objects for moving data between layers, especially outwards from _Services_.

- `QueryRequest`: User query data.
- `QueryResponse`: Formatted response with sources and metadata.
- `IngestRequest`: File upload/processing data.

### C. Services (Application Layer)

Contains business logic orchestration. Uses interfaces (Abstractions) to interact with external components.

- `AgentService`: **Main entry point**. ReAct agent that decides whether to search RAG or respond directly. See [implementation detail](agent_service_detail.md).
- `RAGService`: Orchestrates hybrid search and generation with context. Uses `ContextBuilder` for context assembly. See [implementation detail](rag_service_detail.md).
- `IngestService`: Orchestrates parsing, chunking, embedding, and storage via interfaces.
- `ContextBuilder`: Assembles context from search results with source attribution.

### D. Core Interfaces (Abstraction Layer)

Abstract contracts that define capabilities without implementation details:

| Interface        | Purpose                                      | Implementations                      |
|------------------|----------------------------------------------|--------------------------------------|
| `IRepository`    | Vector storage and hybrid search             | `MongoRepository`, `SupabaseRepository` |
| `ILLMProvider`   | Text generation                              | `OpenAILLMProvider`                  |
| `IEmbedder`      | Vector embedding generation                  | `OpenAIEmbedder`                     |
| `IParser`        | Document parsing (PDF, DOCX, etc. → text)    | `DoclingParser`                      |
| `IChunker`       | Text segmentation into semantic chunks       | `DoclingChunker`                     |
| `IAdminRepository` | Administrative operations (clean, stats)   | `MongoRepository`, `SupabaseRepository` |

### E. Endpoints (Interface Adapter Layer)

System entry points.

- `CLI`: Current implementation using Rich.
- `API`: (Future) FastAPI/Flask endpoints.

### F. Infrastructure (External Layer)

Concrete implementations of provider interfaces.

- **Database**: `MongoRepository`, `SupabaseRepository`
- **LLM**: `OpenAILLMProvider`
- **Embedder**: `OpenAIEmbedder`
- **Ingestion**: `DoclingParser`, `DoclingChunker`

---

## 3. Architecture Diagrams

### C4 Level 2: Container Diagram

Shows the main containers (applications/services) and how they interact.

```mermaid
flowchart TB
    User((User))

    subgraph Endpoints["Endpoints Layer"]
        CLI["CLI (Rich)"]
    end

    subgraph Services["Application Layer"]
        Agent["AgentService"]
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

### C4 Level 3: Component Diagram - IngestService

Detailed view of the Ingestion Service and its dependencies.

```mermaid
flowchart TB
    subgraph IngestService["IngestService"]
        direction TB
        ingest["ingest_documents()"]
        process["_process_file()"]
        save["_save_chunks()"]
        ingest --> process
        process --> save
    end

    subgraph Interfaces["Abstractions"]
        direction LR
        IParser([IParser])
        IChunker([IChunker])
        IEmb([IEmbedder])
        IRepo([IRepository])
    end

    subgraph Implementations["Infrastructure"]
        direction LR
        DocParser["DoclingParser"]
        DocChunker["DoclingChunker"]
        OAIEmb["OpenAIEmbedder"]
        Supa[(SupabaseRepository)]
    end

    process -.->|parse| IParser
    process -.->|chunk| IChunker
    save -.->|embed| IEmb
    save -.->|store| IRepo

    IParser -.-> DocParser
    IChunker -.-> DocChunker
    IEmb -.-> OAIEmb
    IRepo -.-> Supa

    %% Styling
    style IngestService fill:#1a1a2e,stroke:#16213e,stroke-width:2px,color:#eaeaea
    style Interfaces fill:#0f3460,stroke:#1a1a2e,stroke-width:2px,color:#eaeaea
    style Implementations fill:#00b894,stroke:#55efc4,color:#2d3436
    style ingest fill:#e94560,stroke:#1a1a2e,color:#fff
    style process fill:#533483,stroke:#1a1a2e,color:#fff
    style save fill:#533483,stroke:#1a1a2e,color:#fff
```

### C4 Level 3: Component Diagram - RAGService

Detailed view of the RAG Service query flow.

```mermaid
flowchart TB
    subgraph RAGService["RAGService"]
        direction TB
        answer["answer()"]
        search["_hybrid_search()"]
        generate["_generate_response()"]
        answer --> search
        search --> generate
    end

    subgraph Helpers["Support Services"]
        Context["ContextBuilder"]
    end

    subgraph Interfaces["Abstractions"]
        direction LR
        IRepo([IRepository])
        ILLM([ILLMProvider])
    end

    subgraph Implementations["Infrastructure"]
        direction LR
        Supa[(SupabaseRepository)]
        OAILLM["OpenAILLMProvider"]
    end

    search -.->|hybrid_search| IRepo
    generate -.->|generate| ILLM
    generate --> Context

    IRepo -.-> Supa
    ILLM -.-> OAILLM

    %% Styling
    style RAGService fill:#1a1a2e,stroke:#16213e,stroke-width:2px,color:#eaeaea
    style Helpers fill:#fdcb6e,stroke:#f39c12,color:#2d3436
    style Interfaces fill:#0f3460,stroke:#1a1a2e,stroke-width:2px,color:#eaeaea
    style Implementations fill:#00b894,stroke:#55efc4,color:#2d3436
    style answer fill:#e94560,stroke:#1a1a2e,color:#fff
    style search fill:#533483,stroke:#1a1a2e,color:#fff
    style generate fill:#533483,stroke:#1a1a2e,color:#fff
```

---

## 4. Dependency Inversion (Code Example)

To achieve decoupling, services do not import concrete implementations. Instead, they use interfaces:

```python
# core/interfaces/repository.py
class IRepository(ABC):
    @abstractmethod
    async def hybrid_search(self, query: str, vector: list[float], limit: int) -> list[SearchMatch]:
        pass

# core/interfaces/parser.py
class IParser(ABC):
    @abstractmethod
    def parse(self, file_path: Path) -> str:
        """Parse a document file and return its text content."""
        pass

# core/interfaces/chunker.py
class IChunker(ABC):
    @abstractmethod
    def chunk(self, text: str, metadata: dict) -> list[Chunk]:
        """Split text into semantic chunks."""
        pass

# services/ingest_service.py
class IngestService:
    def __init__(
        self,
        repository: IRepository,
        embedder: IEmbedder,
        parser: IParser,    # Interface, not DoclingParser
        chunker: IChunker,  # Interface, not DoclingChunker
    ):
        self.repository = repository
        self.embedder = embedder
        self.parser = parser
        self.chunker = chunker
```

## 5. Folder Organization

```text
src/
├── core/
│   ├── schemas/           # Document, Chunk, SearchMatch
│   ├── dtos/              # Input/Output Data Transfer Objects
│   ├── interfaces/        # Abstract contracts
│   │   ├── repository.py      # IRepository
│   │   ├── admin_repository.py # IAdminRepository
│   │   ├── llm.py             # ILLMProvider
│   │   ├── embedder.py        # IEmbedder
│   │   ├── parser.py          # IParser (NEW)
│   │   └── chunker.py         # IChunker (NEW)
│   └── prompts.py         # System prompts
├── services/              # Business logic orchestration
│   ├── agent_service.py       # ReAct Agent
│   ├── rag_service.py         # Hybrid Search + Generation
│   ├── ingest_service.py      # Document Processing
│   └── context_builder.py     # Context Assembly
├── infrastructure/        # Provider implementations
│   ├── database/
│   │   ├── mongo_repository.py
│   │   └── supabase_repository.py
│   ├── llm/
│   │   └── openai_provider.py
│   ├── embeddings/
│   │   └── openai_embedder.py
│   └── ingestion/         # NEW: Parsing implementations
│       ├── docling_parser.py
│       └── docling_chunker.py
├── endpoints/             # User interfaces
│   ├── cli/
│   │   ├── main.py
│   │   └── ingest.py
│   └── api/               # (Future) FastAPI
└── bootstrap.py           # Dependency injection setup
```

## 6. Sequence Diagram: Query Flow

```mermaid
sequenceDiagram
    autonumber
    participant U as User
    participant CLI as CLI
    participant Agent as AgentService
    participant RAG as RAGService
    participant Repo as IRepository
    participant LLM as ILLMProvider
    participant CB as ContextBuilder

    U->>CLI: Enter query
    CLI->>Agent: process_query(query)
    activate Agent

    Agent->>Agent: Classify intent
    alt Requires RAG
        Agent->>RAG: answer(query)
        activate RAG
        RAG->>Repo: hybrid_search(query, vector)
        Repo-->>RAG: SearchMatch[]
        RAG->>CB: build_context(matches)
        CB-->>RAG: formatted_context
        RAG->>LLM: generate(context, query)
        LLM-->>RAG: response
        deactivate RAG
        RAG-->>Agent: answer
    else Direct response
        Agent->>LLM: generate(query)
        LLM-->>Agent: response
    end

    Agent-->>CLI: formatted_response
    deactivate Agent
    CLI-->>U: Display answer
```

## 7. Sequence Diagram: Ingestion Flow

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
    CLI->>Svc: ingest_documents(path)
    activate Svc

    loop For each file
        Svc->>Parser: parse(file_path)
        Parser-->>Svc: raw_text
        Svc->>Chunker: chunk(text, metadata)
        Chunker-->>Svc: Chunk[]
        
        loop For each chunk batch
            Svc->>Emb: embed(texts)
            Emb-->>Svc: vectors[]
            Svc->>Repo: upsert_chunks(chunks)
            Repo-->>Svc: success
        end
    end

    deactivate Svc
    Svc-->>CLI: Ingestion complete
    CLI-->>U: Summary report
```
