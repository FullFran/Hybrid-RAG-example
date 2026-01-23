from src.services.ingest_service import IngestService
from src.services.rag_service import RAGService
from src.settings import load_settings


def _get_repository(settings):
    """Factory to get the repository based on settings using lazy imports."""
    if settings.db_type == "supabase":
        from src.infrastructure.database.supabase_repository import SupabaseRepository

        if not settings.supabase_url or not settings.supabase_key:
            raise ValueError(
                "SUPABASE_URL and SUPABASE_KEY must be set for db_type='supabase'"
            )
        return SupabaseRepository(
            url=settings.supabase_url,
            key=settings.supabase_key,
            threshold=settings.semantic_match_threshold,
        )
    else:
        from src.infrastructure.database.mongo_repository import MongoRepository

        return MongoRepository(
            uri=settings.mongodb_uri,
            db_name=settings.mongodb_database,
            doc_collection=settings.mongodb_collection_documents,
            chunk_collection=settings.mongodb_collection_chunks,
        )


def bootstrap_rag_service() -> RAGService:
    settings = load_settings()
    repository = _get_repository(settings)

    from src.infrastructure.embeddings.openai_embedder import OpenAIEmbedder
    from src.infrastructure.llm.openai_provider import OpenAILLMProvider
    from src.services.context_builder import ContextBuilder

    llm = OpenAILLMProvider(
        api_key=settings.llm_api_key,
        model=settings.llm_model,
        base_url=settings.llm_base_url,
    )

    embedder = OpenAIEmbedder(
        api_key=settings.embedding_api_key,
        model=settings.embedding_model,
        base_url=settings.embedding_base_url,
    )

    context_builder = ContextBuilder(
        max_chars=8000,  # Could be moved to settings
        max_per_document=2,
    )

    return RAGService(repository, llm, embedder, context_builder)


def bootstrap_ingest_service() -> IngestService:
    settings = load_settings()
    repository = _get_repository(settings)

    from src.infrastructure.embeddings.openai_embedder import OpenAIEmbedder
    from src.infrastructure.ingestion.docling_parser import DoclingParser
    from src.infrastructure.ingestion.docling_chunker import DoclingChunker

    embedder = OpenAIEmbedder(
        api_key=settings.embedding_api_key,
        model=settings.embedding_model,
        base_url=settings.embedding_base_url,
    )

    parser = DoclingParser()
    chunker = DoclingChunker(max_tokens=settings.embedding_dimension)

    return IngestService(repository, embedder, parser, chunker)


def bootstrap_agent_service():
    """Bootstrap the AgentService with all dependencies.

    The AgentService wraps RAGService and decides when to search or respond directly.
    """
    from src.services.agent_service import AgentService

    settings = load_settings()

    # Get the RAG service (includes repository, llm, embedder)
    rag_service = bootstrap_rag_service()

    # Agent needs direct LLM access for decision making
    from src.infrastructure.llm.openai_provider import OpenAILLMProvider

    llm = OpenAILLMProvider(
        api_key=settings.llm_api_key,
        model=settings.llm_model,
        base_url=settings.llm_base_url,
    )

    return AgentService(rag_service, llm, conservative=True)
