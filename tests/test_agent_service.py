"""Tests for AgentService ReAct implementation."""

import pytest
from src.services.agent_service import AgentService, AgentResult
from src.services.rag_service import RAGService
from src.core.interfaces.llm import ToolResponse, ToolCall
from src.core.schemas.chunk import Chunk
from src.core.schemas.search import SearchHit
from src.services.context_builder import ContextBuilder
from tests.conftest import (
    MockLLMWithTools,
    MockLLMNoTools,
    MockRepository,
    MockEmbedder,
)


class TestReActLoop:
    """Tests for the ReAct loop implementation."""

    @pytest.mark.asyncio
    async def test_react_loop_search_then_answer(
        self, agent_service: AgentService, mock_llm_with_tools: MockLLMWithTools
    ):
        """ReAct should search first, then provide final answer."""
        result = await agent_service.chat(
            query="What is in the test document?",
            system_prompt="You are helpful.",
            limit=5,
        )

        assert result.searched is True
        assert result.search_query is not None
        # Calls: 1 tool call + 1 reformulate + 1 final answer
        assert len(mock_llm_with_tools.call_history) >= 2
        text = await result.collect()
        assert "Based on the documents" in text

    @pytest.mark.asyncio
    async def test_react_loop_direct_answer(self):
        """ReAct should answer directly if LLM doesn't call tools."""
        llm = MockLLMWithTools(
            responses=[ToolResponse(content="FINAL: 2+2 equals 4", tool_calls=[])]
        )

        chunk = Chunk(id="c1", document_id="d1", content="test", chunk_index=0)
        hit = SearchHit(
            chunk=chunk,
            document_title="Test",
            document_source="test.pdf",
            semantic_score=0.9,
        )
        repo = MockRepository(semantic_results=[hit])
        embedder = MockEmbedder()
        cb = ContextBuilder()
        rag = RAGService(repo, llm, embedder, cb)
        agent = AgentService(rag, llm, max_steps=3)

        result = await agent.chat("What is 2+2?", "Be helpful")

        assert result.searched is False
        text = await result.collect()
        assert "4" in text

    @pytest.mark.asyncio
    async def test_react_loop_multiple_searches(self):
        """ReAct should support multiple search iterations."""
        llm = MockLLMWithTools(
            responses=[
                ToolResponse(
                    content=None,
                    tool_calls=[
                        ToolCall(
                            name="search_documents", arguments={"query": "first query"}
                        )
                    ],
                ),
                ToolResponse(
                    content=None,
                    tool_calls=[
                        ToolCall(
                            name="search_documents", arguments={"query": "second query"}
                        )
                    ],
                ),
                ToolResponse(
                    content="FINAL: Combined answer from both searches", tool_calls=[]
                ),
            ]
        )

        chunk = Chunk(id="c1", document_id="d1", content="test", chunk_index=0)
        hit = SearchHit(
            chunk=chunk,
            document_title="Test",
            document_source="test.pdf",
            semantic_score=0.9,
        )
        repo = MockRepository(semantic_results=[hit])
        embedder = MockEmbedder()
        cb = ContextBuilder()
        rag = RAGService(repo, llm, embedder, cb)
        agent = AgentService(rag, llm, max_steps=5)

        result = await agent.chat("Complex question", "Be helpful")

        assert result.searched is True
        # 2 searches + reformulates + final = multiple calls
        assert len(llm.call_history) >= 3

    @pytest.mark.asyncio
    async def test_react_loop_max_steps_exhaustion(self):
        """ReAct should fallback when max_steps is exhausted."""
        llm = MockLLMWithTools(
            responses=[
                ToolResponse(
                    content=None,
                    tool_calls=[
                        ToolCall(name="search_documents", arguments={"query": "query"})
                    ],
                )
                for _ in range(10)
            ]
        )

        chunk = Chunk(id="c1", document_id="d1", content="test content", chunk_index=0)
        hit = SearchHit(
            chunk=chunk,
            document_title="Test",
            document_source="test.pdf",
            semantic_score=0.9,
        )
        repo = MockRepository(semantic_results=[hit])
        embedder = MockEmbedder()
        cb = ContextBuilder()
        rag = RAGService(repo, llm, embedder, cb)
        agent = AgentService(rag, llm, max_steps=2)

        result = await agent.chat("Never ending question", "Be helpful")

        assert result.searched is True
        # 2 tool calls + 2 reformulates + 1 fallback = 5 calls
        assert len(llm.call_history) >= 3

    def test_extract_final_answer(self, agent_service: AgentService):
        """Should correctly extract answer after FINAL: marker."""
        answer = agent_service._extract_final_answer(
            "Some thinking... FINAL: This is the answer."
        )
        assert answer == "This is the answer."

        answer = agent_service._extract_final_answer("No marker here")
        assert answer is None


class TestFallbackMode:
    """Tests for LLMs without tool support."""

    @pytest.mark.asyncio
    async def test_fallback_classifier_search(self):
        """Should use prompt-based classifier when no tools available."""
        llm = MockLLMNoTools(classifier_response="SEARCH")

        chunk = Chunk(id="c1", document_id="d1", content="test", chunk_index=0)
        hit = SearchHit(
            chunk=chunk,
            document_title="Test",
            document_source="test.pdf",
            semantic_score=0.9,
        )
        repo = MockRepository(semantic_results=[hit])
        embedder = MockEmbedder()
        cb = ContextBuilder()
        rag = RAGService(repo, llm, embedder, cb)
        agent = AgentService(rag, llm, conservative=True)

        result = await agent.chat("What documents do I have?", "Be helpful")

        assert result.searched is True
        assert len(llm.call_history) >= 2

    @pytest.mark.asyncio
    async def test_fallback_classifier_direct(self):
        """Should respond directly when classifier says DIRECT."""
        llm = MockLLMNoTools(classifier_response="DIRECT")

        repo = MockRepository()
        embedder = MockEmbedder()
        cb = ContextBuilder()
        rag = RAGService(repo, llm, embedder, cb)
        agent = AgentService(rag, llm, conservative=False)

        result = await agent.chat("What is 2+2?", "Be helpful")

        assert result.searched is False


class TestAgentResult:
    """Tests for AgentResult structure."""

    @pytest.mark.asyncio
    async def test_response_includes_matches(self, agent_service: AgentService):
        """Response should include search matches when RAG is used."""
        result = await agent_service.chat("Find documents", "Be helpful")

        assert isinstance(result, AgentResult)
        assert result.searched is True
        assert len(result.matches) > 0
        assert result.matches[0].document_title == "Test Document"

    @pytest.mark.asyncio
    async def test_response_types(self, agent_service: AgentService):
        """Response should have correct field types."""
        result = await agent_service.chat("Test query", "Be helpful")

        assert isinstance(result.searched, bool)
        assert result.search_query is None or isinstance(result.search_query, str)
        assert isinstance(result.matches, list)
