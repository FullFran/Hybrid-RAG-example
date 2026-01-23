# Implementation Detail: Agent Service

This document provides a "magnifying glass" view of the `AgentService`, detailing its ReAct decision logic, data flow, and how it orchestrates RAG.

## 1. Responsibility

The `AgentService` is a vanilla ReAct agent that acts as the **main entry point** of the system. Its function is to automatically decide if a question requires searching the knowledge base (RAG) or can be answered directly using the LLM's general knowledge.

> [!IMPORTANT]
> The agent operates in **conservative mode**: when in doubt, it always searches the RAG to prioritize accuracy over speed.

## 2. Sequence Diagram (Decision Flow)

The following diagram shows the temporal flow of the ReAct pattern:

```mermaid
sequenceDiagram
    autonumber
    participant U as User
    participant A as AgentService
    participant LLM as ILLMProvider
    participant RAG as RAGService

    U->>A: chat(query, system_prompt)
    activate A

    Note over A: _decide(query)

    alt Function Calling supported
        A->>LLM: generate_with_tools(query, [SEARCH_TOOL])
        LLM-->>A: ToolResponse

        alt tool_calls present
            Note over A: Decision: SEARCH
        else No tool_calls (conservative)
            A->>LLM: Fallback to _decide_with_prompt()
        end
    else Prompt Engineering Only
        A->>LLM: generate_response(classifier, query)
        LLM-->>A: "SEARCH" | "DIRECT"
    end

    alt should_search = True
        A->>RAG: answer(query, system_prompt)
        activate RAG
        Note over RAG: Hybrid search + generation
        RAG-->>A: (response, matches, search_query)
        deactivate RAG
        A-->>U: AgentResponse(searched=True, matches)
    else should_search = False
        A->>LLM: generate_response(system_prompt, query)
        LLM-->>U: AsyncIterator[response]
        A-->>U: AgentResponse(searched=False)
    end

    deactivate A
```

## 3. Component Diagram (C4 Zoom-in)

Static view of `AgentService` internal dependencies:

```mermaid
flowchart TB
    subgraph Service["AgentService"]
        direction TB
        chat["chat()"]
        decide["_decide()"]
        decideTools["_decide_with_tools()"]
        decidePrompt["_decide_with_prompt()"]

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
    end

    %% Dependencies
    chat -.->|"answer()"| RAG
    chat -.->|"generate_response()"| ILLM
    decideTools -.->|"generate_with_tools()"| ILLM
    decidePrompt -.->|"generate_response()"| ILLM

    %% Styling
    style Service fill:#1a1a2e,stroke:#16213e,stroke-width:2px,color:#eaeaea
    style Interfaces fill:#0f3460,stroke:#1a1a2e,stroke-width:2px,color:#eaeaea
    style Services fill:#0f4c75,stroke:#1b262c,stroke-width:2px,color:#bbe1fa
    style chat fill:#e94560,stroke:#1a1a2e,color:#fff
    style decide fill:#533483,stroke:#1a1a2e,color:#fff
    style decideTools fill:#533483,stroke:#1a1a2e,color:#fff
    style decidePrompt fill:#533483,stroke:#1a1a2e,color:#fff
```

## 4. Decision Strategies

The agent implements **two strategies** with automatic fallback:

### A. Function Calling (Preferred)

Uses the native OpenAI API to define a `search_documents` tool:

```python
SEARCH_TOOL = {
    "type": "function",
    "function": {
        "name": "search_documents",
        "description": "Search for information in the knowledge base",
        "parameters": {"type": "object", "properties": {"query": {...}}}
    }
}
```

- If the LLM invokes the tool → **SEARCH**
- If the LLM responds directly → In conservative mode, **fallback to prompt**

### B. Prompt Engineering (Fallback)

For LLMs that do not support function calling:

```
Classify this question in ONE word:
SEARCH = documents, meetings, personal data...
DIRECT = ONLY for: greetings, math, translations...
IF IN DOUBT → SEARCH
```

## 5. Structured Response

The agent returns an `AgentResponse` dataclass for **explainability**:

| Field          | Type                 | Description                         |
| -------------- | -------------------- | ----------------------------------- |
| `response`     | `AsyncIterator[str]` | Response stream                     |
| `searched`     | `bool`               | Whether RAG was used                |
| `search_query` | `str \| None`        | Reformulated query used for search  |
| `matches`      | `List[SearchMatch]`  | Found documents (sources)           |

## 6. Dependency Inversion

`AgentService` depends on abstractions, not implementations:

| Dependency    | Interface      | Use                           |
| ------------- | -------------- | ----------------------------- |
| `rag_service` | `RAGService`   | Hybrid search and generation  |
| `llm`         | `ILLMProvider` | Decision and direct generation|

## 7. Configuration

| Parameter      | Default | Description                             |
| -------------- | ------- | --------------------------------------- |
| `conservative` | `True`  | Search RAG if in doubt                  |
| `limit`        | `5`     | Maximum number of documents to retrieve |

---

> [!TIP]
> To change decision behavior, edit `CLASSIFIER_PROMPT` in `agent_service.py` or adjust the `_decide_with_tools()` prompt.
