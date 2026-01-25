"""Tests for RAGService hybrid search and generation."""

import pytest
from src.services.rag_service import RAGService
from src.core.schemas.search import SearchType, SearchHit
from src.core.schemas.chunk import Chunk
from src.services.context_builder import ContextBuilder
from tests.conftest import MockRepository, MockEmbedder, MockLLMWithTools


class TestHybridSearch:
    """Tests for hybrid search functionality."""

    @pytest.mark.asyncio
    async def test_hybrid_search_combines_results(self):
        """Hybrid search should combine semantic and text results."""
        chunk1 = Chunk(
            id="c1", document_id="d1", content="semantic match", chunk_index=0
        )
        chunk2 = Chunk(id="c2", document_id="d2", content="text match", chunk_index=0)

        semantic_hit = SearchHit(
            chunk=chunk1,
            document_title="Semantic Doc",
            document_source="semantic.pdf",
            semantic_score=0.95,
        )
        text_hit = SearchHit(
            chunk=chunk2,
            document_title="Text Doc",
            document_source="text.pdf",
            text_score=0.85,
        )

        repo = MockRepository(semantic_results=[semantic_hit], text_results=[text_hit])
        embedder = MockEmbedder()
        llm = MockLLMWithTools()
        cb = ContextBuilder()

        rag = RAGService(repo, llm, embedder, cb)
        hits, query = await rag.search(
            "test query", limit=5, search_type=SearchType.HYBRID
        )

        assert len(hits) == 2
        assert len(repo.search_history) == 2

    @pytest.mark.asyncio
    async def test_semantic_only_search(self):
        """Semantic search should only use vector search."""
        chunk = Chunk(id="c1", document_id="d1", content="test", chunk_index=0)
        hit = SearchHit(
            chunk=chunk,
            document_title="Doc",
            document_source="doc.pdf",
            semantic_score=0.9,
        )

        repo = MockRepository(semantic_results=[hit])
        embedder = MockEmbedder()
        llm = MockLLMWithTools()
        cb = ContextBuilder()

        rag = RAGService(repo, llm, embedder, cb)
        hits, _ = await rag.search("test", limit=5, search_type=SearchType.SEMANTIC)

        assert len(hits) == 1
        assert repo.search_history == [("semantic", 5)]

    @pytest.mark.asyncio
    async def test_text_only_search(self):
        """Text search should only use keyword search."""
        chunk = Chunk(id="c1", document_id="d1", content="test", chunk_index=0)
        hit = SearchHit(
            chunk=chunk,
            document_title="Doc",
            document_source="doc.pdf",
            text_score=0.8,
        )

        repo = MockRepository(text_results=[hit])
        embedder = MockEmbedder()
        llm = MockLLMWithTools()
        cb = ContextBuilder()

        rag = RAGService(repo, llm, embedder, cb)
        hits, _ = await rag.search("test", limit=5, search_type=SearchType.TEXT)

        assert len(hits) == 1
        assert repo.search_history == [("text", "test", 5)]


class TestReciprocalRankFusion:
    """Tests for RRF merging algorithm."""

    def test_rrf_merges_unique_results(self):
        """RRF should merge results from different sources."""
        chunk1 = Chunk(id="c1", document_id="d1", content="first", chunk_index=0)
        chunk2 = Chunk(id="c2", document_id="d2", content="second", chunk_index=0)

        semantic_hits = [
            SearchHit(
                chunk=chunk1,
                document_title="Doc1",
                document_source="d1.pdf",
                semantic_score=0.9,
            )
        ]
        text_hits = [
            SearchHit(
                chunk=chunk2,
                document_title="Doc2",
                document_source="d2.pdf",
                text_score=0.8,
            )
        ]

        repo = MockRepository()
        embedder = MockEmbedder()
        llm = MockLLMWithTools()
        cb = ContextBuilder()
        rag = RAGService(repo, llm, embedder, cb)

        merged = rag._reciprocal_rank_fusion(semantic_hits, text_hits)

        assert len(merged) == 2
        for hit in merged:
            assert hit.fusion_score is not None

    def test_rrf_boosts_overlapping_results(self):
        """RRF should boost documents appearing in both result sets."""
        chunk = Chunk(id="c1", document_id="d1", content="overlap", chunk_index=0)

        semantic_hits = [
            SearchHit(
                chunk=chunk,
                document_title="Doc",
                document_source="d.pdf",
                semantic_score=0.9,
            )
        ]
        text_hits = [
            SearchHit(
                chunk=chunk,
                document_title="Doc",
                document_source="d.pdf",
                text_score=0.8,
            )
        ]

        repo = MockRepository()
        embedder = MockEmbedder()
        llm = MockLLMWithTools()
        cb = ContextBuilder()
        rag = RAGService(repo, llm, embedder, cb)

        merged = rag._reciprocal_rank_fusion(semantic_hits, text_hits)

        assert len(merged) == 1
        assert merged[0].fusion_score > 1 / 60


class TestAnswer:
    """Tests for answer generation."""

    @pytest.mark.asyncio
    async def test_answer_returns_hits_and_query(self):
        """Answer should return response, hits, and query used."""
        chunk = Chunk(
            id="c1", document_id="d1", content="answer content", chunk_index=0
        )
        hit = SearchHit(
            chunk=chunk,
            document_title="Doc",
            document_source="d.pdf",
            semantic_score=0.9,
        )

        repo = MockRepository(semantic_results=[hit])
        embedder = MockEmbedder()
        llm = MockLLMWithTools()
        cb = ContextBuilder()

        rag = RAGService(repo, llm, embedder, cb)
        response, hits, query = await rag.answer("test question", "Be helpful", limit=3)

        assert len(hits) > 0
        assert query == "test question"

    @pytest.mark.asyncio
    async def test_answer_no_results_message(self):
        """Should return helpful message when no documents found."""
        repo = MockRepository(semantic_results=[], text_results=[])
        embedder = MockEmbedder()
        llm = MockLLMWithTools()
        cb = ContextBuilder()

        rag = RAGService(repo, llm, embedder, cb)
        response, hits, _ = await rag.answer("obscure query", "Be helpful")

        assert len(hits) == 0
        assert isinstance(response, str)
        assert "couldn't find" in response.lower()
