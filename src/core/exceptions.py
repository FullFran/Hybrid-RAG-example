"""Domain exceptions for the RAG system.

These exceptions provide meaningful error context instead of generic exceptions.
They are raised by infrastructure layer and caught by service/endpoint layers.
"""


class RepositoryError(Exception):
    """Base exception for repository operations."""

    pass


class DocumentSaveError(RepositoryError):
    """Raised when a document fails to save to the database."""

    def __init__(self, cause: str, document_id: str | None = None):
        if document_id:
            msg = f"Failed to save document {document_id}: {cause}"
        else:
            msg = f"Failed to save document: {cause}"
        super().__init__(msg)
        self.cause = cause
        self.document_id = document_id


class ChunkSaveError(RepositoryError):
    """Raised when chunks fail to save to the database."""

    def __init__(
        self, cause: str, document_id: str | None = None, chunk_count: int = 0
    ):
        msg = f"Failed to save {chunk_count} chunks"
        if document_id:
            msg += f" for document {document_id}"
        msg += f": {cause}"
        super().__init__(msg)
        self.cause = cause
        self.document_id = document_id
        self.chunk_count = chunk_count


class SearchError(RepositoryError):
    """Raised when a search operation fails."""

    def __init__(self, search_type: str, cause: str):
        super().__init__(f"{search_type} search failed: {cause}")
        self.search_type = search_type
        self.cause = cause


class EmbeddingError(Exception):
    """Raised when embedding generation fails."""

    def __init__(self, cause: str, text_preview: str | None = None):
        msg = f"Embedding generation failed: {cause}"
        if text_preview:
            msg += f" (text: '{text_preview[:50]}...')"
        super().__init__(msg)
        self.cause = cause


class LLMError(Exception):
    """Raised when LLM generation fails."""

    def __init__(self, cause: str, model: str | None = None):
        msg = f"LLM generation failed: {cause}"
        if model:
            msg = f"LLM generation failed (model: {model}): {cause}"
        super().__init__(msg)
        self.cause = cause
        self.model = model
