import logging
from typing import List

from src.core.interfaces.embedder import IEmbedder
from src.core.interfaces.llm import ILLMProvider
from src.core.interfaces.repository import IRepository
from src.core.schemas.search import SearchMatch

logger = logging.getLogger(__name__)


class RAGService:
    """Business logic for Retrieval Augmented Generation."""

    def __init__(self, repository: IRepository, llm: ILLMProvider, embedder: IEmbedder):
        self.repository = repository
        self.llm = llm
        self.embedder = embedder

    async def search(
        self, query: str, limit: int = 5, search_type: str = "hybrid"
    ) -> List[SearchMatch]:
        """Orchestrate search across multiple methods and merge results."""
        if search_type == "semantic":
            vector = await self.embedder.get_embedding(query)
            return await self.repository.semantic_search(vector, limit), query
        elif search_type == "text":
            return await self.repository.text_search(query, limit), query
        else:  # hybrid (manual RRF)
            logger.debug(f"Original query: {query}")

            # --- Agentic Step: Query Reformulation ---
            search_query = await self._reformulate_query(query)
            logger.debug(f"Reformulated query for search: {search_query}")

            vector = await self.embedder.get_embedding(search_query)
            semantic_results = await self.repository.semantic_search(vector, limit * 2)
            text_results = await self.repository.text_search(search_query, limit * 2)
            merged = self._reciprocal_rank_fusion([semantic_results, text_results])
            logger.debug(f"Hybrid search merged into {len(merged)} results")
            return merged[:limit], search_query

    async def _reformulate_query(self, query: str) -> str:
        """Use LLM to transform a conversational query into a search-optimized query."""
        system_prompt = (
            "Eres un experto en recuperación de información. Tu tarea es convertir una "
            "pregunta conversacional en una consulta de búsqueda optimizada (keywords y conceptos clave).\n"
            "Reglas:\n"
            "- Elimina saludos, cortesías y relleno.\n"
            "- Extrae las entidades y conceptos principales.\n"
            "- Si la pregunta es corta y directa, mantenla igual.\n"
            "- RESPONDE ÚNICAMENTE CON LA CONSULTA OPTIMIZADA, SIN EXPLICACIONES."
        )

        # We use a non-streaming call for this internal reasoning step
        reformulated = await self.llm.generate_response(
            system_prompt, query, stream=False
        )
        # Clean up in case the LLM added quotes or extra spaces
        return reformulated.strip().strip('"').strip("'")

    def _reciprocal_rank_fusion(
        self, result_sets: List[List[SearchMatch]], k: int = 60
    ) -> List[SearchMatch]:
        """Manual implementation of RRF to merge search results."""
        scores = {}  # (chunk_id) -> score
        matches = {}  # (chunk_id) -> SearchMatch

        for result_set in result_sets:
            for rank, match in enumerate(result_set):
                chunk_id = match.chunk.id
                score = 1.0 / (k + rank)
                if chunk_id in scores:
                    scores[chunk_id] += score
                else:
                    scores[chunk_id] = score
                    matches[chunk_id] = match

        # Sort by score
        sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)

        final_results = []
        for cid in sorted_ids:
            match = matches[cid]
            match.similarity = scores[cid]  # Update similarity with RRF score
            final_results.append(match)

        return final_results

    async def answer(self, query: str, system_prompt: str, limit: int = 5) -> tuple:
        """Find relevant info and generate an answer.

        Returns:
            Tuple of (response, matches, search_query) where response is
            AsyncIterator[str] | str
        """
        matches, search_query = await self.search(query, limit=limit)

        if not matches:
            logger.warning(f"No documents found for search query: {search_query}")
            return (
                "No encontré información relevante en la base de conocimientos.",
                [],
                search_query,
            )

        context = "\n".join(
            [
                f"--- Documento: {m.document_title} ---\n{m.chunk.content}"
                for m in matches
            ]
        )

        user_prompt = f"Contexto:\n{context}\n\nPregunta: {query}"
        response = await self.llm.generate_response(
            system_prompt, user_prompt, stream=True
        )
        return response, matches, search_query
