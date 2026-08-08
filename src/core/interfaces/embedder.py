from abc import ABC, abstractmethod


class IEmbedder(ABC):
    """Interface for embedding generation providers."""

    @abstractmethod
    async def get_embedding(self, text: str) -> list[float]:
        """Generate embedding for a single string."""

    @abstractmethod
    async def get_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a batch of strings."""
