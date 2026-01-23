# Implementation Detail: RAG Service

This document provides a "magnifying glass" view of the `RAGService`, detailing its internal logic, data flow, and how it interacts with other system layers.

## 1. Responsibility

The `RAGService` is the main orchestrator of the **Retrieval-Augmented Generation (RAG)** flow. Its function is to mediate between the user query, the knowledge base, and the language model (LLM).

## 2. Sequence Diagram (Hybrid Flow)

The following diagram shows the temporal flow when `search_type="hybrid"` is used:

```mermaid
sequenceDiagram
    autonumber
    participant U as User
    participant RS as RAGService
    participant LLM as ILLMProvider
    participant EMB as IEmbedder
    participant DB as IRepository

    U->>RS: answer(query, system_prompt)
    activate RS

    Note over RS: search(query, search_type="hybrid")
    RS->>LLM: _reformulate_query(query)
    LLM-->>RS: optimized search_query

    par Parallel Search
        RS->>EMB: get_embedding(search_query)
        EMB-->>RS: vector[]
        RS->>DB: semantic_search(vector, limit*2)
        DB-->>RS: semantic_results[]
    and
        RS->>DB: text_search(search_query, limit*2)
        DB-->>RS: text_results[]
    end

    Note over RS: _reciprocal_rank_fusion([semantic, text])
    RS->>RS: Merge & Rank (RRF k=60)

    RS->>LLM: generate_response(system_prompt, context + query)
    LLM-->>U: AsyncIterator[response]
    deactivate RS
```

## 3. Component Diagram (C4 Zoom-in)

Static view of `RAGService` internal dependencies:

```mermaid
flowchart TB
    subgraph Service["RAGService"]
        direction TB
        search["search()"]
        reformulate["_reformulate_query()"]
        rrf["_reciprocal_rank_fusion()"]
        answer["answer()"]

        answer --> search
        search --> reformulate
        search --> rrf
    end

    subgraph Interfaces["Abstractions (src.core.interfaces)"]
        direction LR
        IEmb([IEmbedder])
        IRepo[(IRepository)]
        ILLM([ILLMProvider])
    end

    %% Dependencies
    reformulate -.->|uses| ILLM
    search -.->|vectorizes| IEmb
    search -.->|semantic_search / text_search| IRepo
    answer -.->|generate_response| ILLM

    %% Styling
    style Service fill:#1a1a2e,stroke:#16213e,stroke-width:2px,color:#eaeaea
    style Interfaces fill:#0f3460,stroke:#1a1a2e,stroke-width:2px,color:#eaeaea
    style search fill:#e94560,stroke:#1a1a2e,color:#fff
    style answer fill:#e94560,stroke:#1a1a2e,color:#fff
    style reformulate fill:#533483,stroke:#1a1a2e,color:#fff
    style rrf fill:#533483,stroke:#1a1a2e,color:#fff
```

## 4. Main Flows

### A. Agentic Hybrid Search (`search_type="hybrid"`)

The `search()` method coordinates multiple steps:

1. **Reformulation**: `_reformulate_query()` uses the LLM to clean conversational noise from the query and extract keywords.
2. **Parallelism**:
    - Generates embeddings via `IEmbedder.get_embedding()`.
    - Executes full-text search via `IRepository.text_search()`.
3. **Rank Fusion (RRF)**: `_reciprocal_rank_fusion()` combines results using the formula:
    ```
    score(d) = Σ 1 / (k + rank_i(d))
    ```
    where `k=60` is the smoothing parameter.

### B. Alternative Modes

| Mode       | Description                                       |
| ---------- | ------------------------------------------------- |
| `semantic` | Vector search only, no reformulation or RRF       |
| `text`     | Text search only (BM25/FTS), no embeddings        |

### C. Response Generation (`answer()`)

1. Invokes `search()` to get top matches.
2. Builds the `context` by concatenating retrieved fragments.
3. Formats the `user_prompt` injecting context + original question.
4. Returns an `AsyncIterator[str]` to support streaming.

## 5. Dependency Inversion

`RAGService` does not know concrete implementations. It depends exclusively on interfaces:

| Interface      | Use                                               |
| -------------- | ------------------------------------------------- |
| `IRepository`  | `semantic_search()` and `text_search()`             |
| `IEmbedder`    | `get_embedding()` to vectorize queries            |
| `ILLMProvider` | `generate_response()` to reformulate and respond  |

---

> [!TIP]
> To adjust ranking logic, modify the `_reciprocal_rank_fusion()` method and its `k` parameter.
