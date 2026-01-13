# Arquitectura del Sistema: MongoDB RAG Agent

Este documento describe la arquitectura del sistema **MongoDB RAG Agent**, un sistema de Recuperación Aumentada por Generación (RAG) diseñado para buscar y responder preguntas sobre una base de conocimientos documental.

## 1. Contexto del Sistema (C4 Level 1)

El siguiente diagrama muestra cómo interactúa el sistema con los usuarios y los servicios externos.

```mermaid
C4Context
    title Diagrama de Contexto: MongoDB RAG Agent

    Person(user, "Usuario Técnico", "Interactúa con el sistema vía CLI para realizar consultas.")

    System(rag_agent, "MongoDB RAG Agent", "Procesa documentos, genera embeddings y responde consultas usando RAG.")

    System_Ext(mongodb, "MongoDB Atlas", "Almacena documentos, fragmentos (chunks) y realiza búsquedas vectoriales/texto.")
    System_Ext(openai, "OpenAI / OpenRouter", "Provee servicios de embeddings (LLM) y generación de texto.")
    System_Ext(docling, "Docling", "Servicio de procesamiento y conversión de documentos (PDF, Docx, etc.).")

    Rel(user, rag_agent, "Realiza consultas y recibe respuestas")
    Rel(rag_agent, mongodb, "Almacena y busca datos")
    Rel(rag_agent, openai, "Genera embeddings y respuestas LLM")
    Rel(rag_agent, docling, "Convierte documentos a Markdown")
```

---

## 2. Contenedores del Sistema (C4 Level 2)

El sistema se divide en dos componentes principales: el **Pipeline de Ingesta** y el **Agente RAG**.

```mermaid
C4Container
    title Diagrama de Contenedores: MongoDB RAG Agent

    Person(user, "Usuario Técnico", "Consultas vía CLI")

    Container_Boundary(c1, "Aplicación Python") {
        Container(cli, "CLI Interface", "Rich / Click", "Interfaz de línea de comandos interactiva.")
        Container(ingest_pipeline, "Ingestion Pipeline", "Python / Docling", "Procesa archivos locales y los guarda en DB.")
        Container(agent, "RAG Agent", "Pydantic AI", "Orquesta la búsqueda y la generación de respuestas.")
        Container(tools, "Search Tools", "Python / Motor", "Implementa algoritmos de búsqueda (Semántica, Texto, Híbrida).")
    }

    ContainerDb(db, "MongoDB Atlas", "NoSQL / Vector Store", "Almacena 'documents' y 'chunks' con índices de búsqueda.")

    System_Ext(llm, "LLM Provider", "OpenAI / OpenRouter API", "Generación de texto y embeddings.")

    Rel(user, cli, "Usa")
    Rel(cli, agent, "Envía consultas")
    Rel(cli, ingest_pipeline, "Inicia ingesta de archivos locales")
    Rel(ingest_pipeline, db, "Guarda documentos y chunks")
    Rel(agent, tools, "Llama a herramientas de búsqueda")
    Rel(tools, db, "Realiza consultas $vectorSearch y $search")
    Rel(agent, llm, "Solicita generación de respuesta")
```

---

## 3. Flujos Principales

### A. Pipeline de Ingestión

1. **Carga**: Se leen archivos del directorio `./documents`.
2. **Conversión**: **Docling** convierte PDF/Docx/Audio a Markdown.
3. **Fragmentación (Chunking)**: Se divide el texto en fragmentos semánticos.
4. **Embedding**: Se generan vectores para cada fragmento vía OpenAI.
5. **Almacenamiento**: Se guardan en MongoDB en dos colecciones:
   - `documents`: Metadatos del archivo original.
   - `chunks`: Texto del fragmento, vector de embedding y referencia al document_id.

### B. Ciclo de Consulta (RAG)

1. **Input**: El usuario escribe una consulta en el CLI.
2. **Razonamiento**: El Agente (Pydantic AI) decide qué herramienta usar.
3. **Búsqueda Híbrida**:
   - **Búsqueda Semántica**: Usa `$vectorSearch` para encontrar conceptos similares.
   - **Búsqueda de Texto**: Usa `$search` (Lucene) para coincidencias exactas y fuzzy.
4. **Fusión (RRF)**: Se combinan los resultados usando _Reciprocal Rank Fusion_ para priorizar lo más relevante.
5. **Síntesis**: El LLM recibe los fragmentos recuperados y genera la respuesta final.

---

## 4. Dependencias de Base de Datos (Clave para Migración)

Si planeas cambiar la base de datos, los puntos de acoplamiento están en:

1. **`src/dependencies.py`**:

   - Gestión de la conexión (`AsyncMongoClient`).
   - Inicialización del cliente y acceso a colecciones.

2. **`src/tools.py`**:

   - Consultas de agregación de MongoDB.
   - Uso de operadores específicos: `$vectorSearch`, `$search`, `$lookup` (para joins entre chunks y docs), y `$meta: "vectorSearchScore"`.

3. **`src/ingestion/ingest.py`**:
   - Lógica de guardado (`insert_one`, `insert_many`).
   - Gestión de IDs de documentos (`ObjectId`).

> [!IMPORTANT]
> El sistema utiliza **RRF Manual** en Python (`reciprocal_rank_fusion` en `src/tools.py`). Esto es una ventaja para la migración, ya que no dependes de una implementación nativa de la base de datos para la fusión de rangos.

---

## 5. Modelos de Datos

- **Document**: `{ _id, title, source, metadata, created_at }`
- **Chunk**: `{ _id, document_id, content, embedding: [float], metadata, token_count }`
