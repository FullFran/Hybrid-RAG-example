from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, AsyncIterator


@dataclass
class ToolCall:
    """Represents a tool call requested by the LLM."""

    name: str
    arguments: dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolResponse:
    """Response from an LLM that may include tool calls."""

    content: str | None = None
    tool_calls: list[ToolCall] = field(default_factory=list)


class ILLMProvider(ABC):
    """Interface for Large Language Model providers."""

    @abstractmethod
    async def generate_response(
        self, system_prompt: str, user_prompt: str, stream: bool = False
    ) -> AsyncIterator[str] | str:
        """Generate a response from the LLM."""
        pass

    def supports_tools(self) -> bool:
        """Check if the provider supports function calling / tools.

        Override in subclasses that support tools.
        """
        return False

    async def generate_with_tools(
        self,
        system_prompt: str,
        user_prompt: str,
        tools: list[dict],
    ) -> ToolResponse:
        """Generate a response with tool calling support.

        Args:
            system_prompt: System instructions for the LLM.
            user_prompt: User's query.
            tools: List of tool definitions in OpenAI format.

        Returns:
            ToolResponse with either content or tool_calls.

        Raises:
            NotImplementedError: If the provider doesn't support tools.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} does not support tool calling. "
            "Use generate_response() instead."
        )
