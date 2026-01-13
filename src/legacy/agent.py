"""Main MongoDB RAG agent implementation with shared state."""

from pydantic_ai import Agent, RunContext
from pydantic import BaseModel
from typing import Optional

from pydantic_ai.ag_ui import StateDeps

from src.providers import get_llm_model
from src.dependencies import AgentDependencies
from src.prompts import MAIN_SYSTEM_PROMPT
from src.tools import semantic_search, hybrid_search, text_search


class RAGState(BaseModel):
    """Minimal shared state for the RAG agent."""
    pass


# Create the RAG agent with AGUI support
rag_agent = Agent(
    get_llm_model(),
    deps_type=StateDeps[RAGState],
    system_prompt=MAIN_SYSTEM_PROMPT
)


@rag_agent.tool
async def search_knowledge_base(
    ctx: RunContext[StateDeps[RAGState]],
    query: str,
    match_count: Optional[int] = 5,
    search_type: Optional[str] = "hybrid"
) -> str:
    """
    Search the knowledge base for relevant information.

    Args:
        ctx: Agent runtime context with state dependencies
        query: Search query text
        match_count: Number of results to return (default: 5)
        search_type: Type of search - "semantic" or "text" or "hybrid" (default: hybrid)

    Returns:
        String containing the retrieved information formatted for the LLM
    """
    try:
        # Initialize database connection
        agent_deps = AgentDependencies()
        await agent_deps.initialize()

        # Create a context wrapper for the search tools
        class DepsWrapper:
            def __init__(self, deps):
                self.deps = deps

        deps_ctx = DepsWrapper(agent_deps)

        # Perform the search based on type
        if search_type == "hybrid":
            results = await hybrid_search(
                ctx=deps_ctx,
                query=query,
                match_count=match_count
            )
        elif search_type == "semantic":
            results = await semantic_search(
                ctx=deps_ctx,
                query=query,
                match_count=match_count
            )
        else:
            results = await text_search(
                ctx=deps_ctx,
                query=query,
                match_count=match_count
            )

        # Clean up
        await agent_deps.cleanup()

        # Format results as a simple string
        if not results:
            return "No relevant information found in the knowledge base."

        # Build a formatted response
        response_parts = [f"Found {len(results)} relevant documents:\n"]

        for i, result in enumerate(results, 1):
            response_parts.append(f"\n--- Document {i}: {result.document_title} (relevance: {result.similarity:.2f}) ---")
            response_parts.append(result.content)

        return "\n".join(response_parts)

    except Exception as e:
        return f"Error searching knowledge base: {str(e)}"
