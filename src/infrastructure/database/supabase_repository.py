import logging
from typing import List

from supabase import Client, create_client

from src.core.interfaces.repository import IRepository
from src.core.schemas.chunk import Chunk
from src.core.schemas.document import Document
from src.core.schemas.search import SearchMatch

logger = logging.getLogger(__name__)


class SupabaseRepository(IRepository):
    """Supabase/PostgreSQL implementation of the repository interface."""

    def __init__(self, url: str, key: str, threshold: float = 0.3):
        self.client: Client = create_client(url, key)
        self.threshold = threshold

    async def save_document(self, document: Document) -> str:
        data = document.model_dump(exclude={"id"}, by_alias=True, mode="json")
        # In Supabase/Postgres, we insert and get the ID back
        result = self.client.table("documents").insert(data).execute()
        if not result.data:
            raise Exception("Failed to save document to Supabase")
        return str(result.data[0]["id"])

    async def save_chunks(self, chunks: List[Chunk]) -> None:
        if not chunks:
            return

        chunk_dicts = []
        for chunk in chunks:
            cd = chunk.model_dump(exclude={"id"}, by_alias=True, mode="json")
            # Ensure document_id is treated as a UUID string for Postgres
            chunk_dicts.append(cd)

        result = self.client.table("chunks").insert(chunk_dicts).execute()
        if not result.data:
            logger.error(f"Failed to save chunks: {result}")

    async def semantic_search(
        self, vector: List[float], limit: int
    ) -> List[SearchMatch]:
        """
        Perform semantic search using pgvector via an RPC function.
        Assumes a stored procedure 'match_chunks' exists in the database.
        """
        rpc_params = {
            "query_embedding": vector,
            "match_threshold": self.threshold,
            "match_count": limit,
        }

        logger.debug(
            f"Performing semantic search. Query vector dim: {len(vector)}. Threshold: {self.threshold}"
        )
        result = self.client.rpc("match_chunks", rpc_params).execute()
        logger.debug(f"Semantic search result: {len(result.data)} matches from RPC")
        if result.data:
            logger.debug(f"Top match similarity: {result.data[0].get('similarity')}")

        matches = []
        for item in result.data:
            chunk = Chunk(
                _id=str(item["id"]),
                document_id=str(item["document_id"]),
                content=item["content"],
                chunk_index=item.get("chunk_index", 0),
                metadata=item.get("metadata", {}),
            )
            matches.append(
                SearchMatch(
                    chunk=chunk,
                    similarity=item["similarity"],
                    document_title=item["doc_title"],
                    document_source=item["doc_source"],
                )
            )
        return matches

    async def text_search(self, query: str, limit: int) -> List[SearchMatch]:
        """
        Perform full-text search using a custom PostgreSQL RPC that returns ts_rank.
        """
        rpc_params = {
            "query_text": query,
            "match_count": limit,
        }

        logger.debug(f"Performing text search (RPC) for query: '{query}'")
        result = self.client.rpc("text_search_chunks", rpc_params).execute()
        logger.debug(f"Text search found {len(result.data)} matches from RPC")

        matches = []
        for item in result.data:
            chunk = Chunk(
                _id=str(item["id"]),
                document_id=str(item["document_id"]),
                content=item["content"],
                metadata=item.get("metadata", {}),
                # Note: chunk_index is not returned by current RPC to keep it simple,
                # but can be added if needed.
                chunk_index=0,
            )
            matches.append(
                SearchMatch(
                    chunk=chunk,
                    similarity=item["similarity"],  # This is now the ts_rank
                    document_title=item.get("doc_title", "Unknown"),
                    document_source=item.get("doc_source", "Unknown"),
                )
            )
        return matches

    async def clean_all(self) -> None:
        # Cascading delete should handle chunks if set up in Postgres
        self.client.table("documents").delete().neq(
            "id", "00000000-0000-0000-0000-000000000000"
        ).execute()

    async def close(self):
        # Supabase client doesn't strictly need closing like Motor, but good to have the hook
        pass
