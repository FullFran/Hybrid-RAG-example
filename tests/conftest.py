"""Pytest fixtures and mocks for testing."""

import pytest

from src.core.interfaces.admin_repository import IAdminRepository
from src.core.interfaces.embedder import IEmbedder
from src.core.interfaces.llm import ILLMProvider, ToolCall, ToolResponse
from src.core.interfaces.repository import IRepository
from src.core.schemas.chunk import Chunk
from src.core.schemas.search import SearchHit
from src.services.agent_service import AgentService
from src.services.context_builder import ContextBuilder
from src.services.rag_service import RAGService


class MockLLMWithTools(ILLMProvider):
    """LLM that supports tools and follows a scripted response sequence."""

    def __init__(self, responses: list[ToolResponse] | None = None):
        self.responses: list[ToolResponse] = responses if responses is not None else []
        self.call_index = 0
        self.call_history: list[tuple] = []

    def supports_tools(self) -> bool:
        return True

    async def generate_response(
        self, system_prompt: str, user_prompt: str, stream: bool = False
    ) -> str:
        self.call_history.append(("generate", user_prompt[:100]))
        return "Generated response"

    async def generate_with_tools(
        self, system_prompt: str, user_prompt: str, tools: list
    ) -> ToolResponse:
        self.call_history.append(("tools", user_prompt[:100]))
        if self.call_index < len(self.responses):
            response = self.responses[self.call_index]
            self.call_index += 1
            return response
        return ToolResponse(content="FINAL: Default answer", tool_calls=[])


class MockLLMNoTools(ILLMProvider):
    """LLM that does NOT support tools (fallback mode)."""

    def __init__(self, classifier_response: str = "SEARCH"):
        self.classifier_response = classifier_response
        self.call_history: list[tuple] = []

    def supports_tools(self) -> bool:
        return False

    async def generate_response(
        self, system_prompt: str, user_prompt: str, stream: bool = False
    ) -> str:
        self.call_history.append(("generate", system_prompt[:50], user_prompt[:50]))
        if "SEARCH" in system_prompt.upper() and "DIRECT" in system_prompt.upper():
            return self.classifier_response
        return "Fallback generated response"


class MockRepository(IRepository):
    """Mock repository with configurable search results."""

    def __init__(
        self,
        semantic_results: list[SearchHit] | None = None,
        text_results: list[SearchHit] | None = None,
    ):
        self._semantic_results: list[SearchHit] = (
            semantic_results if semantic_results is not None else []
        )
        self._text_results: list[SearchHit] = (
            text_results if text_results is not None else []
        )
        self.search_history: list[tuple] = []

    async def save_document(self, document) -> str:
        return "doc-test-id"

    async def save_chunks(self, chunks) -> None:
        pass

    async def semantic_search(
        self, vector: list[float], limit: int, threshold: float | None = None
    ) -> list[SearchHit]:
        # The threshold is recorded so tests can assert that retrieval policy
        # actually reaches the adapter instead of being silently dropped.
        self.search_history.append(("semantic", limit, threshold))
        return self._semantic_results[:limit]

    async def text_search(self, query: str, limit: int) -> list[SearchHit]:
        self.search_history.append(("text", query, limit))
        return self._text_results[:limit]


class FakeAdminRepository(IAdminRepository):
    """Admin double. Records that destructive access was actually used."""

    def __init__(self) -> None:
        self.clean_all_calls = 0

    async def clean_all(self) -> None:
        self.clean_all_calls += 1

    async def get_stats(self) -> dict:
        return {"document_count": 0, "chunk_count": 0}


class MockEmbedder(IEmbedder):
    """Mock embedder that returns fixed vectors."""

    async def get_embedding(self, text: str) -> list[float]:
        return [0.1] * 1536

    async def get_embeddings(self, texts: list[str]) -> list[list[float]]:
        return [[0.1] * 1536 for _ in texts]


@pytest.fixture
def sample_chunk() -> Chunk:
    """Create a sample chunk for testing."""
    return Chunk(
        id="chunk-1",
        document_id="doc-1",
        content="This is test content about MongoDB and vector search.",
        chunk_index=0,
        metadata={"source": "test.pdf"},
    )


@pytest.fixture
def sample_search_hit(sample_chunk: Chunk) -> SearchHit:
    """Create a sample search hit for testing."""
    return SearchHit(
        chunk=sample_chunk,
        document_title="Test Document",
        document_source="test.pdf",
        semantic_score=0.92,
    )


@pytest.fixture
def mock_embedder() -> MockEmbedder:
    """Provide a mock embedder."""
    return MockEmbedder()


@pytest.fixture
def context_builder() -> ContextBuilder:
    """Provide a context builder."""
    return ContextBuilder(max_chars=4000, max_per_document=2)


@pytest.fixture
def mock_repository(sample_search_hit: SearchHit) -> MockRepository:
    """Provide a mock repository with sample data."""
    return MockRepository(semantic_results=[sample_search_hit])


@pytest.fixture
def mock_llm_with_tools() -> MockLLMWithTools:
    """Provide a mock LLM with tools that searches then answers."""
    return MockLLMWithTools(
        responses=[
            ToolResponse(
                content=None,
                tool_calls=[
                    ToolCall(name="search_documents", arguments={"query": "test query"})
                ],
            ),
            ToolResponse(
                content="FINAL: Based on the documents, here is the answer.",
                tool_calls=[],
            ),
        ]
    )


@pytest.fixture
def mock_llm_no_tools() -> MockLLMNoTools:
    """Provide a mock LLM without tool support."""
    return MockLLMNoTools(classifier_response="SEARCH")


@pytest.fixture
def rag_service(
    mock_repository: MockRepository,
    mock_llm_with_tools: MockLLMWithTools,
    mock_embedder: MockEmbedder,
    context_builder: ContextBuilder,
) -> RAGService:
    """Provide a RAGService with mocks."""
    return RAGService(
        mock_repository, mock_llm_with_tools, mock_embedder, context_builder
    )


@pytest.fixture
def agent_service(
    rag_service: RAGService, mock_llm_with_tools: MockLLMWithTools
) -> AgentService:
    """Provide an AgentService with mocks."""
    return AgentService(
        rag_service, mock_llm_with_tools, conservative=True, max_steps=3
    )
