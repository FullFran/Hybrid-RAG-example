# Ingestión de Documentos: Embedder y Chunker

Este módulo se encarga de procesar documentos crudos, dividirlos en fragmentos inteligentes (chunking) y generar representaciones vectoriales (embeddings) para su posterior recuperación en el sistema RAG.

## Componentes Actuales

### 1. `chunker.py` (Docling HybridChunker)

Utiliza **Docling** para realizar un particionado inteligente que:

- Respeta la estructura del documento (encabezados, tablas, párrafos).
- Es consciente de los tokens (ajusta los trozos al límite del modelo de embedding).
- **Estado Actual:** Ejecución **Local** mediante Transformers (`sentence-transformers/all-MiniLM-L6-v2`) para la tokenización. Depende de modelos locales para el análisis estructural.

### 2. `embedder.py` (OpenAI-Compatible API)

Genera los vectores de búsqueda para cada fragmento.

- **Estado Actual:** **Cloud-Ready**. Utiliza APIs externas (OpenAI o compatibles) para generar embeddings.

---

## Alternativas Cloud (Escalabilidad y Rendimiento)

Para despliegues en servidores cloud con recursos limitados (CPU/RAM) o para mejorar la precisión del parseo sin depender de modelos locales pesados, se recomiendan las siguientes alternativas:

### A. Parseo y Chunking en la Nube

Para evitar el uso de Transformers y modelos de visión locales:

1.  **Docling Serve (API/Container):**
    - Desplegar Docling como un microservicio independiente (Docker).
    - Permite delegar el procesamiento a un servidor dedicado o usar el modo `api` para descripciones de imágenes mediante modelos externos.
2.  **LlamaParse:**
    - Servicio cloud especializado en la extracción de Markdown y tablas complejas de PDFs.
    - Muy rápido y optimizado para RAG.
3.  **Unstructured.io API:**
    - Plataforma robusta que soporta multitud de formatos y ofrece una API gestionada para extraer texto y estructura.
4.  **Servicios de Proveedores Cloud:**
    - **Amazon Textract**, **Azure Document Intelligence** o **Google Document AI**. Ideales para documentos escaneados o formularios complejos.

### B. Reemplazo de Modelos Locales

Para eliminar totalmente la dependencia de `transformers` y `local models`:

- **Embedding:** Sustituir modelos locales por APIs de **OpenAI** (text-embedding-3-small/large), **Cohere** o **Voyage AI**.
- **Audio/Transcripción:** Si se integrara Whisper, usar la **OpenAI Audio API** o **Deepgram** en lugar de `faster-whisper` local.

---

## Estrategia de Refactorización (Roadmap)

Para "cloudificar" este módulo sin romper la lógica actual:

1.  **Abstracción de Clientes:** Crear interfaces base para `BaseChunker` y `BaseEmbedder`.
2.  **Inyección de Configuración:** Usar variables de entorno (`.env`) para alternar entre proveedores (e.g., `PARSING_STRATEGY=local` vs `PARSING_STRATEGY=llamaparse`).
3.  **Clientes Remotos:** Implementar adaptadores que llamen a las APIs de LlamaParse o Unstructured.io, devolviendo el mismo formato de `DocumentChunk`.
4.  **Docling Serve integration:** Si se prefiere mantener Docling, configurar el `DocumentConverter` para conectar con una instancia remota de **Docling Serve** en lugar de instanciar los modelos localmente.
