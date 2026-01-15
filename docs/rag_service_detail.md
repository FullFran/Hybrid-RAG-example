# Detalle de Implementación: RAG Service

Este documento proporciona una vista de "lupa" sobre el `RAGService`, detallando su lógica interna, flujo de datos y cómo interactúa con otras capas del sistema.

## 1. Responsabilidad

El `RAGService` es el orquestador principal del flujo de **Generación Aumentada por Recuperación (RAG)**. Su función es mediar entre la consulta del usuario, la base de conocimientos y el modelo de lenguaje (LLM).

## 2. Diagrama de Secuencia (Flujo Híbrido)

El siguiente diagrama muestra el flujo temporal cuando se utiliza `search_type="hybrid"`:

```mermaid
sequenceDiagram
    autonumber
    participant U as Usuario
    participant RS as RAGService
    participant LLM as ILLMProvider
    participant EMB as IEmbedder
    participant DB as IRepository

    U->>RS: answer(query, system_prompt)
    activate RS

    Note over RS: search(query, search_type="hybrid")
    RS->>LLM: _reformulate_query(query)
    LLM-->>RS: search_query (optimizada)

    par Búsqueda Paralela
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
    LLM-->>U: AsyncIterator[respuesta]
    deactivate RS
```

## 3. Diagrama de Componentes (C4 Zoom-in)

Vista estática de las dependencias internas del `RAGService`:

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

    subgraph Interfaces["Abstracciones (src.core.interfaces)"]
        direction LR
        IEmb([IEmbedder])
        IRepo[(IRepository)]
        ILLM([ILLMProvider])
    end

    %% Dependencies
    reformulate -.->|usa| ILLM
    search -.->|vectoriza| IEmb
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

## 4. Flujos Principales

### A. Búsqueda Híbrida Agéntica (`search_type="hybrid"`)

El método `search()` coordina múltiples pasos:

1. **Reformulación**: `_reformulate_query()` usa el LLM para limpiar la consulta de ruido conversacional y extraer keywords.
2. **Paralelismo**:
   - Genera embeddings via `IEmbedder.get_embedding()`.
   - Ejecuta búsqueda de texto completo via `IRepository.text_search()`.
3. **Fusión de Rangos (RRF)**: `_reciprocal_rank_fusion()` combina los resultados usando la fórmula:
   ```
   score(d) = Σ 1 / (k + rank_i(d))
   ```
   donde `k=60` es el parámetro de suavizado.

### B. Modos Alternativos

| Modo       | Descripción                                       |
| ---------- | ------------------------------------------------- |
| `semantic` | Solo búsqueda vectorial, sin reformulación ni RRF |
| `text`     | Solo búsqueda textual (BM25/FTS), sin embeddings  |

### C. Generación de Respuesta (`answer()`)

1. Invoca `search()` para obtener los top matches.
2. Construye el `context` concatenando los fragmentos recuperados.
3. Formatea el `user_prompt` inyectando contexto + pregunta original.
4. Retorna un `AsyncIterator[str]` para soportar streaming.

## 5. Inversión de Dependencias

El `RAGService` no conoce implementaciones concretas. Depende exclusivamente de interfaces:

| Interfaz       | Uso                                               |
| -------------- | ------------------------------------------------- |
| `IRepository`  | `semantic_search()` y `text_search()`             |
| `IEmbedder`    | `get_embedding()` para vectorizar consultas       |
| `ILLMProvider` | `generate_response()` para reformular y responder |

---

> [!TIP]
> Para ajustar la lógica de ranking, modifica el método `_reciprocal_rank_fusion()` y su parámetro `k`.
