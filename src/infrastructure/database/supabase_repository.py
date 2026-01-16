"""Supabase/PostgreSQL repository implementation.

This module provides the IRepository implementation for Supabase using pgvector.

Note: The supabase-py client is synchronous, so we wrap calls with
asyncio.to_thread() to avoid blocking the event loop.
"""

import asyncio
import logging
from typing import List

from supabase import Client, create_client

from src.core.exceptions import ChunkSaveError, DocumentSaveError, SearchError
from src.core.interfaces.repository import IRepository
from src.core.schemas.chunk import Chunk
from src.core.schemas.document import Document
from src.core.schemas.search import SearchHit

logger = logging.getLogger(__name__)


class SupabaseRepository(IRepository):
    """Supabase/PostgreSQL implementation of the repository interface.

    Uses pgvector for semantic search and PostgreSQL full-text search.
    All sync operations are wrapped with asyncio.to_thread() to be non-blocking.
    """

    def __init__(self, url: str, key: str, threshold: float = 0.3):
        self.client: Client = create_client(url, key)
        self.threshold = threshold

    async def save_document(self, document: Document) -> str:
        """Save a document and return its ID.

        Raises:
            DocumentSaveError: If the document fails to save.
        """
        data = document.model_dump(exclude={"id"}, by_alias=True, mode="json")

        result = await asyncio.to_thread(
            lambda: self.client.table("documents").insert(data).execute()
        )

        if not result.data:
            raise DocumentSaveError(
                cause="No data returned from insert operation",
                document_id=getattr(document, "id", None),
            )
        return str(result.data[0]["id"])

    async def save_chunks(self, chunks: List[Chunk]) -> None:
        """Save a batch of document chunks using upsert.

        Uses upsert with (document_id, chunk_index) constraint to prevent
        duplicates on re-ingestion.

        Raises:
            ChunkSaveError: If chunks fail to save.
        """
        if not chunks:
            return

        chunk_dicts = []
        document_id = chunks[0].document_id if chunks else None

        for chunk in chunks:
            cd = chunk.model_dump(exclude={"id"}, by_alias=True, mode="json")
            chunk_dicts.append(cd)

        # Use upsert to handle re-ingestion without duplicates
        result = await asyncio.to_thread(
            lambda: self.client.table("chunks")
            .upsert(chunk_dicts, on_conflict="document_id,chunk_index")
            .execute()
        )

        if not result.data:
            raise ChunkSaveError(
                cause="No data returned from upsert operation",
                document_id=document_id,
                chunk_count=len(chunks),
            )

    async def semantic_search(
        self, vector: List[float], limit: int, threshold: float | None = None
    ) -> List[SearchHit]:
        """Perform semantic search using pgvector via RPC.

        Args:
            vector: Query embedding vector.
            limit: Maximum results to return.
            threshold: Optional override for similarity threshold.

        Returns:
            List of SearchHit with semantic_score populated.
        """
        effective_threshold = threshold if threshold is not None else self.threshold
        rpc_params = {
            "query_embedding": vector,
            "match_threshold": effective_threshold,
            "match_count": limit,
        }

        logger.debug(
            f"Semantic search: vector_dim={len(vector)}, threshold={effective_threshold}"
        )

        try:
            result = await asyncio.to_thread(
                lambda: self.client.rpc("match_chunks", rpc_params).execute()
            )
        except Exception as e:
            raise SearchError("semantic", str(e)) from e

        logger.debug(f"Semantic search: {len(result.data)} matches")

        hits = []
        for item in result.data:
            chunk = Chunk(
                id=str(item["id"]),
                document_id=str(item["document_id"]),
                content=item["content"],
                chunk_index=item.get("chunk_index", 0),
                metadata=item.get("metadata", {}),
            )
            hits.append(
                SearchHit(
                    chunk=chunk,
                    document_title=item["doc_title"],
                    document_source=item["doc_source"],
                    semantic_score=item["similarity"],  # Explicit semantic score
                )
            )
        return hits

    async def text_search(self, query: str, limit: int) -> List[SearchHit]:
        """Perform full-text search using PostgreSQL RPC with ts_rank.

        Returns:
            List of SearchHit with text_score populated.
        """
        rpc_params = {
            "query_text": query,
            "match_count": limit,
        }

        logger.debug(f"Text search: query='{query}'")

        try:
            result = await asyncio.to_thread(
                lambda: self.client.rpc("text_search_chunks", rpc_params).execute()
            )
        except Exception as e:
            raise SearchError("text", str(e)) from e

        logger.debug(f"Text search: {len(result.data)} matches")

        hits = []
        for item in result.data:
            chunk = Chunk(
                id=str(item["id"]),
                document_id=str(item["document_id"]),
                content=item["content"],
                metadata=item.get("metadata", {}),
                chunk_index=item.get("chunk_index", 0),  # Will be fixed with RPC update
            )
            hits.append(
                SearchHit(
                    chunk=chunk,
                    document_title=item.get("doc_title", "Unknown"),
                    document_source=item.get("doc_source", "Unknown"),
                    text_score=item["similarity"],  # Explicit text score (ts_rank)
                )
            )
        return hits

    async def clean_all(self) -> None:
        """Clear all documents and chunks.

        Cascading delete handles chunks if set up in Postgres.
        """
        await asyncio.to_thread(
            lambda: self.client.table("documents")
            .delete()
            .neq("id", "00000000-0000-0000-0000-000000000000")
            .execute()
        )

    async def close(self) -> None:
        """Close the repository connection.

        Supabase client doesn't require explicit closing, but this hook
        exists for interface consistency.
        """
        pass
