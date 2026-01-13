from abc import ABC, abstractmethod
from typing import AsyncIterator


class ILLMProvider(ABC):
    """Interface for Large Language Model providers."""

    @abstractmethod
    async def generate_response(
        self, system_prompt: str, user_prompt: str, stream: bool = False
    ) -> AsyncIterator[str] | str:
        """Generate a response from the LLM."""
        pass
