# Hybrid RAG Agent - Clean Architecture

Sistema RAG (Generación Aumentada por Recuperación) moderno y modular diseñado bajo principios de **Clean Architecture**. Este sistema permite la recuperación inteligente de documentos con total independencia de los proveedores de infraestructura (Base de Datos, LLM o Embeddings).

## 🏛️ Arquitectura: Clean RAG Design

Este proyecto implementa una arquitectura desacoplada donde la lógica de negocio reside en el núcleo, protegida de cambios en servicios externos.

### Principios de Diseño

- **Independencia de Proveedores**: Intercambia fácilmente entre MongoDB, Supabase, PostgreSQL o cualquier otra DB implementando su interfaz.
- **Abstracción de IA**: Soporte para múltiples proveedores de LLM y Embeddings (OpenAI, Anthropic, Local).
- **Testabilidad**: Lógica de RAG verificable sin necesidad de conexiones externas.
- **CLI-First**: Interfaz potente por terminal diseñada para flujo de trabajo técnico.

### Estructura de Capas

1.  **Domain (Core)**: Schemas puros (`Document`, `Chunk`) e interfaces abstractas (`IRepository`, `ILLMProvider`).
2.  **Application (Services)**: `AgentService` (punto de entrada agéntico), `RAGService` (búsqueda híbrida), `IngestService` (ingesta).
3.  **Infrastructure**: Implementaciones concretas (actualmente incluye **Supabase** y **OpenAI**).
4.  **Endpoints**: Interfaz de usuario vía CLI (Rich).

---

### Diagrama de Arquitectura (C4 Clean Design)

```mermaid
flowchart TB
    User((Usuario))

    subgraph Endpoints["Endpoints Layer"]
        CLI[CLI Rich]
    end

    subgraph Services["Application Layer"]
        Agent[AgentService]
        RAG[RAGService]
        Ingest[IngestService]
    end

    subgraph Core["Domain Layer - Interfaces"]
        direction LR
        IRepo([IRepository])
        ILLM([ILLMProvider])
        IEmb([IEmbedder])
    end

    subgraph Infra["Infrastructure Layer"]
        direction TB
        subgraph DBs["Database Providers"]
            Mongo[(MongoRepository)]
            Supa[(SupabaseRepository)]
        end
        subgraph AI["AI Providers"]
            OAILLM[OpenAIProvider]
            OAIEmb[OpenAIEmbedder]
        end
    end

    subgraph Ingestion["Ingestion Module"]
        Chunker[chunker.py]
        Embedder[embedder.py]
    end

    User --> CLI
    CLI --> Agent
    Agent --> RAG
    CLI --> Ingest

    RAG -.-> IRepo
    RAG -.-> ILLM
    Ingest -.-> IRepo
    Ingest -.-> IEmb

    IRepo -.-> Mongo
    IRepo -.-> Supa
    ILLM -.-> OAILLM
    IEmb -.-> OAIEmb

    Ingest --> Chunker
    Ingest --> Embedder

    %% Layer styling
    style Endpoints fill:#2d3436,stroke:#636e72,color:#dfe6e9
    style Services fill:#0984e3,stroke:#74b9ff,color:#fff
    style Core fill:#6c5ce7,stroke:#a29bfe,color:#fff
    style Infra fill:#00b894,stroke:#55efc4,color:#fff
    style Ingestion fill:#fdcb6e,stroke:#f39c12,color:#2d3436
    style DBs fill:#00cec9,stroke:#81ecec,color:#2d3436
    style AI fill:#e17055,stroke:#fab1a0,color:#fff
```

---

## 📂 Organización del Proyecto

```text
src/
├── core/
│   ├── schemas/        # Modelos base: Document, Chunk, SearchMatch
│   ├── dtos/           # Objetos de transferencia de datos
│   └── interfaces/     # Contratos abstractos (IRepository, ILLMProvider)
├── services/           # Lógica de negocio (Agent, RAG, Ingestión)
├── infrastructure/     # Implementaciones concretas de proveedores (Supabase, OpenAI)
└── endpoints/          # Adaptadores de entrada (CLI)
```

---

## 🚀 Guía de Inicio Rápido

### 1. Instalación

Requiere Python 3.10+ y [UV Package Manager](https://astral.sh/uv/).

```bash
git clone https://github.com/FullFran/Hybrid-RAG-example.git
cd Hybrid-RAG-example
uv venv && uv sync
```

### 2. Configuración

Copia `.env.example` a `.env` y configura tus variables de entorno (Supabase URL/Key, OpenAI API Key, etc.).

### 3. Uso

```bash
# Ingestar documentos
uv run python -m src.endpoints.cli.ingest -d ./documents

# Iniciar el chat inteligente
uv run python -m src.endpoints.cli.main
```

---

## 🛠️ Extensibilidad

Gracias a la arquitectura limpia, añadir un nuevo proveedor de base de datos es tan simple como:

1. Crear una nueva clase en `src/infrastructure/database/`.
2. Implementar la interfaz `IRepository`.
3. Inyectarla en el servicio al iniciar la aplicación.
