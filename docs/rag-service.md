# RAG Service - Hybrid Search and Generation

The `RAGService` orchestrates **Retrieval-Augmented Generation** with hybrid search combining semantic and keyword matching.

## 1. Responsibility

The RAG service handles:

- **Hybrid search**: Semantic + text search with RRF fusion
- **Context building**: Assembles retrieved chunks with diversity limits
- **Response generation**: Streams LLM responses with context

## 2. Sequence Diagram (Hybrid Search Flow)

```mermaid
sequenceDiagram
    autonumber
    participant C as Caller
    participant RS as RAGService
    participant EMB as IEmbedder
    participant DB as IRepository
    participant CB as ContextBuilder
    participant LLM as ILLMProvider

    C->>RS: answer(query, system_prompt)
    activate RS

    Note over RS: search(query, type=HYBRID)

    par Parallel Search
        RS->>EMB: get_embedding(query)
        EMB-->>RS: vector[]
        RS->>DB: semantic_search(vector, limit*2)
        DB-->>RS: semantic_hits[]
    and
        RS->>DB: text_search(query, limit*2)
        DB-->>RS: text_hits[]
    end

    Note over RS: _reciprocal_rank_fusion()
    RS->>RS: Merge with RRF (k=60)

    RS->>CB: build(merged_hits)
    CB-->>RS: ContextResult

    RS->>LLM: generate_response(system_prompt, context + query)
    LLM-->>C: AsyncIterator[response]
    deactivate RS
```

## 3. Component Diagram

```mermaid
flowchart TB
    subgraph Service["RAGService"]
        direction TB
        answer["answer()"]
        search["search()"]
        rrf["_reciprocal_rank_fusion()"]

        answer --> search
        search --> rrf
    end

    subgraph Helpers["Support Services"]
        CB["ContextBuilder"]
    end

    subgraph Interfaces["Abstractions"]
        direction LR
        IEmb([IEmbedder])
        IRepo[(IRepository)]
        ILLM([ILLMProvider])
    end

    %% Dependencies
    search -.->|"get_embedding()"| IEmb
    search -.->|"semantic_search()"| IRepo
    search -.->|"text_search()"| IRepo
    answer -.->|"build()"| CB
    answer -.->|"generate_response()"| ILLM

    %% Styling
    style Service fill:#1a1a2e,stroke:#16213e,stroke-width:2px,color:#eaeaea
    style Helpers fill:#fdcb6e,stroke:#f39c12,color:#2d3436
    style Interfaces fill:#0f3460,stroke:#1a1a2e,stroke-width:2px,color:#eaeaea
    style answer fill:#e94560,stroke:#1a1a2e,color:#fff
    style search fill:#e94560,stroke:#1a1a2e,color:#fff
    style rrf fill:#533483,stroke:#1a1a2e,color:#fff
```

## 4. Search Types

| Mode | Description |
|------|-------------|
| `HYBRID` | Semantic + text search merged with RRF (default) |
| `SEMANTIC` | Vector similarity search only |
| `TEXT` | Full-text keyword search only |

## 5. Reciprocal Rank Fusion (RRF)

Combines results from multiple search channels:

```
score(doc) = SUM( 1 / (k + rank_i(doc)) )
```

Where `k=60` is a smoothing constant that prevents high-ranked documents from dominating.

## 6. Key Methods

| Method | Purpose |
|--------|---------|
| `search()` | Orchestrates search based on type. Returns `(hits, query)`. |
| `answer()` | Full RAG flow: search + context + generation. |
| `_reciprocal_rank_fusion()` | Merges semantic and text results. |

## 7. Dependency Inversion

The service depends only on abstractions:

| Interface | Use |
|-----------|-----|
| `IRepository` | `semantic_search()` and `text_search()` |
| `IEmbedder` | `get_embedding()` for query vectorization |
| `ILLMProvider` | `generate_response()` for answer generation |
| `ContextBuilder` | Assembles context with diversity limits |
