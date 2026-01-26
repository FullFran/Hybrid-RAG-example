# Agent Service - ReAct Pattern Implementation

The `AgentService` implements a **real ReAct (Reasoning + Acting) loop** that iteratively uses tools before generating a final answer. This is the main entry point of the system.

## 1. Responsibility

The agent orchestrates the decision-making process:

- Decides **when** to search the knowledge base
- Executes **multiple search iterations** if needed
- Builds context from observations
- Generates a final answer when ready

## 2. ReAct Pattern (Iterative Loop)

Unlike a simple router, the ReAct pattern allows **multi-step reasoning**:

```
Step 1: Thought → Action (search) → Observation
Step 2: Thought → Action (search again) → Observation
Step 3: Thought → FINAL: [answer]
```

The agent continues until it has enough information or reaches `max_steps`.

## 3. Sequence Diagram (ReAct Loop)

```mermaid
sequenceDiagram
    autonumber
    participant U as User
    participant A as AgentService
    participant LLM as ILLMProvider
    participant RAG as RAGService

    U->>A: chat(query, system_prompt)
    activate A

    Note over A: _react_loop()

    loop ReAct Steps (max_steps=3)
        A->>LLM: generate_with_tools(scratchpad, [SEARCH_TOOL])
        
        alt tool_calls present
            Note over A: Action: search_documents
            A->>A: _reformulate_query()
            A->>RAG: search(optimized_query)
            RAG-->>A: SearchHit[]
            A->>A: _format_observation(hits)
            Note over A: Append to scratchpad
        else content with "FINAL:"
            A->>A: _extract_final_answer()
            A-->>U: AgentResult(stream, matches)
        end
    end

    Note over A: Fallback if steps exhausted

    alt Has matches from previous searches
        A->>LLM: generate_response(context, query)
    else No matches
        A->>LLM: generate_response(query)
    end

    A-->>U: AgentResult
    deactivate A
```

## 4. Component Diagram

```mermaid
flowchart TB
    subgraph Service["AgentService"]
        direction TB
        chat["chat()"]
        react["_react_loop()"]
        format["_format_observation()"]
        extract["_extract_final_answer()"]
        reformulate["_reformulate_query()"]
        decide["_decide()"]
        decideTools["_decide_with_tools()"]
        decidePrompt["_decide_with_prompt()"]

        chat --> react
        react --> format
        react --> extract
        react --> reformulate
        chat --> decide
        decide --> decideTools
        decide --> decidePrompt
    end

    subgraph Interfaces["Abstractions"]
        direction LR
        ILLM([ILLMProvider])
    end

    subgraph Services["Services"]
        direction LR
        RAG["RAGService"]
        CB["ContextBuilder"]
    end

    %% Dependencies
    react -.->|"generate_with_tools()"| ILLM
    react -.->|"search()"| RAG
    format -.->|"build()"| CB
    reformulate -.->|"generate_response()"| ILLM
    decideTools -.->|"generate_with_tools()"| ILLM
    decidePrompt -.->|"generate_response()"| ILLM

    %% Styling
    style Service fill:#1a1a2e,stroke:#16213e,stroke-width:2px,color:#eaeaea
    style Interfaces fill:#0f3460,stroke:#1a1a2e,stroke-width:2px,color:#eaeaea
    style Services fill:#0f4c75,stroke:#1b262c,stroke-width:2px,color:#bbe1fa
    style chat fill:#e94560,stroke:#1a1a2e,color:#fff
    style react fill:#e94560,stroke:#1a1a2e,color:#fff
    style format fill:#533483,stroke:#1a1a2e,color:#fff
    style extract fill:#533483,stroke:#1a1a2e,color:#fff
    style reformulate fill:#533483,stroke:#1a1a2e,color:#fff
    style decide fill:#533483,stroke:#1a1a2e,color:#fff
    style decideTools fill:#533483,stroke:#1a1a2e,color:#fff
    style decidePrompt fill:#533483,stroke:#1a1a2e,color:#fff
```

## 5. Key Methods

| Method | Purpose |
|--------|---------|
| `chat()` | Main entry point. Routes to ReAct loop or fallback. |
| `_react_loop()` | Core ReAct implementation with scratchpad. |
| `_format_observation()` | Formats search results for the scratchpad. |
| `_extract_final_answer()` | Extracts answer after `FINAL:` marker. |
| `_reformulate_query()` | Optimizes query for semantic search. |
| `_decide()` | Legacy router for LLMs without tool support. |

## 6. Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `max_steps` | `3` | Maximum ReAct iterations before fallback |
| `conservative` | `True` | Search if in doubt (legacy mode) |
| `limit` | `5` | Max documents to retrieve per search |

## 7. Response Structure

```python
@dataclass
class AgentResult:
    stream: AsyncIterator[str]          # Always a stream
    searched: bool = False              # Whether RAG was used
    search_query: str | None = None     # Last optimized query
    matches: List[SearchHit] = []       # Retrieved documents
```

## 8. Fallback Strategy

If the LLM does not support tools (`supports_tools() == False`), the agent falls back to:

1. Prompt-based classification (SEARCH vs DIRECT)
2. Single-shot RAG or direct response

This maintains compatibility with any LLM provider.
