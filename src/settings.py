"""Settings configuration for MongoDB RAG Agent."""

from typing import Optional

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Database Configuration
    db_type: str = Field(
        default="mongo", description="Database type (mongo or supabase)"
    )

    # MongoDB Configuration
    mongodb_uri: Optional[str] = Field(
        None, description="MongoDB Atlas connection string"
    )

    mongodb_database: str = Field(default="rag_db", description="MongoDB database name")

    mongodb_collection_documents: str = Field(
        default="documents", description="Collection for source documents"
    )

    mongodb_collection_chunks: str = Field(
        default="chunks", description="Collection for document chunks with embeddings"
    )

    mongodb_vector_index: str = Field(
        default="vector_index",
        description="Vector search index name (must be created in Atlas UI)",
    )

    mongodb_text_index: str = Field(
        default="text_index",
        description="Full-text search index name (must be created in Atlas UI)",
    )

    # Supabase Configuration
    supabase_url: Optional[str] = Field(None, description="Supabase project URL")
    supabase_key: Optional[str] = Field(None, description="Supabase API key")

    # LLM Configuration (Generic OpenAI-compatible)
    llm_api_key: str = Field(..., description="API key for the LLM provider")
    llm_model: str = Field(..., description="Model ID to use")
    llm_base_url: str = Field(
        default="https://api.openai.com/v1",
        description="Base URL for the LLM API (OpenAI-compatible)",
    )

    # Embedding Configuration (Generic OpenAI-compatible)
    embedding_api_key: str = Field(..., description="API key for embedding provider")
    embedding_model: str = Field(..., description="Embedding model ID to use")
    embedding_base_url: str = Field(
        default="https://api.openai.com/v1",
        description="Base URL for embedding API (OpenAI-compatible)",
    )
    embedding_dimension: int = Field(
        default=1536,
        description="Embedding vector dimension",
    )

    # Search Configuration
    default_match_count: int = Field(
        default=10, description="Default number of search results to return"
    )

    max_match_count: int = Field(
        default=50, description="Maximum number of search results allowed"
    )

    default_text_weight: float = Field(
        default=0.3, description="Default text weight for hybrid search (0-1)"
    )

    semantic_match_threshold: float = Field(
        default=0.3, description="Threshold for semantic search similarity (0-1)"
    )


def load_settings() -> Settings:
    """Load settings with proper error handling and dynamic validation."""
    try:
        settings = Settings()

        # Validation based on db_type
        if settings.db_type == "mongo":
            if not settings.mongodb_uri:
                raise ValueError("MONGODB_URI is required when DB_TYPE is 'mongo'")
        elif settings.db_type == "supabase":
            if not settings.supabase_url or not settings.supabase_key:
                raise ValueError(
                    "SUPABASE_URL and SUPABASE_KEY are required when DB_TYPE is 'supabase'"
                )

        return settings
    except Exception as e:
        error_msg = f"Configuration Error: {e}"
        # Provide helpful hints for common missing keys
        if "llm_api_key" in str(e).lower():
            error_msg += "\nTip: Set LLM_API_KEY in your .env file"
        if "llm_model" in str(e).lower():
            error_msg += "\nTip: Set LLM_MODEL in your .env file"
        if "embedding_api_key" in str(e).lower():
            error_msg += "\nTip: Set EMBEDDING_API_KEY in your .env file"
        if "embedding_model" in str(e).lower():
            error_msg += "\nTip: Set EMBEDDING_MODEL in your .env file"
        raise ValueError(error_msg) from e
