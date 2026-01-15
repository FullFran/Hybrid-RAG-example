# Detalle de Implementación: Agent Service

Este documento proporciona una vista de "lupa" sobre el `AgentService`, detallando su lógica de decisión ReAct, flujo de datos y cómo orquesta el RAG.

## 1. Responsabilidad

El `AgentService` es un agente ReAct vanilla que actúa como **punto de entrada principal** del sistema. Su función es decidir automáticamente si una pregunta requiere buscar en la base de conocimientos (RAG) o puede responderse directamente con conocimiento general del LLM.

> [!IMPORTANT]
> El agente opera en **modo conservador**: ante cualquier duda, siempre busca en el RAG para priorizar la precisión sobre la velocidad.

## 2. Diagrama de Secuencia (Flujo de Decisión)

El siguiente diagrama muestra el flujo temporal del patrón ReAct:

```mermaid
sequenceDiagram
    autonumber
    participant U as Usuario
    participant A as AgentService
    participant LLM as ILLMProvider
    participant RAG as RAGService

    U->>A: chat(query, system_prompt)
    activate A

    Note over A: _decide(query)

    alt Function Calling soportado
        A->>LLM: generate_with_tools(query, [SEARCH_TOOL])
        LLM-->>A: ToolResponse

        alt tool_calls presente
            Note over A: Decisión: SEARCH
        else No tool_calls (conservative)
            A->>LLM: Fallback a _decide_with_prompt()
        end
    else Solo Prompt Engineering
        A->>LLM: generate_response(classifier, query)
        LLM-->>A: "SEARCH" | "DIRECT"
    end

    alt should_search = True
        A->>RAG: answer(query, system_prompt)
        activate RAG
        Note over RAG: Búsqueda híbrida + generación
        RAG-->>A: (response, matches, search_query)
        deactivate RAG
        A-->>U: AgentResponse(searched=True, matches)
    else should_search = False
        A->>LLM: generate_response(system_prompt, query)
        LLM-->>U: AsyncIterator[respuesta]
        A-->>U: AgentResponse(searched=False)
    end

    deactivate A
```

## 3. Diagrama de Componentes (C4 Zoom-in)

Vista estática de las dependencias internas del `AgentService`:

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

    subgraph Interfaces["Abstracciones"]
        direction LR
        ILLM([ILLMProvider])
    end

    subgraph Services["Servicios"]
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

## 4. Estrategias de Decisión

El agente implementa **dos estrategias** con fallback automático:

### A. Function Calling (Preferida)

Usa la API nativa de OpenAI para definir una herramienta `search_documents`:

```python
SEARCH_TOOL = {
    "type": "function",
    "function": {
        "name": "search_documents",
        "description": "Buscar información en la base de conocimientos",
        "parameters": {"type": "object", "properties": {"query": {...}}}
    }
}
```

- Si el LLM invoca la herramienta → **SEARCH**
- Si el LLM responde directamente → En modo conservador, **fallback a prompt**

### B. Prompt Engineering (Fallback)

Para LLMs que no soportan function calling:

```
Clasifica esta pregunta en UNA palabra:
SEARCH = documentos, reuniones, proyectos, datos personales...
DIRECT = SOLO para: saludos, matemáticas, traducciones...
EN CASO DE DUDA → SEARCH
```

## 5. Respuesta Estructurada

El agente retorna un `AgentResponse` dataclass para **explicabilidad**:

| Campo          | Tipo                 | Descripción                         |
| -------------- | -------------------- | ----------------------------------- |
| `response`     | `AsyncIterator[str]` | Stream de la respuesta              |
| `searched`     | `bool`               | Si usó RAG                          |
| `search_query` | `str \| None`        | Query reformulada usada en búsqueda |
| `matches`      | `List[SearchMatch]`  | Documentos encontrados (fuentes)    |

## 6. Inversión de Dependencias

El `AgentService` depende de abstracciones, no de implementaciones:

| Dependencia   | Interfaz       | Uso                           |
| ------------- | -------------- | ----------------------------- |
| `rag_service` | `RAGService`   | Búsqueda híbrida y generación |
| `llm`         | `ILLMProvider` | Decisión y generación directa |

## 7. Configuración

| Parámetro      | Default | Descripción                             |
| -------------- | ------- | --------------------------------------- |
| `conservative` | `True`  | Si hay duda, buscar en RAG              |
| `limit`        | `5`     | Número máximo de documentos a recuperar |

---

> [!TIP]
> Para cambiar el comportamiento de decisión, edita `CLASSIFIER_PROMPT` en `agent_service.py` o ajusta el prompt del `_decide_with_tools()`.
