from abc import ABC, abstractmethod
from typing import List


class IEmbedder(ABC):
    """Interface for embedding generation providers."""

    @abstractmethod
    async def get_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single string."""
        pass

    @abstractmethod
    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a batch of strings."""
        pass
