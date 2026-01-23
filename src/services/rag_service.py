import logging
from typing import AsyncIterator, List

from src.core.interfaces.embedder import IEmbedder
from src.core.interfaces.llm import ILLMProvider
from src.core.interfaces.repository import IRepository
from src.core.schemas.search import SearchHit, SearchType
from src.services.context_builder import ContextBuilder

logger = logging.getLogger(__name__)


class RAGService:
    """Business logic for Retrieval Augmented Generation."""

    def __init__(
        self,
        repository: IRepository,
        llm: ILLMProvider,
        embedder: IEmbedder,
        context_builder: ContextBuilder = None,
    ):
        self.repository = repository
        self.llm = llm
        self.embedder = embedder
        self.context_builder = context_builder or ContextBuilder()

    async def search(
        self, query: str, limit: int = 5, search_type: SearchType = SearchType.HYBRID
    ) -> tuple[List[SearchHit], str]:
        """Orchestrate search across multiple methods and merge results.

        Args:
            query: Search query (should be pre-optimized by caller).
            limit: Maximum number of results to return.
            search_type: Type of search to perform.

        Returns:
            Tuple of (hits, query_used).
        """
        if search_type == SearchType.SEMANTIC:
            vector = await self.embedder.get_embedding(query)
            results = await self.repository.semantic_search(vector, limit)
            return results, query
        elif search_type == SearchType.TEXT:
            results = await self.repository.text_search(query, limit)
            return results, query
        else:  # hybrid (RRF)
            logger.debug(f"Hybrid search with query: {query}")

            vector = await self.embedder.get_embedding(query)
            semantic_results = await self.repository.semantic_search(vector, limit * 2)
            text_results = await self.repository.text_search(query, limit * 2)
            merged = self._reciprocal_rank_fusion(semantic_results, text_results)
            logger.debug(f"Hybrid search merged into {len(merged)} results")
            return merged[:limit], query

    def _reciprocal_rank_fusion(
        self,
        semantic_hits: List[SearchHit],
        text_hits: List[SearchHit],
        k: int = 60,
    ) -> List[SearchHit]:
        """Merge search results using Reciprocal Rank Fusion.

        Creates NEW SearchHit objects with fusion_score set.
        Preserves original semantic_score and text_score from each channel.
        """
        rrf_scores: dict[str, float] = {}
        hits_by_id: dict[str, SearchHit] = {}
        semantic_scores: dict[str, float] = {}
        text_scores: dict[str, float] = {}

        # Process semantic results
        for rank, hit in enumerate(semantic_hits):
            chunk_id = hit.chunk.id or f"temp_sem_{rank}"
            rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0) + 1.0 / (k + rank)
            hits_by_id[chunk_id] = hit
            if hit.semantic_score is not None:
                semantic_scores[chunk_id] = hit.semantic_score

        # Process text results
        for rank, hit in enumerate(text_hits):
            chunk_id = hit.chunk.id or f"temp_text_{rank}"
            rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0) + 1.0 / (k + rank)
            if chunk_id not in hits_by_id:
                hits_by_id[chunk_id] = hit
            if hit.text_score is not None:
                text_scores[chunk_id] = hit.text_score

        # Sort by RRF score
        sorted_ids = sorted(
            rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True
        )

        # Create NEW SearchHit objects with fusion_score (no mutation!)
        fused_hits = []
        for chunk_id in sorted_ids:
            original = hits_by_id[chunk_id]
            fused_hit = SearchHit(
                chunk=original.chunk,
                document_title=original.document_title,
                document_source=original.document_source,
                semantic_score=semantic_scores.get(chunk_id),
                text_score=text_scores.get(chunk_id),
                fusion_score=rrf_scores[chunk_id],
            )
            fused_hits.append(fused_hit)

        return fused_hits

    async def answer(
        self, query: str, system_prompt: str, limit: int = 5
    ) -> tuple[AsyncIterator[str] | str, List[SearchHit], str]:
        """Find relevant info and generate an answer.

        Returns:
            Tuple of (response_stream, hits, search_query).
        """
        hits, search_query = await self.search(query, limit=limit)

        if not hits:
            logger.warning(f"No documents found for search query: {search_query}")
            return (
                "I couldn't find any relevant information in the knowledge base.",
                [],
                search_query,
            )

        # Build context using ContextBuilder
        result = self.context_builder.build(hits)

        user_prompt = f"Context:\n{result.context}\n\nQuestion: {query}"
        response = await self.llm.generate_response(
            system_prompt, user_prompt, stream=True
        )
        return response, hits, search_query
