"""Tests for ContextBuilder."""

from src.core.schemas.chunk import Chunk
from src.core.schemas.search import SearchHit
from src.services.context_builder import ContextBuilder, ContextResult


class TestContextBuilder:
    """Tests for context building functionality."""

    def test_build_empty_hits(self):
        """Should handle empty hit list."""
        cb = ContextBuilder()
        result = cb.build([])

        assert result.context == ""
        assert result.total_hits == 0
        assert result.included_hits == 0

    def test_build_includes_content(self):
        """Should include chunk content in context."""
        chunk = Chunk(
            id="c1",
            document_id="d1",
            content="This is important information.",
            chunk_index=0,
        )
        hit = SearchHit(
            chunk=chunk,
            document_title="Important Doc",
            document_source="important.pdf",
            semantic_score=0.95,
        )

        cb = ContextBuilder()
        result = cb.build([hit])

        assert "important information" in result.context
        assert "Important Doc" in result.context
        assert result.total_hits == 1
        assert result.included_hits == 1

    def test_build_respects_max_chars(self):
        """Should truncate when max_chars is exceeded."""
        hits = []
        for i in range(10):
            chunk = Chunk(
                id=f"c{i}",
                document_id=f"d{i}",
                content="X" * 500,
                chunk_index=0,
            )
            hits.append(
                SearchHit(
                    chunk=chunk,
                    document_title=f"Doc {i}",
                    document_source=f"d{i}.pdf",
                    semantic_score=0.9 - (i * 0.05),
                )
            )

        cb = ContextBuilder(max_chars=1000)
        result = cb.build(hits)

        assert len(result.context) <= 1200
        assert result.truncated is True
        assert result.included_hits < result.total_hits

    def test_build_respects_max_per_document(self):
        """Should limit chunks per document for diversity."""
        hits = []
        for i in range(5):
            chunk = Chunk(
                id=f"c{i}",
                document_id="same-doc",
                content=f"Content {i}",
                chunk_index=i,
            )
            hits.append(
                SearchHit(
                    chunk=chunk,
                    document_title="Same Doc",
                    document_source="same.pdf",
                    semantic_score=0.9,
                )
            )

        cb = ContextBuilder(max_per_document=2)
        result = cb.build(hits)

        assert result.included_hits == 2
        assert result.total_hits == 5

    def test_build_creates_citations(self):
        """Should create citation objects for included chunks."""
        chunk = Chunk(
            id="c1",
            document_id="d1",
            content="Cited content",
            chunk_index=3,
        )
        hit = SearchHit(
            chunk=chunk,
            document_title="Cited Doc",
            document_source="cited.pdf",
            semantic_score=0.88,
        )

        cb = ContextBuilder()
        result = cb.build([hit])

        assert len(result.citations) == 1
        assert result.citations[0].document_title == "Cited Doc"
        assert result.citations[0].document_source == "cited.pdf"
        assert result.citations[0].chunk_index == 3
        assert result.citations[0].score == 0.88


class TestContextResult:
    """Tests for ContextResult dataclass."""

    def test_context_result_defaults(self):
        """Should have correct default values."""
        result = ContextResult(context="test")

        assert result.context == "test"
        assert result.citations == []
        assert result.truncated is False
        assert result.total_hits == 0
        assert result.included_hits == 0
