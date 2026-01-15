"""
AgentService - Vanilla ReAct Agent

This agent decides whether to search the RAG or answer directly based on the query.
Uses function calling when supported, falls back to prompt engineering otherwise.
"""

import logging
from dataclasses import dataclass, field
from typing import AsyncIterator, List

from src.core.interfaces.llm import ILLMProvider
from src.core.schemas.search import SearchMatch
from src.services.rag_service import RAGService

logger = logging.getLogger(__name__)


@dataclass
class AgentResponse:
    """Response from the agent with context for explainability."""

    response: AsyncIterator[str] | str
    searched: bool = False
    search_query: str | None = None
    matches: List[SearchMatch] = field(default_factory=list)


class AgentService:
    """ReAct-style agent that decides when to use RAG.

    The agent uses a conservative approach: when in doubt, it searches.
    This prioritizes accuracy over speed.
    """

    # Tool definition for function calling
    SEARCH_TOOL = {
        "type": "function",
        "function": {
            "name": "search_documents",
            "description": (
                "Buscar información en la base de conocimientos del usuario. "
                "Usar cuando la pregunta requiere datos específicos de documentos, "
                "información personal, o contexto que no es conocimiento general."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Consulta optimizada para búsqueda semántica",
                    }
                },
                "required": ["query"],
            },
        },
    }

    # Classifier prompt for fallback strategy
    CLASSIFIER_PROMPT = """Analiza la pregunta del usuario y clasifica si necesitas buscar información.

Responde SOLO con una de estas palabras:
- SEARCH = La pregunta requiere información específica de documentos personales, datos particulares, o contexto que no es conocimiento general.
- DIRECT = Es conocimiento general, matemáticas, definiciones comunes, traducciones, o conversación casual.

Ejemplos:
- "¿Cuánto es 2+2?" → DIRECT
- "¿Qué dice el documento sobre el presupuesto?" → SEARCH
- "Traduce 'hello' al español" → DIRECT
- "¿Cuáles son mis tareas pendientes?" → SEARCH

Responde SOLO: SEARCH o DIRECT"""

    def __init__(
        self,
        rag_service: RAGService,
        llm: ILLMProvider,
        conservative: bool = True,
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

    async def chat(
        self,
        query: str,
        system_prompt: str,
        limit: int = 5,
    ) -> AgentResponse:
        """Main entry point for the agent.

        Decides whether to search the RAG or respond directly based on the query.

        Args:
            query: User's question.
            system_prompt: System instructions for the response.
            limit: Max number of documents to retrieve if searching.

        Returns:
            AgentResponse with response stream and context (searched, matches, etc.)
        """
        # 1. Decide if we need to search
        should_search, search_query = await self._decide(query)

        if should_search:
            # 2a. Use RAG to search and respond
            logger.info(f"Agent decided to SEARCH. Query: '{search_query or query}'")
            response, matches, reformulated = await self.rag.answer(
                search_query or query, system_prompt, limit=limit
            )

            return AgentResponse(
                response=response,
                searched=True,
                search_query=reformulated,
                matches=matches,
            )
        else:
            # 2b. Respond directly without RAG
            logger.info("Agent decided to respond DIRECTLY (no RAG).")
            response = await self.llm.generate_response(
                system_prompt, query, stream=True
            )
            return AgentResponse(response=response, searched=False)

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
            "Eres un asistente inteligente con acceso a una base de conocimientos. "
            "Si la pregunta del usuario parece requerir información de sus documentos "
            "personales, reuniones, proyectos, o cualquier dato específico, "
            "DEBES usar search_documents. Solo responde directamente para preguntas "
            "de conocimiento general obvio como matemáticas simples o saludos."
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
        classifier = """Clasifica esta pregunta en UNA palabra:

SEARCH = Cualquier pregunta sobre: documentos, reuniones, proyectos, tareas, datos personales, información específica, "qué pasó", "qué dice", referencias a eventos o personas.

DIRECT = SOLO para: saludos, matemáticas simples, traducciones, definiciones de diccionario, conocimiento general obvio.

EN CASO DE DUDA → SEARCH

Responde SOLO: SEARCH o DIRECT"""

        response = await self.llm.generate_response(classifier, query, stream=False)

        response_upper = response.strip().upper()

        # Parse the response - conservative: default to SEARCH
        if "DIRECT" in response_upper and "SEARCH" not in response_upper:
            return False, None
        else:
            # Anything else (including SEARCH or ambiguous) -> search
            return True, None
