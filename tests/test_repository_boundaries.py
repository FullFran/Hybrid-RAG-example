"""Tests for the boundaries between retrieval and administration.

These cover the two design fixes that motivated issues #12 and #14:

* Destructive access is not part of ``IRepository``. Anything that only needs
  to persist and retrieve cannot wipe the database.
* The similarity threshold is retrieval policy owned by the application layer
  and carried per query, not configuration baked into an adapter.
"""

import inspect

import pytest

from src.core.dtos import SearchOptions
from src.core.interfaces.admin_repository import IAdminRepository
from src.core.interfaces.repository import IRepository
from src.core.schemas.chunk import Chunk
from src.core.schemas.search import SearchHit, SearchType
from src.services.context_builder import ContextBuilder
from src.services.rag_service import RAGService
from tests.conftest import FakeAdminRepository, MockEmbedder, MockRepository


def _hit() -> SearchHit:
    return SearchHit(
        chunk=Chunk(id="c1", document_id="d1", content="test", chunk_index=0),
        document_title="Test document",
        document_source="test.md",
        semantic_score=0.9,
    )


class TestAdminSeparation:
    """Issue #12: clean_all() must not hang off the retrieval interface."""

    def test_retrieval_interface_has_no_destructive_method(self):
        assert not hasattr(IRepository, "clean_all"), (
            "clean_all() is back on IRepository. Destructive access belongs to "
            "IAdminRepository so that retrieval consumers cannot reach it."
        )

    def test_admin_interface_owns_destructive_method(self):
        assert hasattr(IAdminRepository, "clean_all")
        assert hasattr(IAdminRepository, "get_stats")

    def test_retrieval_interface_keeps_its_own_methods(self):
        for name in ("save_document", "save_chunks", "semantic_search", "text_search"):
            assert hasattr(IRepository, name)

    def test_concrete_adapters_declare_both_ports(self):
        """A concrete adapter may implement both; consumers depend on one."""
        from src.infrastructure.database import mongo_repository, supabase_repository

        for module, cls_name in (
            (mongo_repository, "MongoRepository"),
            (supabase_repository, "SupabaseRepository"),
        ):
            cls = getattr(module, cls_name)
            bases = inspect.getmro(cls)
            assert IRepository in bases, f"{cls_name} must implement IRepository"
            assert IAdminRepository in bases, (
                f"{cls_name} must implement IAdminRepository"
            )


class TestIngestServiceDestructiveAccess:
    """Ingestion only gets destructive powers when they are asked for."""

    @pytest.mark.asyncio
    async def test_clean_fails_loudly_without_an_admin_repository(self):
        from src.services.ingest_service import IngestService

        service = IngestService(
            repository=MockRepository(),
            embedder=MockEmbedder(),
            parser=None,
            chunker=None,
        )

        with pytest.raises(RuntimeError, match="admin repository"):
            await service.clean()

    @pytest.mark.asyncio
    async def test_clean_delegates_to_the_admin_repository(self):
        from src.services.ingest_service import IngestService

        admin = FakeAdminRepository()
        service = IngestService(
            repository=MockRepository(),
            embedder=MockEmbedder(),
            parser=None,
            chunker=None,
            admin_repository=admin,
        )

        await service.clean()

        assert admin.clean_all_calls == 1


class TestThresholdIsApplicationPolicy:
    """Issue #14: the threshold travels with the query."""

    @pytest.mark.asyncio
    async def test_default_options_reach_the_adapter(self):
        repo = MockRepository(semantic_results=[_hit()])
        rag = RAGService(repo, None, MockEmbedder(), ContextBuilder())

        await rag.search("q", limit=3, search_type=SearchType.SEMANTIC)

        assert repo.search_history == [("semantic", 3, 0.3)]

    @pytest.mark.asyncio
    async def test_per_query_options_override_the_default(self):
        repo = MockRepository(semantic_results=[_hit()])
        rag = RAGService(repo, None, MockEmbedder(), ContextBuilder())

        await rag.search(
            "q",
            limit=3,
            search_type=SearchType.SEMANTIC,
            options=SearchOptions(threshold=0.85),
        )

        assert repo.search_history == [("semantic", 3, 0.85)]

    @pytest.mark.asyncio
    async def test_service_level_default_is_configurable(self):
        repo = MockRepository(semantic_results=[_hit()])
        rag = RAGService(
            repo,
            None,
            MockEmbedder(),
            ContextBuilder(),
            default_options=SearchOptions(threshold=0.5),
        )

        await rag.search("q", limit=2, search_type=SearchType.SEMANTIC)

        assert repo.search_history == [("semantic", 2, 0.5)]

    @pytest.mark.asyncio
    async def test_hybrid_search_also_carries_the_threshold(self):
        repo = MockRepository(semantic_results=[_hit()], text_results=[_hit()])
        rag = RAGService(repo, None, MockEmbedder(), ContextBuilder())

        await rag.search(
            "q",
            limit=2,
            search_type=SearchType.HYBRID,
            options=SearchOptions(threshold=0.7),
        )

        semantic_calls = [c for c in repo.search_history if c[0] == "semantic"]
        assert semantic_calls == [("semantic", 4, 0.7)]

    def test_the_adapter_no_longer_stores_a_threshold(self):
        """The adapter keeps a last-resort constant, never instance state."""
        from src.infrastructure.database import supabase_repository

        assert hasattr(supabase_repository, "DEFAULT_SEMANTIC_THRESHOLD")
        params = inspect.signature(
            supabase_repository.SupabaseRepository.__init__
        ).parameters
        assert "threshold" not in params, (
            "SupabaseRepository takes a threshold again. Retrieval policy "
            "belongs to SearchOptions, not to adapter construction."
        )


class TestOptionalIngestionExtra:
    """Issue #18: the heavy ingestion stack must stay optional."""

    def test_docling_chunker_module_imports_without_the_extra(self):
        """Importing the module must not require docling or transformers."""
        import importlib

        module = importlib.import_module("src.infrastructure.ingestion.docling_chunker")
        assert hasattr(module, "DoclingChunker")

    def test_module_does_not_import_the_extra_at_top_level(self):
        from pathlib import Path

        source = Path("src/infrastructure/ingestion/docling_chunker.py").read_text()
        header = source.split("class DoclingChunker")[0]
        for dependency in ("from docling", "from transformers"):
            assert dependency not in header, (
                f"'{dependency}' is imported at module level again. It must be "
                "imported inside __init__ so the module loads without the "
                "'ingestion' extra."
            )
