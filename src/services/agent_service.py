"""
AgentService - ReAct Agent with Iterative Tool Use

Implements the ReAct (Reasoning + Acting) pattern with a multi-step loop:
1. Thought: Reason about what action to take
2. Action: Execute a tool (search_documents)
3. Observation: Process the tool result
4. Repeat until ready to answer with FINAL:

Falls back to prompt-based classification for LLMs without tool support.
"""

import logging
from dataclasses import dataclass, field
from typing import AsyncIterator, List

from src.core.interfaces.llm import ILLMProvider
from src.core.schemas.search import SearchHit
from src.services.rag_service import RAGService

logger = logging.getLogger(__name__)


@dataclass
class AgentResult:
    """Response from the agent with context for explainability."""

    stream: AsyncIterator[str]
    searched: bool = False
    search_query: str | None = None
    matches: List[SearchHit] = field(default_factory=list)

    async def collect(self) -> str:
        """Consume the stream and return the full response as text."""
        return "".join([chunk async for chunk in self.stream])


class AgentService:
    """ReAct agent that iterates tool use before answering.

    The agent uses a conservative approach: when in doubt, it searches.
    This prioritizes accuracy over speed.
    """

    # Tool definition for function calling
    SEARCH_TOOL = {
        "type": "function",
        "function": {
            "name": "search_documents",
            "description": (
                "Search for information in the user's knowledge base. "
                "Use when the question requires specific data from documents, "
                "personal information, or context that is not general knowledge."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Optimized query for semantic search",
                    }
                },
                "required": ["query"],
            },
        },
    }

    # Classifier prompt for fallback strategy
    CLASSIFIER_PROMPT = """Analyze the user's question and classify if you need to search for information.

Respond ONLY with one of these words:
- SEARCH = The question requires specific information from personal documents, particular data, or context that is not general knowledge.
- DIRECT = It is general knowledge, math, common definitions, translations, or casual conversation.

Examples:
- "How much is 2+2?" → DIRECT
- "What does the document say about the budget?" → SEARCH
- "Translate 'hello' to Spanish" → DIRECT
- "What are my pending tasks?" → SEARCH

Respond ONLY: SEARCH or DIRECT"""

    def __init__(
        self,
        rag_service: RAGService,
        llm: ILLMProvider,
        conservative: bool = True,
        max_steps: int = 3,
    ):
        """Initialize the agent.

        Args:
            rag_service: Service for RAG operations.
            llm: LLM provider for generation and decision making.
            conservative: If True, search when in doubt. Default True.
        """
        self.rag = rag_service
        self.llm = llm
        self.conservative = conservative
        self.max_steps = max_steps

    async def chat(
        self,
        query: str,
        system_prompt: str,
        limit: int = 5,
    ) -> AgentResult:
        """Main entry point for the agent.

        Decides whether to search the RAG or respond directly based on the query.

        Args:
            query: User's question.
            system_prompt: System instructions for the response.
            limit: Max number of documents to retrieve if searching.

        Returns:
            AgentResult with response stream and context (searched, matches, etc.)
        """
        if self.llm.supports_tools():
            return await self._react_loop(query, system_prompt, limit)

        # Fallback: no tool support, keep legacy decision flow
        should_search, search_query = await self._decide(query)

        if should_search:
            optimized_query = await self._reformulate_query(search_query or query)
            logger.info(
                f"Agent decided to SEARCH. Optimized query: '{optimized_query}'"
            )

            response, matches, _ = await self.rag.answer(
                optimized_query, system_prompt, limit=limit
            )

            return AgentResult(
                stream=self._ensure_stream(response),
                searched=True,
                search_query=optimized_query,
                matches=matches,
            )

        logger.info("Agent decided to respond DIRECTLY (no RAG).")
        response = await self.llm.generate_response(system_prompt, query, stream=True)
        return AgentResult(stream=self._ensure_stream(response), searched=False)

    async def _react_loop(
        self, query: str, system_prompt: str, limit: int
    ) -> AgentResult:
        """Run a ReAct loop with tool use and observations."""
        react_system = (
            "You are a ReAct agent with access to a knowledge base. "
            "When the user asks for specific or personal information, you MUST use "
            "the search_documents tool. If unsure, search. "
            "After you have enough information, respond with 'FINAL:' followed by the answer."
        )

        full_system = f"{react_system}\n\nResponse rules:\n{system_prompt}"
        scratchpad = ""
        last_matches: List[SearchHit] = []
        last_search_query: str | None = None

        for step in range(self.max_steps):
            user_prompt = (
                f"User question: {query}\n\n"
                f"Scratchpad:\n{scratchpad}\n\n"
                "Decide next action."
            )

            response = await self.llm.generate_with_tools(
                system_prompt=full_system,
                user_prompt=user_prompt,
                tools=[self.SEARCH_TOOL],
            )

            if response.tool_calls:
                tool_call = response.tool_calls[0]
                search_query = tool_call.arguments.get("query", query)
                optimized_query = await self._reformulate_query(search_query)
                logger.info(
                    f"ReAct step {step + 1}: SEARCH with query '{optimized_query}'"
                )

                hits, _ = await self.rag.search(optimized_query, limit=limit)
                last_matches = hits
                last_search_query = optimized_query

                observation = self._format_observation(hits)
                scratchpad += (
                    "Thought: I should search the knowledge base.\n"
                    f"Action: search_documents\n"
                    f"Action Input: {optimized_query}\n"
                    f"Observation:\n{observation}\n\n"
                )
                continue

            if response.content:
                content = response.content.strip()
                final = self._extract_final_answer(content)
                if final is None:
                    final = content
                return AgentResult(
                    stream=self._ensure_stream(final),
                    searched=bool(last_matches),
                    search_query=last_search_query,
                    matches=last_matches,
                )

            logger.warning("ReAct step produced no tool calls or content.")

        logger.warning("ReAct loop exhausted steps; generating final answer.")

        if last_matches:
            context_result = self.rag.context_builder.build(last_matches)
            user_prompt = f"Context:\n{context_result.context}\n\nQuestion: {query}"
            response = await self.llm.generate_response(
                system_prompt, user_prompt, stream=True
            )
            return AgentResult(
                stream=self._ensure_stream(response),
                searched=True,
                search_query=last_search_query,
                matches=last_matches,
            )

        response = await self.llm.generate_response(system_prompt, query, stream=True)
        return AgentResult(stream=self._ensure_stream(response), searched=False)

    def _ensure_stream(self, response: AsyncIterator[str] | str) -> AsyncIterator[str]:
        """Normalize responses to an async stream."""
        if isinstance(response, str):

            async def _stream() -> AsyncIterator[str]:
                yield response

            return _stream()
        return response

    def _format_observation(self, hits: List[SearchHit]) -> str:
        if not hits:
            return "No relevant documents were found."

        context_result = self.rag.context_builder.build(hits)
        sources = "\n".join(
            [f"- {hit.document_title} ({hit.document_source})" for hit in hits[:3]]
        )
        return (
            f"Top sources:\n{sources}\n\nExtracted context:\n{context_result.context}"
        )

    def _extract_final_answer(self, content: str) -> str | None:
        marker = "FINAL:"
        if marker not in content:
            return None
        return content.split(marker, 1)[1].strip()

    async def _decide(self, query: str) -> tuple[bool, str | None]:
        """Decide if the query requires searching.

        Returns:
            Tuple of (should_search, optimized_search_query or None).
        """
        # Try function calling if supported
        if self.llm.supports_tools():
            logger.debug("Attempting function calling for decision.")
            try:
                return await self._decide_with_tools(query)
            except Exception as e:
                logger.warning(f"Function calling failed: {e}. Falling back to prompt.")
                # Fall through to prompt-based classification

        logger.debug("Using prompt-based classifier for decision.")
        return await self._decide_with_prompt(query)

    async def _decide_with_tools(self, query: str) -> tuple[bool, str | None]:
        """Use native function calling to decide.

        The LLM is given a search tool. If it chooses to use it,
        we search. Otherwise, we respond directly.
        """
        system = (
            "You are an intelligent assistant with access to a knowledge base. "
            "If the user's question seems to require information from their "
            "personal documents, meetings, projects, or any specific data, "
            "you MUST use search_documents. Only respond directly for questions "
            "of obvious general knowledge like simple math or greetings."
        )

        response = await self.llm.generate_with_tools(
            system_prompt=system,
            user_prompt=query,
            tools=[self.SEARCH_TOOL],
        )

        # DEBUG: Log the raw response
        logger.debug(
            f"Function calling response - tool_calls: {response.tool_calls}, content: {response.content[:100] if response.content else None}..."
        )

        if response.tool_calls:
            # Model wants to search
            tool_call = response.tool_calls[0]
            search_query = tool_call.arguments.get("query", query)
            logger.debug(f"Tool call: search_documents('{search_query}')")
            return True, search_query
        else:
            # Model responded without tool - in conservative mode, fallback to prompt classifier
            logger.warning(
                f"Model did not use tools. Conservative={self.conservative}. Will use prompt fallback."
            )
            if self.conservative:
                # Don't trust function calling, use prompt classifier instead
                return await self._decide_with_prompt(query)
            return False, None

    async def _decide_with_prompt(self, query: str) -> tuple[bool, str | None]:
        """Fallback: use prompt engineering to classify.

        This works with any LLM that doesn't support function calling.
        """
        classifier = """Classify this question in ONE word:

SEARCH = Any question about: documents, meetings, projects, tasks, personal data, specific information, "what happened", "what does it say", references to events or people.

DIRECT = ONLY for: greetings, simple math, translations, dictionary definitions, obvious general knowledge.

IF IN DOUBT → SEARCH

Respond ONLY: SEARCH or DIRECT"""

        response = await self.llm.generate_response(classifier, query, stream=False)

        # Fix: ensure we don't try to strip an AsyncIterator (though stream=False returns str)
        if isinstance(response, str):
            response_upper = response.strip().upper()
        else:
            # This should not happen with stream=False, but for safety with types
            response_upper = "SEARCH"

        # Parse the response - conservative: default to SEARCH
        if "DIRECT" in response_upper and "SEARCH" not in response_upper:
            return False, None
        else:
            # Anything else (including SEARCH or ambiguous) -> search
            return True, None

    async def _reformulate_query(self, query: str) -> str:
        """Transform a conversational query into a search-optimized query.

        This is an agentic reasoning step that extracts key concepts and
        removes conversational noise to improve search recall.

        Args:
            query: The user's original or decision-provided query.

        Returns:
            An optimized query string for search.
        """
        system_prompt = (
            "You are an information retrieval expert. Your task is to convert a "
            "conversational question into an optimized search query (keywords and key concepts).\n"
            "Rules:\n"
            "- Remove greetings, politeness, and filler.\n"
            "- Extract main entities and concepts.\n"
            "- If the question is short and direct, keep it as is.\n"
            "- RESPOND ONLY WITH THE OPTIMIZED QUERY, WITHOUT EXPLANATIONS."
        )

        reformulated = await self.llm.generate_response(
            system_prompt, query, stream=False
        )

        if isinstance(reformulated, str):
            result = reformulated.strip().strip('"').strip("'")
        else:
            result = query

        logger.debug(f"Query reformulated: '{query}' -> '{result}'")
        return result
