from src.ingestion.chunker import ChunkingConfig, DoclingHybridChunker
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

    return RAGService(repository, llm, embedder)


def bootstrap_ingest_service() -> IngestService:
    settings = load_settings()
    repository = _get_repository(settings)

    from src.infrastructure.embeddings.openai_embedder import OpenAIEmbedder

    embedder = OpenAIEmbedder(
        api_key=settings.embedding_api_key,
        model=settings.embedding_model,
        base_url=settings.embedding_base_url,
    )

    chunker = DoclingHybridChunker(
        ChunkingConfig(max_tokens=settings.embedding_dimension)
    )

    return IngestService(repository, embedder, chunker)
